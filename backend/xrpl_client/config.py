"""XRPL network configuration and constants."""

# Network JSON-RPC URLs
TESTNET_URL = "https://s.altnet.rippletest.net:51234/"
MAINNET_URL = "https://s1.ripple.com:51234/"

# Reserve amounts (in drops - 1 XRP = 1,000,000 drops)
BASE_RESERVE_DROPS = 10_000_000  # 10 XRP base reserve
OWNER_RESERVE_DROPS = 2_000_000  # 2 XRP per owned object

# Base transaction fees (in drops)
BASE_FEE_DROPS = 10  # Standard base fee
HIGH_FEE_DROPS = 12  # Higher fee for faster processing

# Network identifiers
TESTNET_ID = 1
MAINNET_ID = 0