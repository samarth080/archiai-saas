"""MUST-cluster contraction (Phase 4 Stage 3).

Connected components over MUST-adjacency edges become clusters (super-nodes):
the slicing tree then places clusters relative to each other, and recurses into
each cluster's inner subgraph. Because a cluster's members are MUST-connected,
the inner guillotine keeps them mutually wall-sharing. Non-MUST edges between
members of different clusters are contracted to cluster-level edges.

Deterministic: union-find and grouping iterate sorted ids; cluster ids are
`cluster:<smallest member id>`.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.services.planning.graph_layout import _RELATION_RANK, PreparedGraph, PreparedNode
from app.services.planning.slicing_tree import Item, SliceEdge

# Lower = shallower band (placed nearer the front). Used to break zone-majority ties.
_ZONE_PRIORITY = {"public": 0, "semi_private": 1, "circulation": 2, "service": 3, "private": 4, "other": 5}


@dataclass(frozen=True)
class Cluster:
    id: str
    members: tuple[PreparedNode, ...]
    inner_edges: tuple[SliceEdge, ...]
    zone: str

    def item(self) -> Item:
        return Item(
            id=self.id,
            area=sum(m.area for m in self.members),
            min_w=max(m.min_w for m in self.members),
            min_d=max(m.min_d for m in self.members),
            needs_external=any(m.needs_external for m in self.members),
        )


@dataclass(frozen=True)
class ClusterGraph:
    clusters: tuple[Cluster, ...]
    edges: tuple[SliceEdge, ...]  # inter-cluster, contracted

    def cluster(self, cluster_id: str) -> Cluster | None:
        return next((c for c in self.clusters if c.id == cluster_id), None)


def _majority_zone(zones: list[str]) -> str:
    counts: dict[str, int] = {}
    for z in zones:
        counts[z] = counts.get(z, 0) + 1
    # highest count, tie → shallowest (lowest priority number)
    return min(counts, key=lambda z: (-counts[z], _ZONE_PRIORITY.get(z, 5)))


def contract(prepared: PreparedGraph) -> ClusterGraph:
    ids = sorted(n.id for n in prepared.nodes)
    by_id = {n.id: n for n in prepared.nodes}
    parent = {i: i for i in ids}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str):
        ra, rb = find(a), find(b)
        if ra != rb:
            lo, hi = sorted((ra, rb))
            parent[hi] = lo  # attach to the smaller id — deterministic

    for edge in prepared.edges:
        if edge.relation == "must" and edge.a in parent and edge.b in parent:
            union(edge.a, edge.b)

    groups: dict[str, list[str]] = {}
    for i in ids:
        groups.setdefault(find(i), []).append(i)

    clusters: list[Cluster] = []
    id_to_cluster: dict[str, str] = {}
    for root in sorted(groups):
        member_ids = sorted(groups[root])
        member_set = set(member_ids)
        cid = f"cluster:{member_ids[0]}"
        members = tuple(by_id[i] for i in member_ids)
        inner = tuple(
            e for e in prepared.edges
            if e.a in member_set and e.b in member_set
        )
        clusters.append(Cluster(cid, members, inner, _majority_zone([m.zone for m in members])))
        for i in member_ids:
            id_to_cluster[i] = cid

    inter: dict[tuple[str, str], tuple[int, str, str]] = {}
    for edge in prepared.edges:
        ca, cb = id_to_cluster.get(edge.a), id_to_cluster.get(edge.b)
        if ca is None or cb is None or ca == cb:
            continue
        key = (ca, cb) if ca < cb else (cb, ca)
        rank = _RELATION_RANK.get(edge.relation, 0)
        if key not in inter or rank > inter[key][0]:
            inter[key] = (rank, edge.relation, edge.rel_pos)

    edges = tuple(
        SliceEdge(a=key[0], b=key[1], relation=val[1], rel_pos=val[2])
        for key, val in sorted(inter.items())
    )
    return ClusterGraph(tuple(clusters), edges)
