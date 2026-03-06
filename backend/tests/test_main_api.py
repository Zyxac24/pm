import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.ai_client import OPENROUTER_MODEL, OpenRouterRequestError, OpenRouterSchemaError
from app.main import create_app
from app.models import AiAssistantResponseModel, AiBoardPatchModel, AiPatchOperationModel


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

    def test_ai_endpoint_returns_config_error_without_api_key(self) -> None:
        previous_api_key = os.environ.pop("OPENROUTER_API_KEY", None)
        try:
            with TestClient(create_app()) as client:
                response = client.post("/api/ai/test")
                self.assertEqual(response.status_code, 500)
                self.assertIn("OPENROUTER_API_KEY", response.json()["detail"])
        finally:
            if previous_api_key is not None:
                os.environ["OPENROUTER_API_KEY"] = previous_api_key

    @patch("app.main.run_connectivity_test", return_value="2 + 2 = 4")
    def test_ai_endpoint_returns_expected_payload_shape(self, _: object) -> None:
        with TestClient(create_app()) as client:
            response = client.post("/api/ai/test")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["provider"], "openrouter")
        self.assertEqual(payload["model"], OPENROUTER_MODEL)
        self.assertEqual(payload["prompt"], "2+2")
        self.assertTrue(payload["answer"])

    @patch(
        "app.main.run_connectivity_test",
        side_effect=OpenRouterRequestError("Upstream provider unavailable."),
    )
    def test_ai_endpoint_maps_provider_errors_to_bad_gateway(self, _: object) -> None:
        with TestClient(create_app()) as client:
            response = client.post("/api/ai/test")

        self.assertEqual(response.status_code, 502)
        self.assertIn("Upstream provider unavailable", response.json()["detail"])

    @unittest.skipUnless(
        os.getenv("OPENROUTER_API_KEY"),
        "OPENROUTER_API_KEY is required for real integration test.",
    )
    def test_ai_endpoint_real_openrouter_connection(self) -> None:
        with TestClient(create_app()) as client:
            response = client.post("/api/ai/test")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        normalized_answer = payload["answer"].lower()
        self.assertTrue(
            any(token in normalized_answer for token in ("4", "four", "cztery")),
            "Expected response to indicate the result of 2+2.",
        )

    @patch(
        "app.main.run_structured_kanban_chat",
        return_value=AiAssistantResponseModel(message="No board change needed.", patch=None),
    )
    def test_ai_chat_returns_message_without_patch(self, _: object) -> None:
        with TestClient(create_app()) as client:
            response = client.post(
                "/api/ai/chat/user",
                json={
                    "question": "What should I do next?",
                    "history": [{"role": "user", "content": "Help with planning."}],
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["message"], "No board change needed.")
        self.assertFalse(payload["patchApplied"])
        self.assertEqual(len(payload["board"]["columns"]), 5)

    @patch(
        "app.main.run_structured_kanban_chat",
        return_value=AiAssistantResponseModel(
            message="Done. I created, edited and moved cards.",
            patch=AiBoardPatchModel(
                operations=[
                    AiPatchOperationModel(
                        op="create_card",
                        cardId="card-ai-1",
                        columnId="col-backlog",
                        title="AI created card",
                        details="Created by AI",
                        position=0,
                    ),
                    AiPatchOperationModel(
                        op="edit_card",
                        cardId="card-1",
                        title="Card 1 edited by AI",
                        details="Updated details from AI",
                    ),
                    AiPatchOperationModel(
                        op="move_card",
                        cardId="card-1",
                        targetColumnId="col-done",
                        position=0,
                    ),
                ]
            ),
        ),
    )
    def test_ai_chat_applies_create_edit_move_patch(self, _: object) -> None:
        with TestClient(create_app()) as client:
            response = client.post(
                "/api/ai/chat/user",
                json={"question": "Please update board.", "history": []},
            )
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertTrue(payload["patchApplied"])
            self.assertEqual(payload["board"]["cards"]["card-ai-1"]["title"], "AI created card")
            self.assertEqual(
                payload["board"]["cards"]["card-1"]["title"],
                "Card 1 edited by AI",
            )
            self.assertEqual(
                payload["board"]["cards"]["card-1"]["details"],
                "Updated details from AI",
            )
            self.assertEqual(payload["board"]["columns"][4]["id"], "col-done")
            self.assertIn("card-1", payload["board"]["columns"][4]["cardIds"])

            persisted_response = client.get("/api/kanban/user")
            self.assertEqual(persisted_response.status_code, 200)
            persisted_payload = persisted_response.json()
            self.assertEqual(
                persisted_payload["cards"]["card-1"]["title"],
                "Card 1 edited by AI",
            )
            self.assertIn("card-ai-1", persisted_payload["cards"])

    @patch(
        "app.main.run_structured_kanban_chat",
        side_effect=OpenRouterSchemaError(
            "Structured response from OpenRouter failed schema validation."
        ),
    )
    def test_ai_chat_returns_controlled_error_on_schema_failure(self, _: object) -> None:
        with TestClient(create_app()) as client:
            response = client.post(
                "/api/ai/chat/user",
                json={"question": "Make updates", "history": []},
            )

        self.assertEqual(response.status_code, 502)
        self.assertIn("schema validation", response.json()["detail"])

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
                "columns": [
                    {"id": "col-backlog", "title": "Stored", "cardIds": ["card-1"]},
                    {"id": "col-discovery", "title": "Discovery", "cardIds": []},
                    {"id": "col-progress", "title": "In Progress", "cardIds": []},
                    {"id": "col-review", "title": "Review", "cardIds": []},
                    {"id": "col-done", "title": "Done", "cardIds": []},
                ],
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
