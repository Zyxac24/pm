from typing import Literal

from pydantic import BaseModel, Field, model_validator


FIXED_COLUMN_IDS: tuple[str, ...] = (
    "col-backlog",
    "col-discovery",
    "col-progress",
    "col-review",
    "col-done",
)


class CardModel(BaseModel):
    id: str
    title: str
    details: str


class ColumnModel(BaseModel):
    id: str
    title: str
    cardIds: list[str]


class BoardModel(BaseModel):
    columns: list[ColumnModel]
    cards: dict[str, CardModel]

    @model_validator(mode="after")
    def validate_board_integrity(self) -> "BoardModel":
        card_keys = set(self.cards.keys())
        seen_card_ids: set[str] = set()
        expected_column_ids = set(FIXED_COLUMN_IDS)
        actual_column_ids = {column.id for column in self.columns}

        if len(self.columns) != len(FIXED_COLUMN_IDS):
            raise ValueError("Board must contain exactly five fixed columns.")
        if len(actual_column_ids) != len(FIXED_COLUMN_IDS):
            raise ValueError("Board columns must have unique identifiers.")
        if actual_column_ids != expected_column_ids:
            raise ValueError("Board is missing one or more required fixed columns.")

        for card_key, card in self.cards.items():
            if card.id != card_key:
                raise ValueError("Card id must match the key in cards map.")

        for column in self.columns:
            for card_id in column.cardIds:
                if card_id not in card_keys:
                    raise ValueError("Column references a card that does not exist.")
                if card_id in seen_card_ids:
                    raise ValueError("Card cannot appear in multiple columns.")
                seen_card_ids.add(card_id)

        return self


class AiTestResponseModel(BaseModel):
    provider: str
    model: str
    prompt: str
    answer: str


class AiHistoryMessageModel(BaseModel):
    role: Literal["user", "assistant"]
    content: str

    @model_validator(mode="after")
    def validate_content(self) -> "AiHistoryMessageModel":
        if not self.content.strip():
            raise ValueError("History message content cannot be empty.")
        return self


class AiChatRequestModel(BaseModel):
    question: str
    history: list[AiHistoryMessageModel] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_question(self) -> "AiChatRequestModel":
        if not self.question.strip():
            raise ValueError("Question cannot be empty.")
        return self


class AiPatchOperationModel(BaseModel):
    op: Literal["create_card", "edit_card", "move_card"]
    cardId: str | None = None
    title: str | None = None
    details: str | None = None
    columnId: str | None = None
    targetColumnId: str | None = None
    position: int | None = None

    @model_validator(mode="after")
    def validate_operation_fields(self) -> "AiPatchOperationModel":
        if self.position is not None and self.position < 0:
            raise ValueError("Patch position cannot be negative.")

        if self.op == "create_card":
            if self.columnId is None:
                raise ValueError("create_card requires columnId.")
            if self.title is None or not self.title.strip():
                raise ValueError("create_card requires non-empty title.")
            return self

        if self.op == "edit_card":
            if self.cardId is None:
                raise ValueError("edit_card requires cardId.")
            if self.title is None and self.details is None:
                raise ValueError("edit_card requires at least one field to update.")
            return self

        if self.op == "move_card":
            if self.cardId is None:
                raise ValueError("move_card requires cardId.")
            if self.targetColumnId is None:
                raise ValueError("move_card requires targetColumnId.")
            return self

        return self


class AiBoardPatchModel(BaseModel):
    operations: list[AiPatchOperationModel]

    @model_validator(mode="after")
    def validate_operations(self) -> "AiBoardPatchModel":
        if not self.operations:
            raise ValueError("Patch operations cannot be empty.")
        return self


class AiAssistantResponseModel(BaseModel):
    message: str
    patch: AiBoardPatchModel | None = None

    @model_validator(mode="after")
    def validate_message(self) -> "AiAssistantResponseModel":
        if not self.message.strip():
            raise ValueError("Assistant message cannot be empty.")
        return self


class AiChatResponseModel(BaseModel):
    message: str
    patchApplied: bool
    board: BoardModel
