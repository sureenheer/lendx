"""Custom exceptions for XRPL client operations."""

from xrpl.models.exceptions import XRPLException


class XRPLClientError(Exception):
    """Base exception for XRPL client errors."""
    pass


class InsufficientXRP(XRPLClientError):
    """Raised when account has insufficient XRP for operation."""
    pass


class PermissionDenied(XRPLClientError):
    """Raised when operation is not permitted (e.g., account restrictions)."""
    pass


class MaxLedgerExceeded(XRPLClientError):
    """Raised when transaction's LastLedgerSequence has been exceeded."""
    pass


class ConnectionError(XRPLClientError):
    """Raised when connection to XRPL network fails."""
    pass


def wrap_xrpl_exception(func):
    """Decorator to wrap xrpl-py exceptions into custom exceptions."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except XRPLException as e:
            error_msg = str(e).lower()

            if "insufficient" in error_msg and "xrp" in error_msg:
                raise InsufficientXRP(str(e)) from e
            elif "permission" in error_msg or "unauthorized" in error_msg:
                raise PermissionDenied(str(e)) from e
            elif "ledger" in error_msg and ("exceed" in error_msg or "expired" in error_msg):
                raise MaxLedgerExceeded(str(e)) from e
            elif "connection" in error_msg or "network" in error_msg:
                raise ConnectionError(str(e)) from e
            else:
                raise XRPLClientError(str(e)) from e
    return wrapper