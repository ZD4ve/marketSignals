from pydantic import BaseModel, Field

class EUMarArticle19(BaseModel):
    """Extraction schema for EU MAR Article 19 Insider Trading Notifications."""
    pdmr_name: str = Field(..., description="PDMR / PCA Name")
    role_position: str = Field(..., description="Role/Position")
    issuer_name: str = Field(..., description="Issuer Name")
    issuer_lei: str = Field(..., description="Issuer LEI")
    instrument_description: str = Field(..., description="Instrument Description & Type")
    isin: str = Field(..., description="ISIN")
    nature_of_transaction: str = Field(..., description="Nature of Transaction (e.g., Acquisition, Disposal)")
    price_volume: str = Field(..., description="Price(s) and Volume(s) representation or list")
    aggregated_volume: str = Field(...)
    weighted_average_price: str = Field(...)
    date_of_transaction: str = Field(...)
    place_of_transaction: str = Field(...)
