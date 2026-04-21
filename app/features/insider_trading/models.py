from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import date
from .schemas import TransactionType

class InsiderTrade(SQLModel, table=True):
    __tablename__ = "insider_trades"
    id: Optional[int] = Field(default=None, primary_key=True)
    document_url: str = Field(unique=True, index=True)
    pdmr_name: str
    role_position: str
    issuer_name: str
    issuer_lei: str = Field(max_length=20)
    instrument_description: str
    isin: str = Field(max_length=12)
    nature_of_transaction: TransactionType
    price_volume: str
    aggregated_volume: int
    weighted_average_price: float
    date_of_transaction: date
    place_of_transaction: str
