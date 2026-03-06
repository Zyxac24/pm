import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.models import BoardModel


class UserNotFoundError(Exception):
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


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS kanban_boards (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL UNIQUE,
  board_json TEXT NOT NULL CHECK (json_valid(board_json)),
  updated_at TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_boards_user_id ON kanban_boards(user_id);
"""


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class KanbanRepository:
    db_path: Path

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as connection:
            connection.executescript(SCHEMA_SQL)

            created_at = _now_iso()
            connection.execute(
                "INSERT OR IGNORE INTO users (username, created_at) VALUES (?, ?)",
                ("user", created_at),
            )

            user_row = connection.execute(
                "SELECT id FROM users WHERE username = ?",
                ("user",),
            ).fetchone()
            if user_row is None:
                raise RuntimeError("Failed to initialize demo user.")

            updated_at = _now_iso()
            connection.execute(
                """
                INSERT OR IGNORE INTO kanban_boards (user_id, board_json, updated_at, version)
                VALUES (?, ?, ?, 1)
                """,
                (user_row["id"], json.dumps(DEFAULT_BOARD), updated_at),
            )
            self._repair_demo_board_if_invalid(connection, user_row["id"])
            connection.commit()

    def get_board(self, username: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT kb.board_json
                FROM kanban_boards kb
                INNER JOIN users u ON u.id = kb.user_id
                WHERE u.username = ?
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

            updated_at = _now_iso()
            serialized_board = json.dumps(board)
            update_result = connection.execute(
                """
                UPDATE kanban_boards
                SET board_json = ?, updated_at = ?, version = version + 1
                WHERE user_id = ?
                """,
                (serialized_board, updated_at, user_row["id"]),
            )

            if update_result.rowcount == 0:
                connection.execute(
                    """
                    INSERT INTO kanban_boards (user_id, board_json, updated_at, version)
                    VALUES (?, ?, ?, 1)
                    """,
                    (user_row["id"], serialized_board, updated_at),
                )

            connection.commit()
        return board

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON;")
        return connection

    def _repair_demo_board_if_invalid(
        self,
        connection: sqlite3.Connection,
        user_id: int,
    ) -> None:
        row = connection.execute(
            """
            SELECT board_json
            FROM kanban_boards
            WHERE user_id = ?
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
                WHERE user_id = ?
                """,
                (json.dumps(DEFAULT_BOARD), _now_iso(), user_id),
            )
