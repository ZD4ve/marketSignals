from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import date
from enum import Enum

class TransactionType(str, Enum):
    buy = "buy"
    sell = "sell"
    other = "other"

class EUMarArticle19(BaseModel):
    """Extraction schema for EU MAR Article 19 Insider Trading Notifications."""
    pdmr_name: str | None = Field(default=None, description="Name of the Person Discharging Managerial Responsibilities (PDMR) or person closely associated.")
    role_position: str | None = Field(default=None, description="Position/status of the PDMR within the company.")
    issuer_name: str | None = Field(default=None, description="Name of the issuer company.")
    issuer_lei: str | None = Field(
        default=None,
        pattern=r"^[A-Z0-9]{20}$",
        description="LEI (Legal Entity Identifier) code of the issuer, formatted as a 20-character uppercase alphanumeric code based on ISO 17442.",
    )
    instrument_description: str | None = Field(default=None, description="Description of the financial instrument (e.g., ordinary share).")
    isin: str | None = Field(
        default=None,
        pattern=r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$",
        description="ISIN code of the financial instrument, formatted as a 12-character code per ISO 6166: two letters, nine alphanumeric NSIN characters, and one numeric check digit.",
    )
    nature_of_transaction: TransactionType | None = Field(default=None, description="Nature of the transaction: 'buy' (Vétel) or 'sell' (Eladás).")
    price_volume: str | None = Field(default=None, description="Raw text describing the individual price(s) and volume(s) of the transaction tranches.")
    aggregated_volume: int | None = Field(default=None, description="Total aggregated volume (number of shares) of the transaction. Extract only the numeric integer value.")
    weighted_average_price: float | None = Field(default=None, description="Weighted average price of the transaction in HUF. Extract only the numeric float value. May be next to the aggregated volume.")
    date_of_transaction: date | None = Field(default=None, description="Date of the transaction.")
    place_of_transaction: str | None = Field(default=None, description="Place of the transaction (e.g., Budapesti Értéktőzsde, BÉT, OTC).")
    has_missing_fields: bool = Field(
        default=False,
        description="True when the source document did not contain one or more Article 19 fields.",
    )

    @staticmethod
    def _expand_isin_characters(value: str) -> str:
        # ISO 6166 expands letters as A=10 ... Z=35 before applying Luhn.
        return "".join(str(ord(char) - 55) if char.isalpha() else char for char in value)

    @classmethod
    def _passes_luhn(cls, digits: str) -> bool:
        total = 0
        for idx, char in enumerate(reversed(digits)):
            digit = int(char)
            if idx % 2 == 1:
                digit *= 2
                if digit > 9:
                    digit -= 9
            total += digit
        return total % 10 == 0

    @field_validator("isin")
    @classmethod
    def validate_isin_check_digit(cls, value: str) -> str:
        if value is None:
            return value
        expanded = cls._expand_isin_characters(value)
        if not cls._passes_luhn(expanded):
            raise ValueError("Invalid ISIN check digit.")
        return value

    def missing_fields(self) -> list[str]:
        return [field_name for field_name, field_value in self.model_dump().items() if field_value is None]


class InsiderExtractionResult(BaseModel):
    """LLM output for either insider trade extraction or high-certainty rejection."""

    is_insider_trading: bool = Field(
        description="True when the document is an EU MAR Article 19 PDMR transaction notification (including routine buy/sell disclosures)."
    )
    certainty: float = Field(
        ge=0.0,
        le=1.0,
        description="Model certainty score between 0 and 1. For non-insider verdicts this must be exactly 1.0.",
    )
    non_insider_reason: str | None = Field(
        default=None,
        description="Required when is_insider_trading is false. Briefly explain why the document is certainly not an Article 19 PDMR notification.",
    )
    evidence_snippets: list[str] = Field(
        default_factory=list,
        description="Short snippets copied from the source document that support the verdict.",
    )
    insider_trade: EUMarArticle19 | None = Field(
        default=None,
        description="Required when is_insider_trading is true.",
    )

    @model_validator(mode="after")
    def validate_verdict_consistency(self) -> "InsiderExtractionResult":
        if self.is_insider_trading:
            if self.insider_trade is None:
                raise ValueError("insider_trade is required when is_insider_trading is true.")
            return self

        if self.certainty != 1.0:
            raise ValueError("A non-insider verdict is only allowed at certainty=1.0.")
        if self.insider_trade is not None:
            raise ValueError("insider_trade must be empty when is_insider_trading is false.")
        if not self.non_insider_reason:
            raise ValueError("non_insider_reason is required when is_insider_trading is false.")
        if len(self.evidence_snippets) == 0:
            raise ValueError("evidence_snippets must include at least one snippet for non-insider verdicts.")
        return self
