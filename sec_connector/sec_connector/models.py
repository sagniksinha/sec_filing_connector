# Building data models with pydantic
# Have added validators wherever was possible

from pydantic import BaseModel, Field, field_validator
from datetime import date


class Company(BaseModel):
    # Company data model
    
    ticker: str = Field(..., min_length=1, description="Stock ticker symbol")
    cik: str = Field(..., min_length=10, max_length=10, description="10-digit CIK number")
    name: str = Field(..., min_length=1, description="Company name")
    
    @field_validator('ticker')
    @classmethod
    def ticker_uppercase(cls, v: str) -> str:
        # uppercase
        return v.upper().strip()
    
    @field_validator('cik')
    @classmethod
    def validate_cik(cls, v: str) -> str:
        # Check CIK is 10 digits
        v = v.strip()
        if not v.isdigit():
            raise ValueError("CIK must contain only digits")
        if len(v) != 10:
            raise ValueError("CIK must be exactly 10 digits")
        return v


class Filing(BaseModel):
    # SEC fillings data model
    
    cik: str = Field(..., description="Company CIK")
    company_name: str = Field(..., description="Company name")
    form_type: str = Field(..., description="Filing form type (e.g., 10-K, 10-Q)")
    filing_date: date = Field(..., description="Date of filing")
    accession_number: str = Field(..., description="Unique filing identifier")
    
    @field_validator('form_type')
    @classmethod
    def normalize_form_type(cls, v: str) -> str:
        # Uppercase
        return v.upper().strip()


class FilingFilter(BaseModel):
    # Search query data model
    
    form_types: list[str] | None = Field(None, description="Filter by form types")
    date_from: date | None = Field(None, description="Start date (inclusive)")
    date_to: date | None = Field(None, description="End date (inclusive)")
    limit: int = Field(10, gt=0, le=1000, description="Maximum results to return")
    
    # Adding field validators to uppercase form type and check dates
    @field_validator('form_types')
    @classmethod
    def normalize_form_types(cls, v: list[str] | None) -> list[str] | None:
        # Uppercase
        if v is None:
            return None
        return [ft.upper().strip() for ft in v if ft.strip()]
    
    @field_validator('date_to')
    @classmethod
    def validate_date_range(cls, v: date | None, info) -> date | None:
        # Check from date is before to date
        if v is not None and info.data.get('date_from') is not None:
            if v < info.data['date_from']:
                raise ValueError("date_to must be >= date_from")
        return v