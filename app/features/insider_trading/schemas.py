from pydantic import BaseModel, Field
from datetime import date
from enum import Enum

class TransactionType(str, Enum):
    buy = "buy"
    sell = "sell"
    other = "other"

class EUMarArticle19(BaseModel):
    """Extraction schema for EU MAR Article 19 Insider Trading Notifications."""
    pdmr_name: str = Field(description="Name of the Person Discharging Managerial Responsibilities (PDMR) or person closely associated.")
    role_position: str = Field(description="Position/status of the PDMR within the company.")
    issuer_name: str = Field(description="Name of the issuer company.")
    issuer_lei: str = Field(
        pattern=r"^[A-Z0-9]{20}$",
        description="LEI (Legal Entity Identifier) code of the issuer, formatted as a 20-character uppercase alphanumeric code based on ISO 17442.",
    )
    instrument_description: str = Field(description="Description of the financial instrument (e.g., ordinary share).")
    isin: str = Field(
        pattern=r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$",
        description="ISIN code of the financial instrument, formatted as a 12-character code per ISO 6166: two letters, nine alphanumeric NSIN characters, and one numeric check digit.",
    )
    nature_of_transaction: TransactionType = Field(description="Nature of the transaction: 'buy' (Vétel) or 'sell' (Eladás).")
    price_volume: str = Field(description="Raw text describing the individual price(s) and volume(s) of the transaction tranches.")
    aggregated_volume: int = Field(description="Total aggregated volume (number of shares) of the transaction. Extract only the numeric integer value.")
    weighted_average_price: float = Field(description="Weighted average price of the transaction in HUF. Extract only the numeric float value. May be next to the aggregated volume.")
    date_of_transaction: date = Field(description="Date of the transaction.")
    place_of_transaction: str = Field(description="Place of the transaction (e.g., Budapesti Értéktőzsde, BÉT, OTC).")
