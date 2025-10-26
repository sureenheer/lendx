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
from .mpt import (
    create_issuance,
    authorize_holder,
    get_mpt_balance,
    mint_to_holder,
    burn_from_holder,
    destroy_issuance
)

__all__ = [
    # Client functions
    'connect',
    'submit_and_wait',
    'subscribe_account',
    'AccountSubscription',

    # MPT functions
    'create_issuance',
    'authorize_holder',
    'get_mpt_balance',
    'mint_to_holder',
    'burn_from_holder',
    'destroy_issuance',

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