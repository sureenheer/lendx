from __future__ import annotations

from collections import defaultdict

from .types import Edge


def compute_nets(edges: list[Edge]) -> dict[str, float]:
    """
    Computes net positions: positive => owes overall, negative => is owed overall.
    """
    balances = defaultdict(float)
    for edge in edges:
        balances[edge.debtor] += edge.amount
        balances[edge.creditor] -= edge.amount
    return dict(balances)
