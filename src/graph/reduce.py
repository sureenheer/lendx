from __future__ import annotations

from dataclasses import replace
from typing import Dict, List, Tuple

from .types import Edge

EPSILON = 1e-9


def reduce_cycle(edges: list[Edge], cycle_path: list[str]) -> list[Edge]:
    """
    Reduce debts along a cycle by the smallest edge amount in that cycle.
    """
    if len(cycle_path) < 2 or cycle_path[0] != cycle_path[-1]:
        raise ValueError("cycle_path must describe a closed loop.")

    cycle_pairs = list(zip(cycle_path, cycle_path[1:]))
    if not cycle_pairs:
        return edges[:]

    edge_lookup: Dict[Tuple[str, str], List[int]] = {}
    for idx, edge in enumerate(edges):
        edge_lookup.setdefault((edge.debtor, edge.creditor), []).append(idx)

    cycle_indices: list[int] = []
    cycle_amounts: list[float] = []
    for pair in cycle_pairs:
        indices = edge_lookup.get(pair)
        if not indices:
            raise ValueError(f"Missing edge for debtor={pair[0]} creditor={pair[1]}")
        idx = indices.pop(0)
        cycle_indices.append(idx)
        cycle_amounts.append(edges[idx].amount)

    min_amount = min(cycle_amounts, default=0.0)
    if min_amount <= 0:
        return edges[:]

    result: list[Edge] = []
    cycle_index_set = set(cycle_indices)
    for idx, edge in enumerate(edges):
        if idx not in cycle_index_set:
            result.append(edge)
            continue

        new_amount = edge.amount - min_amount
        if new_amount > EPSILON:
            result.append(replace(edge, amount=new_amount))

    return result
