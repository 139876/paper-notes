"""
图论核心模块：加权无向图 + Dijkstra + Floyd-Warshall
对应《图论》课程第 4 章「最短路问题」。

说明：所有算法均为手写实现（不依赖 networkx 的求解器），
networkx 仅在 verify.py 中用于交叉验证，保证报告实验可信。
"""
from __future__ import annotations
import heapq
from collections import defaultdict
from typing import Dict, List, Tuple, Optional


class WeightedGraph:
    """加权无向图。节点属性含 name / type / (x, y) 便于绘图。"""

    def __init__(self) -> None:
        self.nodes: Dict[str, dict] = {}
        self.adj: Dict[str, Dict[str, float]] = defaultdict(dict)
        self._edge_count = 0

    # ---------- 建图 ----------
    def add_node(self, nid: str, **attrs) -> None:
        if nid not in self.nodes:
            self.nodes[nid] = {"id": nid, "name": attrs.pop("name", nid), "type": attrs.pop("type", "junction")}
            self.nodes[nid].update(attrs)
        else:
            self.nodes[nid].update(attrs)

    def add_edge(self, u: str, v: str, w: float) -> None:
        """添加无向边，权重取较小者（避免同一路段重复录入导致权值冲突）。"""
        self.add_node(u)
        self.add_node(v)
        if v in self.adj[u] and self.adj[u][v] <= w:
            return
        if u in self.adj[v] and self.adj[v][u] <= w:
            return
        self.adj[u][v] = w
        self.adj[v][u] = w
        self._edge_count += 1

    @property
    def n(self) -> int:
        return len(self.nodes)

    @property
    def m(self) -> int:
        return self._edge_count

    def edges(self) -> List[Tuple[str, str, float]]:
        out = []
        for u, nbrs in self.adj.items():
            for v, w in nbrs.items():
                if u < v:
                    out.append((u, v, w))
        return out

    # ---------- 第 4.2 节 Dijkstra ----------
    def dijkstra(self, src: str) -> Tuple[Dict[str, float], Dict[str, Optional[str]]]:
        """单源最短路。返回 (dist, prev)；prev 用于回溯路径。

        时间复杂度 O((n+m) log n)，空间 O(n+m)。
        """
        INF = float("inf")
        dist: Dict[str, float] = {v: INF for v in self.nodes}
        prev: Dict[str, Optional[str]] = {v: None for v in self.nodes}
        dist[src] = 0.0
        pq: List[Tuple[float, str]] = [(0.0, src)]
        visited = set()
        while pq:
            d, u = heapq.heappop(pq)
            if u in visited:
                continue
            visited.add(u)
            for v, w in self.adj[u].items():
                nd = d + w
                if nd < dist[v] - 1e-12:
                    dist[v] = nd
                    prev[v] = u
                    heapq.heappush(pq, (nd, v))
        return dist, prev

    def shortest_path(self, src: str, dst: str) -> Tuple[float, List[str]]:
        """两点间最短路长度与具体路径。"""
        dist, prev = self.dijkstra(src)
        if dist.get(dst, float("inf")) == float("inf"):
            return float("inf"), []
        path = [dst]
        cur = dst
        while prev[cur] is not None:
            cur = prev[cur]
            path.append(cur)
        path.reverse()
        return dist[dst], path

    # ---------- 第 4.3 节 Floyd-Warshall ----------
    def floyd(self) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Dict[str, Optional[str]]]]:
        """全源最短路。n 较小（<200）时用 Floyd 与 Dijkstra 互验。"""
        ids = list(self.nodes)
        INF = float("inf")
        D: Dict[str, Dict[str, float]] = {a: {b: INF for b in ids} for a in ids}
        Nxt: Dict[str, Dict[str, Optional[str]]] = {a: {b: None for b in ids} for a in ids}
        for a in ids:
            D[a][a] = 0.0
            for b, w in self.adj[a].items():
                if w < D[a][b]:
                    D[a][b] = w
                    Nxt[a][b] = b
        for k in ids:
            for i in ids:
                dik = D[i][k]
                if dik == INF:
                    continue
                for j in ids:
                    dkj = D[k][j]
                    if dkj == INF:
                        continue
                    if dik + dkj < D[i][j]:
                        D[i][j] = dik + dkj
                        Nxt[i][j] = Nxt[i][k]
        return D, Nxt

    # ---------- 配送点距离矩阵 ----------
    def distance_matrix(self, points: List[str]) -> List[List[float]]:
        """以配送点为节点生成 k x k 最短距离矩阵 D（k = len(points)）。

        D[i][j] = 沿校园道路网络从配送点 i 到 j 的最短步行距离，
        不是直线距离 —— 这是本报告建模的关键。
        """
        k = len(points)
        M = [[float("inf")] * k for _ in range(k)]
        for i, p in enumerate(points):
            dist, _ = self.dijkstra(p)
            for j, q in enumerate(points):
                M[i][j] = dist.get(q, float("inf"))
        return M
