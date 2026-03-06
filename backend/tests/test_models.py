import unittest

from pydantic import ValidationError

from app.db import DEFAULT_BOARD
from app.models import BoardModel


class BoardModelValidationTests(unittest.TestCase):
    def test_accepts_valid_board(self) -> None:
        board = BoardModel.model_validate(DEFAULT_BOARD)
        self.assertEqual(len(board.columns), 5)

    def test_rejects_unknown_card_reference(self) -> None:
        invalid_board = {
            **DEFAULT_BOARD,
            "columns": [
                {
                    "id": "col-backlog",
                    "title": "Backlog",
                    "cardIds": ["card-404"],
                }
            ],
        }

        with self.assertRaises(ValidationError):
            BoardModel.model_validate(invalid_board)

    def test_rejects_card_id_mismatch(self) -> None:
        invalid_board = {
            **DEFAULT_BOARD,
            "cards": {
                **DEFAULT_BOARD["cards"],
                "card-1": {
                    "id": "different-id",
                    "title": "Align roadmap themes",
                    "details": "Draft quarterly themes with impact statements and metrics.",
                },
            },
        }

        with self.assertRaises(ValidationError):
            BoardModel.model_validate(invalid_board)

    def test_rejects_missing_fixed_columns(self) -> None:
        invalid_board = {
            **DEFAULT_BOARD,
            "columns": [
                {
                    "id": "col-backlog",
                    "title": "Backlog",
                    "cardIds": list(DEFAULT_BOARD["cards"].keys()),
                }
            ],
        }

        with self.assertRaises(ValidationError):
            BoardModel.model_validate(invalid_board)


if __name__ == "__main__":
    unittest.main()
