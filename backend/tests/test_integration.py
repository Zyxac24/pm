"""Integration tests covering end-to-end workflows across multiple API endpoints."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import create_app
from app.models import AiAssistantResponseModel, AiBoardPatchModel, AiPatchOperationModel


class FullWorkflowIntegrationTests(unittest.TestCase):
    """Tests that simulate complete user journeys."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "kanban.db"
        os.environ["KANBAN_DB_PATH"] = str(db_path)

    def tearDown(self) -> None:
        os.environ.pop("KANBAN_DB_PATH", None)
        self.temp_dir.cleanup()

    def test_register_create_board_add_cards_workflow(self) -> None:
        """Full workflow: register -> create board -> add cards -> verify."""
        with TestClient(create_app()) as client:
            # 1. Register
            reg = client.post(
                "/api/auth/register",
                json={"username": "alice", "password": "alice123"},
            )
            self.assertEqual(reg.status_code, 200)
            token = reg.json()["token"]
            headers = {"Authorization": f"Bearer {token}"}

            # 2. Create a project board
            board_resp = client.post(
                "/api/boards",
                json={"name": "Project Alpha", "description": "Main project board"},
                headers=headers,
            )
            self.assertEqual(board_resp.status_code, 201)
            board_id = board_resp.json()["board_id"]

            # 3. Update board with cards
            board_data = {
                "columns": [
                    {"id": "col-todo", "title": "To Do", "cardIds": ["c1", "c2"]},
                    {"id": "col-doing", "title": "Doing", "cardIds": []},
                    {"id": "col-done", "title": "Done", "cardIds": []},
                ],
                "cards": {
                    "c1": {"id": "c1", "title": "Design mockups", "details": "Create wireframes"},
                    "c2": {"id": "c2", "title": "Set up CI", "details": "Configure pipelines"},
                },
            }
            update_resp = client.put(
                f"/api/boards/{board_id}", json=board_data, headers=headers
            )
            self.assertEqual(update_resp.status_code, 200)

            # 4. Verify board state
            get_resp = client.get(f"/api/boards/{board_id}", headers=headers)
            self.assertEqual(get_resp.status_code, 200)
            board = get_resp.json()["board"]
            self.assertEqual(len(board["cards"]), 2)
            self.assertEqual(board["columns"][0]["title"], "To Do")

            # 5. Verify in board list
            list_resp = client.get("/api/boards", headers=headers)
            boards = list_resp.json()["boards"]
            project_board = next(b for b in boards if b["name"] == "Project Alpha")
            self.assertEqual(project_board["card_count"], 2)

    def test_multi_user_isolation(self) -> None:
        """Two users' boards should be completely isolated."""
        with TestClient(create_app()) as client:
            # Register two users
            reg1 = client.post(
                "/api/auth/register",
                json={"username": "bob", "password": "bob12345"},
            )
            reg2 = client.post(
                "/api/auth/register",
                json={"username": "carol", "password": "carol123"},
            )
            token1 = reg1.json()["token"]
            token2 = reg2.json()["token"]
            h1 = {"Authorization": f"Bearer {token1}"}
            h2 = {"Authorization": f"Bearer {token2}"}

            # Each creates a board
            b1 = client.post("/api/boards", json={"name": "Bob's Board"}, headers=h1)
            b2 = client.post("/api/boards", json={"name": "Carol's Board"}, headers=h2)
            bid1 = b1.json()["board_id"]
            bid2 = b2.json()["board_id"]

            # Bob can see his boards but not Carol's
            bob_boards = client.get("/api/boards", headers=h1).json()["boards"]
            bob_names = {b["name"] for b in bob_boards}
            self.assertIn("Bob's Board", bob_names)
            self.assertNotIn("Carol's Board", bob_names)

            # Carol can't access Bob's board
            cross_access = client.get(f"/api/boards/{bid1}", headers=h2)
            self.assertEqual(cross_access.status_code, 403)

            # Carol can access her own
            self_access = client.get(f"/api/boards/{bid2}", headers=h2)
            self.assertEqual(self_access.status_code, 200)

    def test_board_crud_lifecycle(self) -> None:
        """Create -> Read -> Update -> Rename -> Delete lifecycle."""
        with TestClient(create_app()) as client:
            token = client.post(
                "/api/auth/login",
                json={"username": "user", "password": "password"},
            ).json()["token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Create
            created = client.post(
                "/api/boards",
                json={"name": "Lifecycle Board", "description": "Testing lifecycle"},
                headers=headers,
            )
            bid = created.json()["board_id"]

            # Read
            read = client.get(f"/api/boards/{bid}", headers=headers)
            self.assertEqual(read.json()["name"], "Lifecycle Board")

            # Update board data
            client.put(
                f"/api/boards/{bid}",
                json={
                    "columns": [{"id": "col-1", "title": "Only Column", "cardIds": []}],
                    "cards": {},
                },
                headers=headers,
            )

            # Rename
            renamed = client.patch(
                f"/api/boards/{bid}/meta",
                json={"name": "Renamed Board", "description": "Updated desc"},
                headers=headers,
            )
            self.assertEqual(renamed.json()["name"], "Renamed Board")

            # Delete
            deleted = client.delete(f"/api/boards/{bid}", headers=headers)
            self.assertEqual(deleted.status_code, 204)

            # Verify gone
            gone = client.get(f"/api/boards/{bid}", headers=headers)
            self.assertEqual(gone.status_code, 404)

    @patch(
        "app.main.run_structured_kanban_chat",
        return_value=AiAssistantResponseModel(
            message="I created a card for you.",
            patch=AiBoardPatchModel(
                operations=[
                    AiPatchOperationModel(
                        op="create_card",
                        cardId="card-ai-1",
                        columnId="col-todo",
                        title="AI Task",
                        details="Created by AI",
                        position=0,
                    ),
                ]
            ),
        ),
    )
    def test_ai_chat_with_authenticated_board(self, _: object) -> None:
        """AI chat endpoint works with the new auth + board ID system."""
        with TestClient(create_app()) as client:
            token = client.post(
                "/api/auth/register",
                json={"username": "aiuser", "password": "ai123456"},
            ).json()["token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Create board
            board_resp = client.post(
                "/api/boards", json={"name": "AI Board"}, headers=headers
            )
            board_id = board_resp.json()["board_id"]

            # Chat with AI
            chat_resp = client.post(
                f"/api/ai/chat/{board_id}",
                json={"question": "Create a task for me", "history": []},
                headers=headers,
            )

        self.assertEqual(chat_resp.status_code, 200)
        payload = chat_resp.json()
        self.assertTrue(payload["patchApplied"])
        self.assertIn("card-ai-1", payload["board"]["cards"])

    def test_legacy_endpoints_still_work(self) -> None:
        """Legacy /api/kanban/{username} endpoints remain functional."""
        with TestClient(create_app()) as client:
            # Get demo board
            response = client.get("/api/kanban/user")
            self.assertEqual(response.status_code, 200)
            self.assertIn("columns", response.json())
            self.assertEqual(len(response.json()["columns"]), 5)

    def test_register_login_roundtrip(self) -> None:
        """Register a user, then login with same credentials."""
        with TestClient(create_app()) as client:
            client.post(
                "/api/auth/register",
                json={"username": "roundtrip", "password": "round123"},
            )
            login = client.post(
                "/api/auth/login",
                json={"username": "roundtrip", "password": "round123"},
            )

        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.json()["username"], "roundtrip")

    def test_concurrent_board_updates(self) -> None:
        """Multiple updates to same board should all persist."""
        with TestClient(create_app()) as client:
            token = client.post(
                "/api/auth/login",
                json={"username": "user", "password": "password"},
            ).json()["token"]
            headers = {"Authorization": f"Bearer {token}"}

            board_resp = client.post(
                "/api/boards", json={"name": "Update Test"}, headers=headers
            )
            bid = board_resp.json()["board_id"]

            for i in range(5):
                board_data = {
                    "columns": [
                        {"id": "col-1", "title": f"Iteration {i}", "cardIds": []},
                    ],
                    "cards": {},
                }
                client.put(f"/api/boards/{bid}", json=board_data, headers=headers)

            final = client.get(f"/api/boards/{bid}", headers=headers)
            self.assertEqual(final.json()["board"]["columns"][0]["title"], "Iteration 4")


class DatabaseMigrationTests(unittest.TestCase):
    """Test that old databases get migrated properly."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "kanban.db"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_fresh_database_initializes_correctly(self) -> None:
        from app.db import KanbanRepository

        repo = KanbanRepository(db_path=self.db_path)
        repo.initialize()

        # Demo user should exist and have a board
        board = repo.get_board("user")
        self.assertIn("columns", board)

        # Demo user should be loginable
        user = repo.authenticate_user("user", "password")
        self.assertEqual(user["username"], "user")

    def test_double_initialize_is_idempotent(self) -> None:
        from app.db import KanbanRepository

        repo = KanbanRepository(db_path=self.db_path)
        repo.initialize()
        repo.initialize()

        board = repo.get_board("user")
        self.assertIn("columns", board)


if __name__ == "__main__":
    unittest.main()
