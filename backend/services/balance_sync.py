"""Balance synchronization service for MPT tokens."""

import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..xrpl_client.client import JsonRpcClient
from ..xrpl_client.mpt import get_mpt_balance, mint_to_holder, burn_from_holder
from ..xrpl_client.exceptions import XRPLClientError
from xrpl.wallet import Wallet

logger = logging.getLogger(__name__)


@dataclass
class BalanceDelta:
    """Represents a balance change needed for synchronization."""
    address: str
    current_balance: float
    target_balance: float
    delta: float

    @property
    def needs_mint(self) -> bool:
        """True if this delta requires minting tokens."""
        return self.delta > 0

    @property
    def needs_burn(self) -> bool:
        """True if this delta requires burning tokens."""
        return self.delta < 0

    @property
    def amount(self) -> float:
        """Absolute amount to mint or burn."""
        return abs(self.delta)


class BalanceCache:
    """Simple in-memory cache for balance data."""

    def __init__(self):
        self._cache: Dict[str, Dict[str, float]] = {}

    def get_cached_balances(self, group_id: str) -> Dict[str, float]:
        """Get cached net balances for a group."""
        return self._cache.get(group_id, {})

    def update_cache(self, group_id: str, balances: Dict[str, float]):
        """Update cached balances for a group."""
        self._cache[group_id] = balances.copy()

    def clear_cache(self, group_id: str = None):
        """Clear cache for specific group or all groups."""
        if group_id:
            self._cache.pop(group_id, None)
        else:
            self._cache.clear()


# Global cache instance
_balance_cache = BalanceCache()


def get_cached_nets(group_id: str) -> Dict[str, float]:
    """
    Get cached net balances for a group.

    In a real implementation, this would read from a persistent cache
    (Redis, database, etc.) that stores the computed net balances
    from transaction history.

    Args:
        group_id: Group identifier

    Returns:
        Dictionary mapping addresses to their net balances
    """
    # For now, use in-memory cache
    # In production, this would query your persistent cache
    cached_balances = _balance_cache.get_cached_balances(group_id)

    logger.debug(f"Retrieved cached nets for group {group_id}: {cached_balances}")
    return cached_balances


def compute_deltas(current_balances: Dict[str, float], target_balances: Dict[str, float]) -> List[BalanceDelta]:
    """
    Compute balance deltas between current and target states.

    Args:
        current_balances: Current MPT balances on XRPL
        target_balances: Target balances from cached nets

    Returns:
        List of BalanceDelta objects representing needed changes
    """
    deltas = []

    # Get all addresses that appear in either current or target
    all_addresses = set(current_balances.keys()) | set(target_balances.keys())

    for address in all_addresses:
        current = current_balances.get(address, 0.0)
        target = target_balances.get(address, 0.0)
        delta = target - current

        # Only include significant deltas (avoid tiny floating point differences)
        if abs(delta) > 0.000001:  # 1 millionth threshold
            deltas.append(BalanceDelta(
                address=address,
                current_balance=current,
                target_balance=target,
                delta=delta
            ))

    return deltas


def batch_execute_operations(
    client: JsonRpcClient,
    issuer_wallet: Wallet,
    issuance_id: str,
    deltas: List[BalanceDelta],
    max_workers: int = 5
) -> List[Tuple[BalanceDelta, str, bool]]:
    """
    Execute mint/burn operations in parallel batches.

    Args:
        client: XRPL client
        issuer_wallet: Token issuer wallet
        issuance_id: MPT issuance ID
        deltas: List of balance changes to execute
        max_workers: Maximum number of parallel operations

    Returns:
        List of tuples: (delta, tx_hash_or_error, success)
    """
    results = []

    def execute_operation(delta: BalanceDelta) -> Tuple[BalanceDelta, str, bool]:
        """Execute a single mint or burn operation."""
        try:
            if delta.needs_mint:
                tx_hash = mint_to_holder(client, issuer_wallet, delta.address, delta.amount, issuance_id)
                logger.info(f"Minted {delta.amount} to {delta.address}: {tx_hash}")
                return (delta, tx_hash, True)
            elif delta.needs_burn:
                tx_hash = burn_from_holder(client, issuer_wallet, delta.address, delta.amount, issuance_id)
                logger.info(f"Burned {delta.amount} from {delta.address}: {tx_hash}")
                return (delta, tx_hash, True)
            else:
                return (delta, "No operation needed", True)
        except Exception as e:
            logger.error(f"Operation failed for {delta.address}: {e}")
            return (delta, str(e), False)

    # Execute operations in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all operations
        future_to_delta = {executor.submit(execute_operation, delta): delta for delta in deltas}

        # Collect results as they complete
        for future in as_completed(future_to_delta):
            result = future.result()
            results.append(result)

    return results


