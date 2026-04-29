from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import date, datetime
from .schemas import TransactionType

class InsiderTrade(SQLModel, table=True):
    __tablename__ = "insider_trades"
    id: Optional[int] = Field(default=None, primary_key=True)
    document_url: str = Field(unique=True, index=True)
    pdmr_name: Optional[str] = None
    role_position: Optional[str] = None
    issuer_name: Optional[str] = None
    issuer_lei: Optional[str] = Field(default=None, max_length=20)
    instrument_description: Optional[str] = None
    isin: Optional[str] = Field(default=None, max_length=12)
    nature_of_transaction: Optional[TransactionType] = None
    price_volume: Optional[str] = None
    aggregated_volume: Optional[int] = None
    weighted_average_price: Optional[float] = None
    date_of_transaction: Optional[date] = None
    place_of_transaction: Optional[str] = None
    published_date: Optional[datetime] = None
    has_missing_fields: bool = Field(default=False, index=True)
