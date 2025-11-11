# SEC EDGAR Connector

SEC EDGAR filings by company ticker, form type, and date range.

## Installation

```bash
pip install -e .
```

## Example CLI Usage

```bash
# Basic usage - get latest filings for a company
python -m sec_connector.cli AAPL

# Filter by form type
python -m sec_connector.cli AAPL --form 10-K

# Multiple form types with limit
python -m sec_connector.cli MSFT --form 10-K 10-Q --limit 5

# Filter by date range
python -m sec_connector.cli TSLA --date-from 2024-01-01 --date-to 2024-12-31

# Combined filters
python -m sec_connector.cli GOOGL --form 10-K --date-from 2023-01-01 --limit 3

# JSON output
python -m sec_connector.cli AMZN --form 10-Q --json
```