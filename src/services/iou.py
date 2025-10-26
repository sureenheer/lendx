from __future__ import annotations

import logging
import time
from typing import Dict

from src.graph.cycles import detect_cycle
from src.graph.nets import compute_nets
from src.graph.reduce import reduce_cycle
from src.graph.types import Edge, Graph

logger = logging.getLogger(__name__)

_graphs: Dict[str, Graph] = {}
_nets_cache: Dict[str, Dict[str, float]] = {}


def add_iou(group_id: str, debtor: str, creditor: str, amount: float) -> dict[str, float]:
    """
    Add an IOU edge, run cycle reduction, and return updated net balances.
    """
    if amount <= 0:
        raise ValueError("amount must be positive")
    if debtor == creditor:
        raise ValueError("debtor and creditor must be different users")

    graph = _graphs.setdefault(group_id, Graph(group_id=group_id))
    new_edge = Edge(debtor=debtor, creditor=creditor, amount=amount)

    logger.debug("Adding IOU edge %s -> %s (%s) for group %s", debtor, creditor, amount, group_id)

    updated_edges = graph.edges + [new_edge]
    cycle_path = detect_cycle(graph.edges, new_edge)
    if cycle_path:
        logger.debug("Cycle detected for group %s: %s", group_id, " -> ".join(cycle_path))
        updated_edges = reduce_cycle(updated_edges, cycle_path)

    graph.edges = updated_edges
    graph.updated_at = time.time()

    nets = compute_nets(graph.edges)
    _nets_cache[group_id] = nets
    _trigger_balance_sync(group_id, nets)

    return nets.copy()


def get_group_balances(group_id: str) -> dict[str, float]:
    """
    Return cached net balances for a group and verify them against on-chain data.
    """
    graph = _graphs.get(group_id)
    if not graph:
        return {}

    if group_id not in _nets_cache:
        _nets_cache[group_id] = compute_nets(graph.edges)

    nets = _nets_cache[group_id].copy()
    _verify_onchain_balances(group_id, nets)
    return nets


def _trigger_balance_sync(group_id: str, nets: dict[str, float]) -> None:
    """
    Placeholder hook for syncing updated balances with persistent storage or XRPL.
    """
    logger.debug("Triggering balance sync for group %s: %s", group_id, nets)
    # TODO: integrate with persistence layer / XRPL publisher.


def _verify_onchain_balances(group_id: str, nets: dict[str, float]) -> None:
    """
    Placeholder verification step to compare cached nets against on-chain MPT balances.
    """
    try:
        # TODO: Fetch real MPT balances and compare once plumbing is available.
        logger.debug("Verified group %s nets against on-chain snapshot (stub).", group_id)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning("On-chain verification failed for group %s: %s", group_id, exc)
