import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


class MainApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "kanban.db"
        os.environ["KANBAN_DB_PATH"] = str(db_path)

    def tearDown(self) -> None:
        os.environ.pop("KANBAN_DB_PATH", None)
        self.temp_dir.cleanup()

    def test_health_endpoint(self) -> None:
        with TestClient(create_app()) as client:
            response = client.get("/api/health")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["status"], "ok")

    def test_get_board_for_demo_user(self) -> None:
        with TestClient(create_app()) as client:
            response = client.get("/api/kanban/user")
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertIn("columns", payload)
            self.assertIn("cards", payload)

    def test_update_board_then_read_persists(self) -> None:
        with TestClient(create_app()) as client:
            update_payload = {
                "columns": [{"id": "col-backlog", "title": "Stored", "cardIds": ["card-1"]}],
                "cards": {
                    "card-1": {
                        "id": "card-1",
                        "title": "Persisted",
                        "details": "Persisted details",
                    }
                },
            }
            write_response = client.put("/api/kanban/user", json=update_payload)
            self.assertEqual(write_response.status_code, 200)

            read_response = client.get("/api/kanban/user")
            self.assertEqual(read_response.status_code, 200)
            self.assertEqual(
                read_response.json()["columns"][0]["title"],
                "Stored",
            )

    def test_missing_user_returns_not_found(self) -> None:
        with TestClient(create_app()) as client:
            response = client.get("/api/kanban/missing-user")
            self.assertEqual(response.status_code, 404)

    def test_invalid_payload_returns_validation_error(self) -> None:
        with TestClient(create_app()) as client:
            invalid_payload = {
                "columns": [{"id": "col-a", "title": "A", "cardIds": ["card-1"]}],
                "cards": {
                    "card-1": {
                        "id": "different-id",
                        "title": "Invalid",
                        "details": "Mismatch",
                    }
                },
            }
            response = client.put("/api/kanban/user", json=invalid_payload)
            self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
