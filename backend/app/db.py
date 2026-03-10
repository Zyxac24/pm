import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.auth import hash_password, verify_password
from app.models import BoardModel


class UserNotFoundError(Exception):
    pass


class UserAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class BoardNotFoundError(Exception):
    pass


class BoardAccessDeniedError(Exception):
    pass


DEFAULT_BOARD: dict[str, Any] = {
    "columns": [
        {"id": "col-backlog", "title": "Backlog", "cardIds": ["card-1", "card-2"]},
        {"id": "col-discovery", "title": "Discovery", "cardIds": ["card-3"]},
        {"id": "col-progress", "title": "In Progress", "cardIds": ["card-4", "card-5"]},
        {"id": "col-review", "title": "Review", "cardIds": ["card-6"]},
        {"id": "col-done", "title": "Done", "cardIds": ["card-7", "card-8"]},
    ],
    "cards": {
        "card-1": {
            "id": "card-1",
            "title": "Align roadmap themes",
            "details": "Draft quarterly themes with impact statements and metrics.",
        },
        "card-2": {
            "id": "card-2",
            "title": "Gather customer signals",
            "details": "Review support tags, sales notes, and churn feedback.",
        },
        "card-3": {
            "id": "card-3",
            "title": "Prototype analytics view",
            "details": "Sketch initial dashboard layout and key drill-downs.",
        },
        "card-4": {
            "id": "card-4",
            "title": "Refine status language",
            "details": "Standardize column labels and tone across the board.",
        },
        "card-5": {
            "id": "card-5",
            "title": "Design card layout",
            "details": "Add hierarchy and spacing for scanning dense lists.",
        },
        "card-6": {
            "id": "card-6",
            "title": "QA micro-interactions",
            "details": "Verify hover, focus, and loading states.",
        },
        "card-7": {
            "id": "card-7",
            "title": "Ship marketing page",
            "details": "Final copy approved and asset pack delivered.",
        },
        "card-8": {
            "id": "card-8",
            "title": "Close onboarding sprint",
            "details": "Document release notes and share internally.",
        },
    },
}

