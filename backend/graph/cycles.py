from __future__ import annotations

from collections import deque
from typing import Dict, List, Optional

from .types import Edge


def detect_cycle(edges: list[Edge], new_edge: Edge) -> list[str] | None:
    """
    Detect whether adding `new_edge` closes a directed cycle.
    Returns the closed path (start repeated at end) or None.
    """
    adjacency: Dict[str, List[str]] = {}
    for edge in edges:
        adjacency.setdefault(edge.debtor, []).append(edge.creditor)

    start = new_edge.creditor
    target = new_edge.debtor
    if start == target:
        return [start, start]

    queue: deque[str] = deque([start])
    parents: Dict[str, Optional[str]] = {start: None}

    while queue:
        node = queue.popleft()
        if node == target:
            break
        for neighbor in adjacency.get(node, []):
            if neighbor in parents:
                continue
            parents[neighbor] = node
            queue.append(neighbor)

    if target not in parents:
        return None

    path: list[str] = []
    cursor: Optional[str] = target
    while cursor is not None:
        path.append(cursor)
        cursor = parents[cursor]
    path.reverse()
    path.append(start)
    return path
