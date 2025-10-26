"""XRPL client connection and transaction handling."""

from typing import Literal, Callable, Dict, Any
import asyncio
import logging
from xrpl.clients import JsonRpcClient, WebsocketClient
from xrpl.models import Transaction
from xrpl.transaction import submit_and_wait, autofill_and_sign
from xrpl.wallet import Wallet
from xrpl.asyncio.clients import AsyncWebsocketClient

from .config import TESTNET_URL, MAINNET_URL
from .exceptions import (
    wrap_xrpl_exception,
    ConnectionError,
    XRPLClientError
)

logger = logging.getLogger(__name__)


@wrap_xrpl_exception
def connect(network: Literal['testnet', 'mainnet']) -> JsonRpcClient:
    """
    Connect to XRPL network and return a connected client.

    Args:
        network: Target network ('testnet' or 'mainnet')

    Returns:
        Connected XRPL JsonRpcClient

    Raises:
        ConnectionError: If connection to network fails
        ValueError: If invalid network specified
    """
    if network == 'testnet':
        url = TESTNET_URL
    elif network == 'mainnet':
        url = MAINNET_URL
    else:
        raise ValueError(f"Invalid network: {network}. Must be 'testnet' or 'mainnet'")

    try:
        client = JsonRpcClient(url)
        # Test connection
        client.request({"command": "server_info"})
        logger.info(f"Successfully connected to {network} at {url}")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to {network}: {e}")
        raise ConnectionError(f"Failed to connect to {network}: {e}") from e


@wrap_xrpl_exception
def submit_and_wait(client: JsonRpcClient, tx: Dict[str, Any], wallet: Wallet) -> Dict[str, Any]:
    """
    Sign transaction with autofill, submit it, and wait for validation.

    Args:
        client: Connected XRPL client
        tx: Transaction dictionary to submit
        wallet: Wallet to sign transaction with

    Returns:
        Transaction response dictionary

    Raises:
        XRPLClientError: If transaction fails or times out
    """
    try:
        # Convert dict to Transaction object if needed
        if isinstance(tx, dict):
            tx_obj = Transaction.from_dict(tx)
        else:
            tx_obj = tx

        # Autofill and sign the transaction
        signed_tx = autofill_and_sign(tx_obj, client, wallet)

        # Submit and wait for validation
        response = submit_and_wait(signed_tx, client)

        logger.info(f"Transaction submitted successfully: {response.result.get('hash')}")
        return response.result

    except Exception as e:
        logger.error(f"Transaction submission failed: {e}")
        raise


class AccountSubscription:
    """Manages WebSocket subscription for account updates."""

    def __init__(self, client: AsyncWebsocketClient, address: str, callback: Callable):
        self.client = client
        self.address = address
        self.callback = callback
        self._running = False

    async def start(self):
        """Start the subscription."""
        self._running = True
        subscribe_request = {
            "command": "subscribe",
            "accounts": [self.address]
        }

        try:
            await self.client.send(subscribe_request)
            logger.info(f"Subscribed to account updates for {self.address}")

            async for message in self.client:
                if not self._running:
                    break

                if message.get("type") == "transaction" and message.get("validated", False):
                    # Call the callback with the transaction data
                    try:
                        self.callback(message)
                    except Exception as e:
                        logger.error(f"Error in subscription callback: {e}")

        except Exception as e:
            logger.error(f"Subscription error: {e}")
            raise ConnectionError(f"Subscription failed: {e}") from e

    def stop(self):
        """Stop the subscription."""
        self._running = False


@wrap_xrpl_exception
def subscribe_account(client: JsonRpcClient, address: str, callback: Callable) -> AccountSubscription:
    """
    Set up WebSocket subscription for account updates.

    Args:
        client: XRPL client (used to get network URL)
        address: Account address to monitor
        callback: Function to call when account updates are received

    Returns:
        AccountSubscription object that can be started/stopped

    Raises:
        ConnectionError: If WebSocket connection fails
    """
    try:
        # Create WebSocket client using the same URL as the JSON-RPC client
        ws_url = client.url.replace('https://', 'wss://').replace('http://', 'ws://')
        if ws_url.endswith('/'):
            ws_url = ws_url[:-1]

        ws_client = AsyncWebsocketClient(ws_url)
        subscription = AccountSubscription(ws_client, address, callback)

        logger.info(f"Created subscription for account {address}")
        return subscription

    except Exception as e:
        logger.error(f"Failed to create subscription: {e}")
        raise ConnectionError(f"Failed to create subscription: {e}") from e