NEW_BOARD_TEMPLATE: dict[str, Any] = {
    "columns": [
        {"id": "col-todo", "title": "To Do", "cardIds": []},
        {"id": "col-in-progress", "title": "In Progress", "cardIds": []},
        {"id": "col-done", "title": "Done", "cardIds": []},
    ],
    "cards": {},
}


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS kanban_boards (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  name TEXT NOT NULL DEFAULT 'My Board',
  description TEXT NOT NULL DEFAULT '',
  board_json TEXT NOT NULL CHECK (json_valid(board_json)),
  updated_at TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_boards_user_id ON kanban_boards(user_id);
"""

MIGRATION_SQL = """
-- Add password_hash column if missing (migration from old schema)
ALTER TABLE users ADD COLUMN password_hash TEXT NOT NULL DEFAULT '';

-- Add name column if missing
ALTER TABLE kanban_boards ADD COLUMN name TEXT NOT NULL DEFAULT 'My Board';

-- Add description column if missing
ALTER TABLE kanban_boards ADD COLUMN description TEXT NOT NULL DEFAULT '';

-- Drop unique constraint on user_id (allow multiple boards per user)
-- SQLite doesn't support DROP CONSTRAINT, so we handle this via schema recreation
"""


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class KanbanRepository:
    db_path: Path

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as connection:
            # Check if we need migration from old schema
            needs_migration = self._check_needs_migration(connection)

            if needs_migration:
                self._migrate_schema(connection)
            else:
                connection.executescript(SCHEMA_SQL)

            # Create demo user if not exists
            demo_hash = hash_password("password")
            existing = connection.execute(
                "SELECT id, password_hash FROM users WHERE username = ?",
                ("user",),
            ).fetchone()

            if existing is None:
                connection.execute(
                    "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                    ("user", demo_hash, _now_iso()),
                )

            user_row = connection.execute(
                "SELECT id FROM users WHERE username = ?",
                ("user",),
            ).fetchone()
            if user_row is None:
                raise RuntimeError("Failed to initialize demo user.")

            # Create default board for demo user if they have none
            board_count = connection.execute(
                "SELECT COUNT(*) as cnt FROM kanban_boards WHERE user_id = ?",
                (user_row["id"],),
            ).fetchone()["cnt"]

            if board_count == 0:
                connection.execute(
                    """
                    INSERT INTO kanban_boards (user_id, name, description, board_json, updated_at, version)
                    VALUES (?, ?, ?, ?, ?, 1)
                    """,
                    (user_row["id"], "Demo Board", "Default demo board with sample cards",
                     json.dumps(DEFAULT_BOARD), _now_iso()),
                )
            else:
                self._repair_demo_board_if_invalid(connection, user_row["id"])

            connection.commit()

    def _check_needs_migration(self, connection: sqlite3.Connection) -> bool:
        tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        ).fetchone()
        if tables is None:
            return False  # Fresh database, no migration needed

        columns = connection.execute("PRAGMA table_info(users)").fetchall()
        column_names = [col["name"] for col in columns]
        return "password_hash" not in column_names

    def _migrate_schema(self, connection: sqlite3.Connection) -> None:
        """Migrate from old schema (no auth, single board per user) to new."""
        # Read existing data
        old_users = connection.execute("SELECT * FROM users").fetchall()
        old_boards = connection.execute("SELECT * FROM kanban_boards").fetchall()

        # Drop old tables
        connection.execute("DROP TABLE IF EXISTS kanban_boards")
        connection.execute("DROP TABLE IF EXISTS users")

        # Create new schema
        connection.executescript(SCHEMA_SQL)

        # Re-insert users with default password hash
        demo_hash = hash_password("password")
        for user in old_users:
            connection.execute(
                "INSERT INTO users (id, username, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (user["id"], user["username"], demo_hash, user["created_at"]),
            )

        # Re-insert boards with name
        for board in old_boards:
            connection.execute(
                """
                INSERT INTO kanban_boards (id, user_id, name, description, board_json, updated_at, version)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (board["id"], board["user_id"], "My Board", "",
                 board["board_json"], board["updated_at"], board["version"]),
            )

    # --- User management ---

    def create_user(self, username: str, password: str) -> dict[str, Any]:
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT id FROM users WHERE username = ?", (username,)
            ).fetchone()
            if existing is not None:
                raise UserAlreadyExistsError(f"Username '{username}' is already taken.")

            password_hash = hash_password(password)
            created_at = _now_iso()
            cursor = connection.execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, password_hash, created_at),
            )
            user_id = cursor.lastrowid

            # Create a default board for the new user
            connection.execute(
                """
                INSERT INTO kanban_boards (user_id, name, description, board_json, updated_at, version)
                VALUES (?, ?, ?, ?, ?, 1)
                """,
                (user_id, "My First Board", "Your first Kanban board",
                 json.dumps(NEW_BOARD_TEMPLATE), _now_iso()),
            )
            connection.commit()

        return {"user_id": user_id, "username": username, "created_at": created_at}

    def authenticate_user(self, username: str, password: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, username, password_hash, created_at FROM users WHERE username = ?",
                (username,),
            ).fetchone()
            if row is None:
                raise InvalidCredentialsError("Invalid username or password.")
            if not verify_password(password, row["password_hash"]):
                raise InvalidCredentialsError("Invalid username or password.")

            return {
                "user_id": row["id"],
                "username": row["username"],
                "created_at": row["created_at"],
            }

    def get_user_by_id(self, user_id: int) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, username, created_at FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
            if row is None:
                raise UserNotFoundError(f"User with id {user_id} does not exist.")
            return {
                "user_id": row["id"],
                "username": row["username"],
                "created_at": row["created_at"],
            }

    # --- Multi-board management ---

    def list_boards(self, user_id: int) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, name, description, board_json, updated_at
                FROM kanban_boards
                WHERE user_id = ?
                ORDER BY updated_at DESC
                """,
                (user_id,),
            ).fetchall()

            boards = []
            for row in rows:
                board_data = json.loads(row["board_json"])
                boards.append({
                    "board_id": row["id"],
                    "name": row["name"],
                    "description": row["description"],
                    "updated_at": row["updated_at"],
                    "column_count": len(board_data.get("columns", [])),
                    "card_count": len(board_data.get("cards", {})),
                })
            return boards

    def create_board(self, user_id: int, name: str, description: str = "") -> dict[str, Any]:
        with self._connect() as connection:
            updated_at = _now_iso()
            cursor = connection.execute(
                """
                INSERT INTO kanban_boards (user_id, name, description, board_json, updated_at, version)
                VALUES (?, ?, ?, ?, ?, 1)
                """,
                (user_id, name, description, json.dumps(NEW_BOARD_TEMPLATE), updated_at),
            )
            board_id = cursor.lastrowid
            connection.commit()

        return {
            "board_id": board_id,
            "name": name,
            "description": description,
            "board": NEW_BOARD_TEMPLATE,
        }

    def get_board_by_id(self, board_id: int, user_id: int) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, user_id, name, description, board_json, updated_at
                FROM kanban_boards
                WHERE id = ?
                """,
                (board_id,),
            ).fetchone()
            if row is None:
                raise BoardNotFoundError(f"Board {board_id} does not exist.")
            if row["user_id"] != user_id:
                raise BoardAccessDeniedError("You do not have access to this board.")

            return {
                "board_id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "board": json.loads(row["board_json"]),
            }

    def update_board_data(self, board_id: int, user_id: int, board: dict[str, Any]) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, user_id, name, description FROM kanban_boards WHERE id = ?",
                (board_id,),
            ).fetchone()
            if row is None:
                raise BoardNotFoundError(f"Board {board_id} does not exist.")
            if row["user_id"] != user_id:
                raise BoardAccessDeniedError("You do not have access to this board.")

            updated_at = _now_iso()
            connection.execute(
                """
                UPDATE kanban_boards
                SET board_json = ?, updated_at = ?, version = version + 1
                WHERE id = ?
                """,
                (json.dumps(board), updated_at, board_id),
            )
            connection.commit()

        return {
            "board_id": board_id,
            "name": row["name"],
            "description": row["description"],
            "board": board,
        }

    def update_board_meta(self, board_id: int, user_id: int, name: str, description: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, user_id, board_json FROM kanban_boards WHERE id = ?",
                (board_id,),
            ).fetchone()
            if row is None:
                raise BoardNotFoundError(f"Board {board_id} does not exist.")
            if row["user_id"] != user_id:
                raise BoardAccessDeniedError("You do not have access to this board.")

            updated_at = _now_iso()
            connection.execute(
                """
                UPDATE kanban_boards
                SET name = ?, description = ?, updated_at = ?
                WHERE id = ?
                """,
                (name, description, updated_at, board_id),
            )
            connection.commit()

        board_data = json.loads(row["board_json"])
        return {
            "board_id": board_id,
            "name": name,
            "description": description,
            "updated_at": updated_at,
            "column_count": len(board_data.get("columns", [])),
            "card_count": len(board_data.get("cards", {})),
        }

    def delete_board(self, board_id: int, user_id: int) -> None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, user_id FROM kanban_boards WHERE id = ?",
                (board_id,),
            ).fetchone()
            if row is None:
                raise BoardNotFoundError(f"Board {board_id} does not exist.")
            if row["user_id"] != user_id:
                raise BoardAccessDeniedError("You do not have access to this board.")

            connection.execute("DELETE FROM kanban_boards WHERE id = ?", (board_id,))
            connection.commit()

    # --- Legacy single-board API (kept for backward compatibility) ---

    def get_board(self, username: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT kb.board_json
                FROM kanban_boards kb
                INNER JOIN users u ON u.id = kb.user_id
                WHERE u.username = ?
                ORDER BY kb.updated_at DESC
                LIMIT 1
                """,
                (username,),
            ).fetchone()
            if row is None:
                raise UserNotFoundError(f"User '{username}' does not exist.")

            return json.loads(row["board_json"])

    def update_board(self, username: str, board: dict[str, Any]) -> dict[str, Any]:
        with self._connect() as connection:
            user_row = connection.execute(
                "SELECT id FROM users WHERE username = ?",
                (username,),
            ).fetchone()
            if user_row is None:
                raise UserNotFoundError(f"User '{username}' does not exist.")

            # Get first board for user
            board_row = connection.execute(
                "SELECT id FROM kanban_boards WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1",
                (user_row["id"],),
            ).fetchone()

            updated_at = _now_iso()
            serialized_board = json.dumps(board)

            if board_row:
                connection.execute(
                    """
                    UPDATE kanban_boards
                    SET board_json = ?, updated_at = ?, version = version + 1
                    WHERE id = ?
                    """,
                    (serialized_board, updated_at, board_row["id"]),
                )
            else:
                connection.execute(
                    """
                    INSERT INTO kanban_boards (user_id, name, description, board_json, updated_at, version)
                    VALUES (?, ?, ?, ?, ?, 1)
                    """,
                    (user_row["id"], "My Board", "", serialized_board, updated_at),
                )

            connection.commit()
        return board

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=2.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode = WAL;")
        connection.execute("PRAGMA foreign_keys = ON;")
        return connection

    def _repair_demo_board_if_invalid(
        self,
        connection: sqlite3.Connection,
        user_id: int,
    ) -> None:
        row = connection.execute(
            """
            SELECT id, board_json
            FROM kanban_boards
            WHERE user_id = ?
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
        if row is None:
            return

        should_repair = False
        try:
            parsed_board = json.loads(row["board_json"])
            BoardModel.model_validate(parsed_board)
        except (json.JSONDecodeError, ValidationError):
            should_repair = True

        if should_repair:
            connection.execute(
                """
                UPDATE kanban_boards
                SET board_json = ?, updated_at = ?, version = version + 1
                WHERE id = ?
                """,
                (json.dumps(DEFAULT_BOARD), _now_iso(), row["id"]),
            )
