# Code to test

import pytest
from datetime import date
from sec_connector.client import SECClient
from sec_connector.models import Company, Filing, FilingFilter
from pydantic import ValidationError

# Setting up Fixtures
@pytest.fixture
def companies_data():
    return {
        "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
        "1": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corp"},
    }

@pytest.fixture
def filings_data():
    return {
        "0000320193": [
            {
                "company_name": "Apple Inc.",
                "form_type": "10-K",
                "filing_date": "2024-11-01",
                "accession_number": "0000320193-24-000123",
            },
            {
                "company_name": "Apple Inc.",
                "form_type": "10-Q",
                "filing_date": "2024-08-01",
                "accession_number": "0000320193-24-000100",
            },
            {
                "company_name": "Apple Inc.",
                "form_type": "8-K",
                "filing_date": "2024-03-15",
                "accession_number": "0000320193-24-000050",
            },
        ]
    }

@pytest.fixture
def client(companies_data, filings_data):
    return SECClient(companies_data, filings_data)

# Model test
class TestModels:
    def test_company_valid(self):
        company = Company(ticker="aapl", cik="0000320193", name="Apple Inc.")
        assert company.ticker == "AAPL"
        assert company.cik == "0000320193"

    def test_filing_valid(self):
        filing = Filing(
            cik="0000320193",
            company_name="Apple Inc.",
            form_type="10-K",
            filing_date=date(2024, 11, 1),
            accession_number="0000320193-24-000123",
        )
        assert filing.form_type == "10-K"

# Company Lookup Tests
class TestCompanyLookup:
    def test_lookup_success(self, client):
        c = client.lookup_company("aapl")
        assert c.name == "Apple Inc."
        assert c.cik == "0000320193"

    def test_lookup_invalid(self, client):
        with pytest.raises(ValueError):
            client.lookup_company("INVALID")

# Edge Case
class TestEdgeCase:
    def test_empty_filings_data(self, companies_data):
        client = SECClient(companies_data)
        with pytest.raises(ValueError):
            client.list_filings("0000320193", FilingFilter())