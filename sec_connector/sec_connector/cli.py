# Simple command-line interface in cli.py
import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import NoReturn
from sec_connector.client import SECClient
from sec_connector.models import FilingFilter

def load_json(filepath: Path) -> dict:
    # Load JSON file.
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading {filepath}: {e}", file=sys.stderr)
        sys.exit(1)

def parse_date(date_str: str) -> date:
    # Parse date string in YYYY-MM-DD format
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")

def print_table(filings: list) -> None:
    # Print filings as a formatted table.
    if not filings:
        print("No filings found.")
        return
    # Calculate column widths
    headers = ['Date', 'Form Type', 'Company', 'Accession Number']
    rows = []
    for filing in filings:
        rows.append([
            str(filing.filing_date),
            filing.form_type,
            filing.company_name[:40],  # Truncate long names
            filing.accession_number
        ])
    # Calculate widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    # Print header
    header_line = ' | '.join(h.ljust(w) for h, w in zip(headers, widths))
    print(header_line)
    print('-' * len(header_line))
    # Print rows
    for row in rows:
        print(' | '.join(cell.ljust(w) for cell, w in zip(row, widths)))

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Fetch SEC EDGAR filings for a company',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
            %(prog)s AAPL
            %(prog)s AAPL --form 10-K --limit 5
            %(prog)s MSFT --form 10-Q 10-K --date-from 2023-01-01 --date-to 2023-12-31
            %(prog)s TSLA --json"""
    )
    
    parser.add_argument('ticker', help='Company ticker symbol')
    parser.add_argument('--form', nargs='+', help='Filter by form type(s)', metavar='TYPE')
    parser.add_argument('--date-from', type=parse_date, help='Start date (YYYY-MM-DD)', metavar='DATE')
    parser.add_argument('--date-to', type=parse_date, help='End date (YYYY-MM-DD)', metavar='DATE')
    parser.add_argument('--limit', type=int, default=10, help='Maximum results (default: 10)')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--companies-file', type=Path, 
                       default=Path('tests/fixtures/company_tickers.json'),
                       help='Path to company tickers JSON file')
    parser.add_argument('--filings-file', type=Path,
                       default=Path('tests/fixtures/filings_sample.json'),
                       help='Path to filings JSON file')
    args = parser.parse_args()
    # Load data
    try:
        companies_data = load_json(args.companies_file)
        filings_data = load_json(args.filings_file)
    except SystemExit:
        return
    # Initialize client
    client = SECClient(companies_data, filings_data)
    # Lookup company
    try:
        company = client.lookup_company(args.ticker)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    # Create filter
    try:
        filters = FilingFilter(
            form_types=args.form,
            date_from=args.date_from,
            date_to=args.date_to,
            limit=args.limit
        )
    except ValueError as e:
        print(f"Error: Invalid filter: {e}", file=sys.stderr)
        sys.exit(1)
    # Get filings
    try:
        filings = client.list_filings(company.cik, filters)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    # Output results
    if args.json:
        output = {
            'company': company.model_dump(),
            'filings': [f.model_dump(mode='json') for f in filings],
            'count': len(filings)
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        print(f"\nFilings for {company.name} ({company.ticker})")
        print(f"CIK: {company.cik}\n")
        print_table(filings)
        print(f"\nTotal: {len(filings)} filing(s)")

if __name__ == "__main__":
    main()