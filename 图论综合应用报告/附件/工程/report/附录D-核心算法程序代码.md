# 附录 D  核心算法程序代码

工程目录：`graph-theory-campus-delivery/`，共 6 个核心模块。

## D.1 Dijkstra 单源最短路（`src/graph_core.py`）

```python
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

```

## D.2 配送点距离矩阵（`src/graph_core.py`）

```python
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
```

## D.3 最近邻 + 2-opt（`src/tsp_core.py`）

```python
def nearest_neighbor(D: List[List[float]], start: int = 0) -> List[int]:
    """最近邻算法：每次走向最近的未访问配送点。

    复杂度 O(n^2)。构造的是一条哈密尔顿回路（每个点恰好进出一次）。
    """
    n = len(D)
    unvisited = set(range(1, n))
    order = [start]
    cur = start
    while unvisited:
        nxt = min(unvisited, key=lambda v: (D[cur][v], v))
        order.append(nxt)
        unvisited.remove(nxt)
        cur = nxt
    return order


# ---------------- 启发式 2：2-opt 局部搜索 ----------------
def two_opt(order: List[int], D: List[List[float]], max_iter: int = 20000) -> Tuple[List[int], float, int]:
    """2-opt 局部搜索（best improvement）。

    操作：取路线上两条边 (a,b) 与 (c,d)，把它们替换为 (a,c) 与 (b,d)。
    等价于把子路径 b..c 反转。若总长度下降则接受。
    返回 (最优访问顺序, 总长度, 迭代次数)。
    """
    order = list(order)
    n = len(order)
    best = tour_length(order, D)
    iters = 0
    improved = True
    while improved and iters < max_iter:
        improved = False
        best_delta = -1e-12
        best_move = None
        for i in range(n - 1):
            a, b = order[i], order[i + 1]
            for j in range(i + 2, n):
                if i == 0 and j == n - 1:
                    continue
                c, d = order[j], order[(j + 1) % n]
                delta = (D[a][c] + D[b][d]) - (D[a][b] + D[c][d])
                if delta < best_delta:
                    best_delta = delta
                    best_move = (i, j)
        if best_move is not None:
            i, j = best_move
            order[i + 1:j + 1] = order[i + 1:j + 1][::-1]
            improved = True
            iters += 1
    return order, tour_length(order, D), iters

```

## D.4 Held–Karp 精确动态规划（`src/tsp_core.py`）

```python
def held_karp(D: List[List[float]], max_n: int = 16) -> Tuple[Optional[float], Optional[List[int]]]:
    """Held-Karp 精确求解闭合 TSP（起点固定为 0）。

    状态 dp[mask][j] = 从 0 出发、恰好访问 mask 中的配送点、最后停在 j 的最小代价。
    时间复杂度 O(2^n * n^2)，空间 O(2^n * n)。n 过大时返回 None。
    """
    n = len(D)
    if n > max_n:
        return None, None
    k = n - 1  # 需要访问的配送点数（不含起点 0）
    if k == 0:
        return 0.0, [0]
    INFV = INF
    size = 1 << k
    dp = [[INFV] * n for _ in range(size)]
    parent = [[-1] * n for _ in range(size)]
    for j in range(1, n):
        dp[1 << (j - 1)][j] = D[0][j]
        parent[1 << (j - 1)][j] = 0  # 基状态的前驱为起点 0
    for mask in range(size):
        row = dp[mask]
        for j in range(1, n):
            if row[j] == INFV:
                continue
            base = row[j]
            for i in range(1, n):
                if i == j or (mask >> (i - 1)) & 1:
                    continue
                nm = mask | (1 << (i - 1))
                cand = base + D[j][i]
                if cand < dp[nm][i]:
                    dp[nm][i] = cand
                    parent[nm][i] = j
    full = size - 1
    best_len, best_end = INFV, -1
    for j in range(1, n):
        if dp[full][j] == INFV:
            continue
        tot = dp[full][j] + D[j][0]
        if tot < best_len:
            best_len, best_end = tot, j
    if best_end < 0:
        return None, None
    # 回溯
    chain: List[int] = []
    mask, cur = full, best_end
    while cur != 0:
        chain.append(cur)
        p = parent[mask][cur]
        mask ^= 1 << (cur - 1)
        cur = p
    chain.reverse()
    return best_len, [0] + chain

```

## D.5 暴力枚举校验（`src/tsp_core.py`）

```python
def brute_force(D: List[List[float]], start: int = 0) -> Tuple[float, List[int]]:
    """枚举所有排列求精确最优（仅用于 n<=8 校验 Held-Karp）。"""
    import itertools
    n = len(D)
    best, best_p = INF, None
    for perm in itertools.permutations(range(1, n)):
        order = [start] + list(perm)
        L = tour_length(order, D)
        if L < best:
            best, best_p = L, order
    return best, best_p


```

---

