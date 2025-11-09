"""SEC EDGAR filing connector."""

from sec_connector.models import Company, Filing, FilingFilter
from sec_connector.client import SECClient

__version__ = "0.1.0"
__all__ = ["Company", "Filing", "FilingFilter", "SECClient"]