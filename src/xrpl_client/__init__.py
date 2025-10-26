"""XRPL client package for connection and transaction handling."""

from .client import connect, submit_and_wait, subscribe_account, AccountSubscription
from .config import (
    TESTNET_URL,
    MAINNET_URL,
    BASE_RESERVE_DROPS,
    OWNER_RESERVE_DROPS,
    BASE_FEE_DROPS,
    HIGH_FEE_DROPS,
    TESTNET_ID,
    MAINNET_ID
)
from .exceptions import (
    XRPLClientError,
    InsufficientXRP,
    PermissionDenied,
    MaxLedgerExceeded,
    ConnectionError,
    wrap_xrpl_exception
)

__all__ = [
    # Client functions
    'connect',
    'submit_and_wait',
    'subscribe_account',
    'AccountSubscription',

    # Configuration
    'TESTNET_URL',
    'MAINNET_URL',
    'BASE_RESERVE_DROPS',
    'OWNER_RESERVE_DROPS',
    'BASE_FEE_DROPS',
    'HIGH_FEE_DROPS',
    'TESTNET_ID',
    'MAINNET_ID',

    # Exceptions
    'XRPLClientError',
    'InsufficientXRP',
    'PermissionDenied',
    'MaxLedgerExceeded',
    'ConnectionError',
    'wrap_xrpl_exception'
]