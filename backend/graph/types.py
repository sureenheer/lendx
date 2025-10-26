from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Edge:
    debtor: str
    creditor: str
    amount: float


@dataclass(slots=True)
class Graph:
    group_id: str
    edges: list[Edge] = field(default_factory=list)
    updated_at: float = 0.0
