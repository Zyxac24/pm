import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


class MultiBoardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "kanban.db"
        os.environ["KANBAN_DB_PATH"] = str(db_path)

    def tearDown(self) -> None:
        os.environ.pop("KANBAN_DB_PATH", None)
        self.temp_dir.cleanup()

    def _login(self, client: TestClient, username: str = "user", password: str = "password") -> str:
        response = client.post("/api/auth/login", json={"username": username, "password": password})
        return response.json()["token"]

    def _register(self, client: TestClient, username: str, password: str = "test1234") -> str:
        response = client.post("/api/auth/register", json={"username": username, "password": password})
        return response.json()["token"]

    def _auth_headers(self, token: str) -> dict:
        return {"Authorization": f"Bearer {token}"}

    def test_list_boards_returns_demo_board(self) -> None:
        with TestClient(create_app()) as client:
            token = self._login(client)
            response = client.get("/api/boards", headers=self._auth_headers(token))

        self.assertEqual(response.status_code, 200)
        boards = response.json()["boards"]
        self.assertGreaterEqual(len(boards), 1)
        self.assertIn("board_id", boards[0])
        self.assertIn("name", boards[0])

    def test_create_board(self) -> None:
        with TestClient(create_app()) as client:
            token = self._login(client)
            response = client.post(
                "/api/boards",
                json={"name": "Sprint Board", "description": "For sprint planning"},
                headers=self._auth_headers(token),
            )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["name"], "Sprint Board")
        self.assertEqual(payload["description"], "For sprint planning")
        self.assertIn("board", payload)
        self.assertGreater(len(payload["board"]["columns"]), 0)

    def test_create_multiple_boards_per_user(self) -> None:
        with TestClient(create_app()) as client:
            token = self._login(client)
            headers = self._auth_headers(token)

            client.post("/api/boards", json={"name": "Board A"}, headers=headers)
            client.post("/api/boards", json={"name": "Board B"}, headers=headers)

            response = client.get("/api/boards", headers=headers)

        boards = response.json()["boards"]
        # Demo board + 2 new boards = 3
        self.assertEqual(len(boards), 3)
        board_names = {b["name"] for b in boards}
        self.assertIn("Board A", board_names)
        self.assertIn("Board B", board_names)

    def test_get_board_by_id(self) -> None:
        with TestClient(create_app()) as client:
            token = self._login(client)
            headers = self._auth_headers(token)

            create_response = client.post(
                "/api/boards", json={"name": "Fetch Me"}, headers=headers
            )
            board_id = create_response.json()["board_id"]

            response = client.get(f"/api/boards/{board_id}", headers=headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Fetch Me")
        self.assertIn("board", response.json())

    def test_update_board_data(self) -> None:
        with TestClient(create_app()) as client:
            token = self._login(client)
            headers = self._auth_headers(token)

            create_response = client.post(
                "/api/boards", json={"name": "Editable"}, headers=headers
            )
            board_id = create_response.json()["board_id"]

            updated_board = {
                "columns": [
                    {"id": "col-1", "title": "Custom Column", "cardIds": ["c1"]},
                ],
                "cards": {"c1": {"id": "c1", "title": "Task", "details": "Details"}},
            }
            response = client.put(
                f"/api/boards/{board_id}", json=updated_board, headers=headers
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["board"]["columns"][0]["title"], "Custom Column")

    def test_update_board_meta(self) -> None:
        with TestClient(create_app()) as client:
            token = self._login(client)
            headers = self._auth_headers(token)

            create_response = client.post(
                "/api/boards", json={"name": "Old Name"}, headers=headers
            )
            board_id = create_response.json()["board_id"]

            response = client.patch(
                f"/api/boards/{board_id}/meta",
                json={"name": "New Name", "description": "Updated description"},
                headers=headers,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "New Name")
        self.assertEqual(response.json()["description"], "Updated description")

    def test_delete_board(self) -> None:
        with TestClient(create_app()) as client:
            token = self._login(client)
            headers = self._auth_headers(token)

            create_response = client.post(
                "/api/boards", json={"name": "Delete Me"}, headers=headers
            )
            board_id = create_response.json()["board_id"]

            delete_response = client.delete(f"/api/boards/{board_id}", headers=headers)
            self.assertEqual(delete_response.status_code, 204)

            get_response = client.get(f"/api/boards/{board_id}", headers=headers)
            self.assertEqual(get_response.status_code, 404)

    def test_board_access_denied_for_other_user(self) -> None:
        with TestClient(create_app()) as client:
            token1 = self._login(client)
            token2 = self._register(client, "otheruser")

            create_response = client.post(
                "/api/boards",
                json={"name": "Private Board"},
                headers=self._auth_headers(token1),
            )
            board_id = create_response.json()["board_id"]

            get_response = client.get(
                f"/api/boards/{board_id}",
                headers=self._auth_headers(token2),
            )
            self.assertEqual(get_response.status_code, 403)

    def test_board_not_found_returns_404(self) -> None:
        with TestClient(create_app()) as client:
            token = self._login(client)
            response = client.get(
                "/api/boards/99999",
                headers=self._auth_headers(token),
            )
        self.assertEqual(response.status_code, 404)

    def test_board_data_persists_across_reads(self) -> None:
        with TestClient(create_app()) as client:
            token = self._login(client)
            headers = self._auth_headers(token)

            create_response = client.post(
                "/api/boards", json={"name": "Persist Test"}, headers=headers
            )
            board_id = create_response.json()["board_id"]

            board_update = {
                "columns": [
                    {"id": "col-a", "title": "Alpha", "cardIds": ["card-x"]},
                    {"id": "col-b", "title": "Beta", "cardIds": []},
                ],
                "cards": {"card-x": {"id": "card-x", "title": "Persisted", "details": "Yes"}},
            }
            client.put(f"/api/boards/{board_id}", json=board_update, headers=headers)

            read_response = client.get(f"/api/boards/{board_id}", headers=headers)

        self.assertEqual(read_response.status_code, 200)
        board = read_response.json()["board"]
        self.assertEqual(len(board["columns"]), 2)
        self.assertEqual(board["cards"]["card-x"]["title"], "Persisted")

    def test_cannot_delete_other_users_board(self) -> None:
        with TestClient(create_app()) as client:
            token1 = self._login(client)
            token2 = self._register(client, "attacker")

            create_response = client.post(
                "/api/boards",
                json={"name": "Protected"},
                headers=self._auth_headers(token1),
            )
            board_id = create_response.json()["board_id"]

            delete_response = client.delete(
                f"/api/boards/{board_id}",
                headers=self._auth_headers(token2),
            )
            self.assertEqual(delete_response.status_code, 403)

    def test_cannot_update_other_users_board(self) -> None:
        with TestClient(create_app()) as client:
            token1 = self._login(client)
            token2 = self._register(client, "intruder")

            create_response = client.post(
                "/api/boards",
                json={"name": "Guarded"},
                headers=self._auth_headers(token1),
            )
            board_id = create_response.json()["board_id"]

            response = client.put(
                f"/api/boards/{board_id}",
                json={
                    "columns": [{"id": "col-1", "title": "Hacked", "cardIds": []}],
                    "cards": {},
                },
                headers=self._auth_headers(token2),
            )
            self.assertEqual(response.status_code, 403)

    def test_list_boards_requires_auth(self) -> None:
        with TestClient(create_app()) as client:
            response = client.get("/api/boards")
        self.assertEqual(response.status_code, 401)

    def test_create_board_requires_auth(self) -> None:
        with TestClient(create_app()) as client:
            response = client.post("/api/boards", json={"name": "Unauthorized"})
        self.assertEqual(response.status_code, 401)

    def test_flexible_board_allows_custom_columns(self) -> None:
        with TestClient(create_app()) as client:
            token = self._login(client)
            headers = self._auth_headers(token)

            create_response = client.post(
                "/api/boards", json={"name": "Custom Columns"}, headers=headers
            )
            board_id = create_response.json()["board_id"]

            custom_board = {
                "columns": [
                    {"id": "col-ideas", "title": "Ideas", "cardIds": []},
                    {"id": "col-research", "title": "Research", "cardIds": []},
                    {"id": "col-dev", "title": "Development", "cardIds": []},
                    {"id": "col-testing", "title": "Testing", "cardIds": []},
                    {"id": "col-staging", "title": "Staging", "cardIds": []},
                    {"id": "col-prod", "title": "Production", "cardIds": []},
                ],
                "cards": {},
            }
            response = client.put(
                f"/api/boards/{board_id}", json=custom_board, headers=headers
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["board"]["columns"]), 6)


