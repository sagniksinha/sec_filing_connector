"""Tests for SEC EDGAR client."""

import pytest
from datetime import date
from sec_connector.client import SECClient
from sec_connector.models import Company, Filing, FilingFilter
from pydantic import ValidationError


# Test fixtures
@pytest.fixture
def companies_data():
    """Sample company data in the given format."""
    return {
        "0": {
            "cik_str": 320193,
            "ticker": "AAPL",
            "title": "Apple Inc."
        },
        "1": {
            "cik_str": 789019,
            "ticker": "MSFT",
            "title": "Microsoft Corp"
        },
        "2": {
            "cik_str": 1318605,
            "ticker": "TSLA",
            "title": "Tesla Inc"
        }
    }


@pytest.fixture
def filings_data():
    """Sample filings data."""
    return {
        "0000320193": [
            {
                "company_name": "Apple Inc.",
                "form_type": "10-K",
                "filing_date": "2024-11-01",
                "accession_number": "0000320193-24-000123"
            },
            {
                "company_name": "Apple Inc.",
                "form_type": "10-Q",
                "filing_date": "2024-08-01",
                "accession_number": "0000320193-24-000100"
            },
            {
                "company_name": "Apple Inc.",
                "form_type": "10-Q",
                "filing_date": "2024-05-01",
                "accession_number": "0000320193-24-000075"
            },
            {
                "company_name": "Apple Inc.",
                "form_type": "8-K",
                "filing_date": "2024-03-15",
                "accession_number": "0000320193-24-000050"
            },
            {
                "company_name": "Apple Inc.",
                "form_type": "10-K",
                "filing_date": "2023-11-02",
                "accession_number": "0000320193-23-000123"
            }
        ],
        "0000789019": [
            {
                "company_name": "Microsoft Corp",
                "form_type": "10-K",
                "filing_date": "2024-07-30",
                "accession_number": "0000789019-24-000100"
            }
        ]
    }


@pytest.fixture
def client(companies_data, filings_data):
    """Create test client."""
    return SECClient(companies_data, filings_data)


# Task 1: Model Tests
class TestModels:
    """Test data models."""
    
    def test_company_validation_success(self):
        """Test valid company creation."""
        company = Company(
            ticker="AAPL",
            cik="0000320193",
            name="Apple Inc."
        )
        assert company.ticker == "AAPL"
        assert company.cik == "0000320193"
        assert company.name == "Apple Inc."
    
    def test_company_ticker_normalization(self):
        """Test ticker is normalized to uppercase."""
        company = Company(
            ticker="aapl",
            cik="0000320193",
            name="Apple Inc."
        )
        assert company.ticker == "AAPL"
    
    def test_company_cik_validation_fails(self):
        """Test CIK validation rejects invalid format."""
        with pytest.raises(ValidationError):
            Company(ticker="AAPL", cik="123", name="Apple Inc.")
        
        with pytest.raises(ValidationError):
            Company(ticker="AAPL", cik="abc1234567", name="Apple Inc.")
    
    def test_filing_validation_success(self):
        """Test valid filing creation."""
        filing = Filing(
            cik="0000320193",
            company_name="Apple Inc.",
            form_type="10-K",
            filing_date=date(2024, 11, 1),
            accession_number="0000320193-24-000123"
        )
        assert filing.form_type == "10-K"
        assert filing.filing_date == date(2024, 11, 1)
    
    def test_filing_filter_defaults(self):
        """Test filter defaults."""
        filters = FilingFilter()
        assert filters.form_types is None
        assert filters.date_from is None
        assert filters.date_to is None
        assert filters.limit == 10
    
    def test_filing_filter_date_range_validation(self):
        """Test date range validation."""
        with pytest.raises(ValidationError):
            FilingFilter(
                date_from=date(2024, 12, 1),
                date_to=date(2024, 1, 1)
            )


# Task 2: Company Lookup Tests
class TestCompanyLookup:
    """Test company lookup functionality."""
    
    def test_lookup_valid_ticker(self, client):
        """Test successful company lookup."""
        company = client.lookup_company("AAPL")
        assert company.ticker == "AAPL"
        assert company.cik == "0000320193"
        assert company.name == "Apple Inc."
    
    def test_lookup_case_insensitive(self, client):
        """Test lookup is case-insensitive."""
        company = client.lookup_company("aapl")
        assert company.ticker == "AAPL"
    
    def test_lookup_cik_zero_padded(self, client):
        """Test CIK is zero-padded to 10 digits."""
        company = client.lookup_company("AAPL")
        assert len(company.cik) == 10
        assert company.cik.startswith("0")
    
    def test_lookup_invalid_ticker_raises(self, client):
        """Test invalid ticker raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            client.lookup_company("INVALID")
    
    def test_lookup_empty_ticker_raises(self, client):
        """Test empty ticker raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            client.lookup_company("")
        
        with pytest.raises(ValueError, match="cannot be empty"):
            client.lookup_company("   ")


