from classes.schemas.base_schema import BaseSchema
from datetime import datetime
from enum import Enum


class Direction(Enum):
    INCOME = 0
    OUTCOME = 1


class TransactionAdd(BaseSchema):
    timestamp: datetime = datetime.now()
    wallet_id: int
    direction: Direction
    amount: int
    category_id: int | None = None
    transfer_id: int | None = None

    


class TransactionTotalsResultItem(BaseSchema):
    category: str
    direction: Direction
    amount: int
