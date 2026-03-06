import tempfile
import unittest
from pathlib import Path

from app.db import KanbanRepository, UserNotFoundError


class KanbanRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "kanban.db"
        self.repository = KanbanRepository(db_path=self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_initialize_creates_database_and_demo_board(self) -> None:
        self.assertFalse(self.db_path.exists())

        self.repository.initialize()

        self.assertTrue(self.db_path.exists())
        board = self.repository.get_board("user")
        self.assertIn("columns", board)
        self.assertIn("cards", board)
        self.assertGreater(len(board["columns"]), 0)

    def test_get_board_raises_for_missing_user(self) -> None:
        self.repository.initialize()

        with self.assertRaises(UserNotFoundError):
            self.repository.get_board("missing-user")

    def test_update_board_persists_changes(self) -> None:
        self.repository.initialize()
        board = self.repository.get_board("user")

        board["columns"][0]["title"] = "Updated Backlog"
        self.repository.update_board("user", board)
        updated = self.repository.get_board("user")

        self.assertEqual(updated["columns"][0]["title"], "Updated Backlog")

    def test_update_board_raises_for_missing_user(self) -> None:
        self.repository.initialize()
        board = self.repository.get_board("user")

        with self.assertRaises(UserNotFoundError):
            self.repository.update_board("missing-user", board)


if __name__ == "__main__":
    unittest.main()