def sync_balances(
    group_id: str,
    client: JsonRpcClient,
    issuer_wallet: Wallet,
    issuance_id: str,
    holder_addresses: List[str]
) -> Dict[str, float]:
    """
    Synchronize MPT balances with cached net balances.

    This function:
    1. Reads cached net balances for the group
    2. Queries current MPT balances from XRPL
    3. Computes deltas between cached and actual balances
    4. Executes batch mint/burn operations to synchronize
    5. Returns the final synchronized balances

    Args:
        group_id: Group identifier for cached balances
        client: Connected XRPL client
        issuer_wallet: Wallet of the MPT issuer
        issuance_id: MPT issuance ID to synchronize
        holder_addresses: List of addresses to check/sync

    Returns:
        Dictionary of final synchronized balances

    Raises:
        XRPLClientError: If synchronization operations fail
    """
    try:
        logger.info(f"Starting balance sync for group {group_id}")

        # 1. Read cached net balances
        target_balances = get_cached_nets(group_id)
        logger.debug(f"Target balances: {target_balances}")

        # 2. Query current MPT balances from XRPL
        current_balances = {}

        # Query balances in parallel for better performance
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_address = {
                executor.submit(get_mpt_balance, client, address, issuance_id): address
                for address in holder_addresses
            }

            for future in as_completed(future_to_address):
                address = future_to_address[future]
                try:
                    balance = future.result()
                    current_balances[address] = balance
                except Exception as e:
                    logger.error(f"Failed to get balance for {address}: {e}")
                    current_balances[address] = 0.0

        logger.debug(f"Current balances: {current_balances}")

        # 3. Compute deltas
        deltas = compute_deltas(current_balances, target_balances)
        logger.info(f"Computed {len(deltas)} balance deltas")

        if not deltas:
            logger.info("No balance changes needed")
            return current_balances

        # 4. Execute batch mint/burn operations
        operation_results = batch_execute_operations(client, issuer_wallet, issuance_id, deltas)

        # 5. Check results and compute final balances
        successful_operations = 0
        failed_operations = 0
        final_balances = current_balances.copy()

        for delta, result, success in operation_results:
            if success:
                successful_operations += 1
                # Update final balance with the expected change
                final_balances[delta.address] = delta.target_balance
            else:
                failed_operations += 1
                logger.error(f"Failed to sync balance for {delta.address}: {result}")

        logger.info(f"Balance sync completed: {successful_operations} successful, {failed_operations} failed")

        # Update cache with new balances
        _balance_cache.update_cache(group_id, final_balances)

        if failed_operations > 0:
            raise XRPLClientError(f"Some balance sync operations failed: {failed_operations}/{len(deltas)}")

        return final_balances

    except Exception as e:
        logger.error(f"Balance sync failed for group {group_id}: {e}")
        raise


def set_cached_nets(group_id: str, balances: Dict[str, float]):
    """
    Set cached net balances for a group (utility function for testing).

    Args:
        group_id: Group identifier
        balances: Net balances to cache
    """
    _balance_cache.update_cache(group_id, balances)
    logger.debug(f"Set cached nets for group {group_id}: {balances}")


def clear_cache(group_id: str = None):
    """
    Clear balance cache for specific group or all groups.

    Args:
        group_id: Group to clear, or None to clear all
    """
    _balance_cache.clear_cache(group_id)
    logger.debug(f"Cleared cache for group: {group_id or 'all'}")