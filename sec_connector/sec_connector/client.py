# Company Lookup
from datetime import date
from typing import Any
from sec_connector.models import Company, Filing, FilingFilter

class SECClient:
    def __init__(self, companies_data: dict[str, dict], filings_data: dict[str, list[dict]] | None = None):
        # Convert the indexed format to ticker-based lookup for efficiency
        self._companies_by_ticker = {}
        for key, company_info in companies_data.items():
            ticker = company_info['ticker'].upper().strip()
            self._companies_by_ticker[ticker] = company_info
        self._filings = filings_data or {}
    
    def lookup_company(self, ticker: str) -> Company:
        # Find company by ticker symbol
        if not ticker or not ticker.strip():
            raise ValueError("Ticker cannot be empty")
        ticker = ticker.upper().strip()
        if ticker not in self._companies_by_ticker:
            raise ValueError(f"Ticker '{ticker}' not found")
        company_data = self._companies_by_ticker[ticker]
        # Pad CIK to 10 digits (cik_str is an integer in the given format)
        cik = str(company_data['cik_str']).zfill(10)
        return Company(ticker=ticker,cik=cik,name=company_data['title'])
    
    def list_filings(self, cik: str, filters: FilingFilter) -> list[Filing]:
        # Get filings for a CIK, applying filters
        if not cik or not cik.strip():
            raise ValueError("CIK cannot be empty")
        # Normalize CIK
        cik = cik.strip().zfill(10)
        if cik not in self._filings:
            raise ValueError(f"No filings found for CIK '{cik}'")
        
        raw_filings = self._filings[cik]
        filings = []
        # Convert raw data to Filing objects
        for filing_data in raw_filings:
            try:
                filing = Filing(
                    cik=cik,
                    company_name=filing_data['company_name'],
                    form_type=filing_data['form_type'],
                    filing_date=self._parse_date(filing_data['filing_date']),
                    accession_number=filing_data['accession_number']
                )
                filings.append(filing)
            except Exception:
                # Skip invalid filings
                continue
        # Apply filters
        filtered = self._apply_filters(filings, filters)
        # Sort by date descending
        filtered.sort(key=lambda f: f.filing_date, reverse=True)
        return filtered[:filters.limit]
    
    def _parse_date(self, date_str: str) -> date:
        # Parse date string in YYYY-MM-DD format.
        try:
            parts = date_str.split('-')
            return date(int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError):
            raise ValueError(f"Invalid date format: {date_str}")
    
    def _apply_filters(self, filings: list[Filing], filters: FilingFilter) -> list[Filing]:
        # Apply filter criteria to filings list.
        result = filings

        # Filter by form types
        if filters.form_types:
            form_types_upper = [ft.upper() for ft in filters.form_types]
            result = [f for f in result if f.form_type.upper() in form_types_upper]
        # Filter by date range
        if filters.date_from:
            result = [f for f in result if f.filing_date >= filters.date_from]
        if filters.date_to:
            result = [f for f in result if f.filing_date <= filters.date_to]
        return result