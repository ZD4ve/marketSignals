from sqlmodel import SQLModel, Field
from typing import Optional

class InsiderTrade(SQLModel, table=True):
    __tablename__ = "insider_trades"
    id: Optional[int] = Field(default=None, primary_key=True)
    document_url: str = Field(unique=True, index=True)
    pdmr_name: str
    role_position: str
    issuer_name: str
    issuer_lei: str
    instrument_description: str
    isin: str
    nature_of_transaction: str
    price_volume: str
    aggregated_volume: str
    weighted_average_price: str
    date_of_transaction: str
    place_of_transaction: str