# Task 3: Filing Filter Tests
class TestFilingFilters:
    """Test filing filtering functionality."""
    
    def test_list_filings_no_filters(self, client):
        """Test listing filings without filters returns all (limited)."""
        filters = FilingFilter(limit=10)
        filings = client.list_filings("0000320193", filters)
        
        assert len(filings) == 5  # All AAPL filings
        assert all(isinstance(f, Filing) for f in filings)
    
    def test_list_filings_sorted_descending(self, client):
        """Test filings are sorted by date descending."""
        filters = FilingFilter()
        filings = client.list_filings("0000320193", filters)
        
        dates = [f.filing_date for f in filings]
        assert dates == sorted(dates, reverse=True)
    
    def test_filter_by_form_type_single(self, client):
        """Test filtering by single form type."""
        filters = FilingFilter(form_types=["10-K"])
        filings = client.list_filings("0000320193", filters)
        
        assert len(filings) == 2
        assert all(f.form_type == "10-K" for f in filings)
    
    def test_filter_by_form_type_multiple(self, client):
        """Test filtering by multiple form types."""
        filters = FilingFilter(form_types=["10-K", "10-Q"])
        filings = client.list_filings("0000320193", filters)
        
        assert len(filings) == 4
        assert all(f.form_type in ["10-K", "10-Q"] for f in filings)
    
    def test_filter_by_date_from(self, client):
        """Test filtering by start date."""
        filters = FilingFilter(date_from=date(2024, 5, 1))
        filings = client.list_filings("0000320193", filters)
        
        assert all(f.filing_date >= date(2024, 5, 1) for f in filings)
        assert len(filings) == 3
    
    def test_filter_by_date_to(self, client):
        """Test filtering by end date."""
        filters = FilingFilter(date_to=date(2024, 6, 1))
        filings = client.list_filings("0000320193", filters)
        
        assert all(f.filing_date <= date(2024, 6, 1) for f in filings)
    
    def test_filter_by_date_range(self, client):
        """Test filtering by date range."""
        filters = FilingFilter(
            date_from=date(2024, 3, 1),
            date_to=date(2024, 8, 31)
        )
        filings = client.list_filings("0000320193", filters)
        
        assert len(filings) == 3
        assert all(
            date(2024, 3, 1) <= f.filing_date <= date(2024, 8, 31)
            for f in filings
        )
    
    def test_filter_limit_respected(self, client):
        """Test limit parameter is respected."""
        filters = FilingFilter(limit=2)
        filings = client.list_filings("0000320193", filters)
        
        assert len(filings) == 2
    
    def test_filter_combined(self, client):
        """Test combining multiple filters."""
        filters = FilingFilter(
            form_types=["10-Q"],
            date_from=date(2024, 1, 1),
            limit=1
        )
        filings = client.list_filings("0000320193", filters)
        
        assert len(filings) == 1
        assert filings[0].form_type == "10-Q"
        assert filings[0].filing_date >= date(2024, 1, 1)
    
    def test_list_filings_invalid_cik_raises(self, client):
        """Test invalid CIK raises ValueError."""
        filters = FilingFilter()
        with pytest.raises(ValueError, match="No filings found"):
            client.list_filings("9999999999", filters)
    
    def test_list_filings_empty_cik_raises(self, client):
        """Test empty CIK raises ValueError."""
        filters = FilingFilter()
        with pytest.raises(ValueError, match="cannot be empty"):
            client.list_filings("", filters)


# Edge Cases
class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_client_with_no_filings_data(self, companies_data):
        """Test client works with no filings data."""
        client = SECClient(companies_data)
        
        company = client.lookup_company("AAPL")
        assert company.ticker == "AAPL"
        
        # Should raise error when trying to list filings
        with pytest.raises(ValueError):
            client.list_filings(company.cik, FilingFilter())
    
    def test_invalid_limit_values(self):
        """Test invalid limit values are rejected."""
        with pytest.raises(ValidationError):
            FilingFilter(limit=0)
        
        with pytest.raises(ValidationError):
            FilingFilter(limit=-1)
        
        with pytest.raises(ValidationError):
            FilingFilter(limit=2000)  # Over max
    
    def test_form_type_case_insensitive(self, client):
        """Test form type filtering is case-insensitive."""
        filters1 = FilingFilter(form_types=["10-k"])
        filters2 = FilingFilter(form_types=["10-K"])
        
        filings1 = client.list_filings("0000320193", filters1)
        filings2 = client.list_filings("0000320193", filters2)
        
        assert len(filings1) == len(filings2)