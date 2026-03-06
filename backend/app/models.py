from pydantic import BaseModel, model_validator


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
