"""
TSP 求解模块：最近邻 / 2-opt / Held-Karp 精确 DP / 暴力枚举（校验用）
对应《图论》课程第 6.2 节「哈密尔顿图与旅行商问题」。
配送点编号约定：0 号为快递站（巡回起点），1..n-1 为宿舍配送点。
"""
from __future__ import annotations
import math
import random
from typing import List, Optional, Tuple

INF = float("inf")


# ---------------- 目标函数 ----------------
def tour_length(order: List[int], D: List[List[float]]) -> float:
    """闭合巡回路线总长度：order 给出访问顺序，最后回到 order[0]。"""
    total = 0.0
    for i in range(len(order)):
        total += D[order[i]][order[(i + 1) % len(order)]]
    return total


# ---------------- 启发式 1：最近邻 ----------------
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


def polish(order: List[int], D: List[List[float]]) -> Tuple[List[int], float]:
    """2-opt 迭代到不动点。"""
    o, L, _ = two_opt(order, D)
    return o, L


# ---------------- 精确解：Held-Karp 动态规划 ----------------
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


# ---------------- 校验：暴力枚举 ----------------
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


# ---------------- 随机基准 ----------------
def random_tour(D: List[List[float]], rng: random.Random, start: int = 0) -> List[int]:
    n = len(D)
    rest = list(range(1, n))
    rng.shuffle(rest)
    return [start] + rest


def gap(heur: float, opt: float) -> float:
    """最优性差距 Gap = (L_alg - L_opt) / L_opt * 100%"""
    if opt is None or opt == 0 or opt == INF:
        return float("nan")
    return (heur - opt) / opt * 100.0
