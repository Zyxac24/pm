from copy import deepcopy
from typing import Any
from uuid import uuid4

from app.models import AiBoardPatchModel, FlexibleBoardModel


class AiPatchError(Exception):
    pass


def apply_ai_patch(board: dict[str, Any], patch: AiBoardPatchModel) -> dict[str, Any]:
    validated_board = FlexibleBoardModel.model_validate(board).model_dump(mode="json")
    next_board = deepcopy(validated_board)
    columns = next_board["columns"]
    cards = next_board["cards"]

    for operation in patch.operations:
        if operation.op == "create_card":
            target_column = _find_column(columns, operation.columnId)
            if target_column is None:
                raise AiPatchError(f"Column '{operation.columnId}' does not exist.")

            card_id = operation.cardId or _generate_card_id()
            if card_id in cards:
                raise AiPatchError(f"Card '{card_id}' already exists.")

            title = (operation.title or "").strip()
            if not title:
                raise AiPatchError("Create operation requires a non-empty title.")

            details = operation.details if operation.details is not None else "No details yet."
            cards[card_id] = {"id": card_id, "title": title, "details": details}
            _insert_card_id(target_column["cardIds"], card_id, operation.position)
            continue

        if operation.op == "edit_card":
            if operation.cardId is None or operation.cardId not in cards:
                raise AiPatchError(f"Card '{operation.cardId}' does not exist.")

            target_card = cards[operation.cardId]
            if operation.title is not None:
                title = operation.title.strip()
                if not title:
                    raise AiPatchError("Edit operation cannot set an empty title.")
                target_card["title"] = title
            if operation.details is not None:
                target_card["details"] = operation.details
            continue

        if operation.op == "move_card":
            if operation.cardId is None:
                raise AiPatchError("Move operation requires cardId.")
            if operation.cardId not in cards:
                raise AiPatchError(f"Card '{operation.cardId}' does not exist.")
            target_column = _find_column(columns, operation.targetColumnId)
            if target_column is None:
                raise AiPatchError(
                    f"Target column '{operation.targetColumnId}' does not exist."
                )
            source_column = _find_column_with_card(columns, operation.cardId)
            if source_column is None:
                raise AiPatchError(f"Card '{operation.cardId}' is not in any column.")

            source_column["cardIds"] = [
                card_id for card_id in source_column["cardIds"] if card_id != operation.cardId
            ]
            _insert_card_id(target_column["cardIds"], operation.cardId, operation.position)
            continue

        raise AiPatchError(f"Unsupported patch operation '{operation.op}'.")

    return FlexibleBoardModel.model_validate(next_board).model_dump(mode="json")


def _find_column(columns: list[dict[str, Any]], column_id: str | None) -> dict[str, Any] | None:
    if column_id is None:
        return None
    for column in columns:
        if column.get("id") == column_id:
            return column
    return None


def _find_column_with_card(
    columns: list[dict[str, Any]],
    card_id: str,
) -> dict[str, Any] | None:
    for column in columns:
        if card_id in column["cardIds"]:
            return column
    return None


def _insert_card_id(card_ids: list[str], card_id: str, position: int | None) -> None:
    if position is None or position >= len(card_ids):
        card_ids.append(card_id)
        return

    insert_position = max(0, position)
    card_ids.insert(insert_position, card_id)


def _generate_card_id() -> str:
    return f"card-ai-{uuid4().hex[:10]}"
