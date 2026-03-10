import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


class UserRegistrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "kanban.db"
        os.environ["KANBAN_DB_PATH"] = str(db_path)

    def tearDown(self) -> None:
        os.environ.pop("KANBAN_DB_PATH", None)
        self.temp_dir.cleanup()

    def test_register_new_user_returns_token(self) -> None:
        with TestClient(create_app()) as client:
            response = client.post(
                "/api/auth/register",
                json={"username": "newuser", "password": "test1234"},
            )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("token", payload)
        self.assertEqual(payload["username"], "newuser")
        self.assertIsInstance(payload["user_id"], int)

    def test_register_duplicate_username_returns_conflict(self) -> None:
        with TestClient(create_app()) as client:
            client.post(
                "/api/auth/register",
                json={"username": "duplicate", "password": "test1234"},
            )
            response = client.post(
                "/api/auth/register",
                json={"username": "duplicate", "password": "other456"},
            )
        self.assertEqual(response.status_code, 409)
        self.assertIn("already taken", response.json()["detail"])

    def test_register_creates_default_board(self) -> None:
        with TestClient(create_app()) as client:
            reg_response = client.post(
                "/api/auth/register",
                json={"username": "boarduser", "password": "test1234"},
            )
            token = reg_response.json()["token"]

            boards_response = client.get(
                "/api/boards",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(boards_response.status_code, 200)
        boards = boards_response.json()["boards"]
        self.assertEqual(len(boards), 1)
        self.assertEqual(boards[0]["name"], "My First Board")

    def test_register_rejects_too_short_password(self) -> None:
        with TestClient(create_app()) as client:
            response = client.post(
                "/api/auth/register",
                json={"username": "shortpw", "password": "ab"},
            )
        self.assertEqual(response.status_code, 422)

    def test_register_rejects_invalid_username_characters(self) -> None:
        with TestClient(create_app()) as client:
            response = client.post(
                "/api/auth/register",
                json={"username": "Bad User!", "password": "test1234"},
            )
        self.assertEqual(response.status_code, 422)


class UserLoginTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "kanban.db"
        os.environ["KANBAN_DB_PATH"] = str(db_path)

    def tearDown(self) -> None:
        os.environ.pop("KANBAN_DB_PATH", None)
        self.temp_dir.cleanup()

    def test_login_demo_user_returns_token(self) -> None:
        with TestClient(create_app()) as client:
            response = client.post(
                "/api/auth/login",
                json={"username": "user", "password": "password"},
            )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("token", payload)
        self.assertEqual(payload["username"], "user")

    def test_login_wrong_password_returns_unauthorized(self) -> None:
        with TestClient(create_app()) as client:
            response = client.post(
                "/api/auth/login",
                json={"username": "user", "password": "wrongpassword"},
            )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid", response.json()["detail"])

    def test_login_nonexistent_user_returns_unauthorized(self) -> None:
        with TestClient(create_app()) as client:
            response = client.post(
                "/api/auth/login",
                json={"username": "nonexistent", "password": "test1234"},
            )
        self.assertEqual(response.status_code, 401)

    def test_login_then_access_profile(self) -> None:
        with TestClient(create_app()) as client:
            login_response = client.post(
                "/api/auth/login",
                json={"username": "user", "password": "password"},
            )
            token = login_response.json()["token"]

            profile_response = client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(profile_response.status_code, 200)
        self.assertEqual(profile_response.json()["username"], "user")

    def test_profile_without_token_returns_unauthorized(self) -> None:
        with TestClient(create_app()) as client:
            response = client.get("/api/auth/me")
        self.assertEqual(response.status_code, 401)

    def test_profile_with_invalid_token_returns_unauthorized(self) -> None:
        with TestClient(create_app()) as client:
            response = client.get(
                "/api/auth/me",
                headers={"Authorization": "Bearer invalid-token"},
            )
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