class FlexibleBoardModelTests(unittest.TestCase):
    def test_rejects_board_with_no_columns(self) -> None:
        from pydantic import ValidationError
        from app.models import FlexibleBoardModel

        with self.assertRaises(ValidationError):
            FlexibleBoardModel.model_validate({"columns": [], "cards": {}})

    def test_rejects_board_with_too_many_columns(self) -> None:
        from pydantic import ValidationError
        from app.models import FlexibleBoardModel

        columns = [{"id": f"col-{i}", "title": f"Col {i}", "cardIds": []} for i in range(21)]
        with self.assertRaises(ValidationError):
            FlexibleBoardModel.model_validate({"columns": columns, "cards": {}})

    def test_rejects_duplicate_column_ids(self) -> None:
        from pydantic import ValidationError
        from app.models import FlexibleBoardModel

        with self.assertRaises(ValidationError):
            FlexibleBoardModel.model_validate({
                "columns": [
                    {"id": "col-1", "title": "A", "cardIds": []},
                    {"id": "col-1", "title": "B", "cardIds": []},
                ],
                "cards": {},
            })

    def test_accepts_valid_flexible_board(self) -> None:
        from app.models import FlexibleBoardModel

        board = FlexibleBoardModel.model_validate({
            "columns": [
                {"id": "col-a", "title": "Alpha", "cardIds": ["c1"]},
                {"id": "col-b", "title": "Beta", "cardIds": []},
            ],
            "cards": {"c1": {"id": "c1", "title": "Card", "details": "Info"}},
        })
        self.assertEqual(len(board.columns), 2)


if __name__ == "__main__":
    unittest.main()
