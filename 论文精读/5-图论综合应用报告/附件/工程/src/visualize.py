# -*- coding: utf-8 -*-
"""
生成报告插图（对应 PDF 建议的「三张核心图」+ 实验分析图）。

图 1  校园道路网络图论抽象模型     -> fig1_road_network.png
图 2  配送点最短距离矩阵热力图     -> fig2_distance_matrix.png
图 3  不同配送路径规划算法对比     -> fig3_algorithm_comparison.png
图 4  最优配送路线 vs 人工路线对比 -> fig4_route_comparison.png
图 5  道路封闭对最优总路程的影响   -> fig5_closure_impact.png

图题统一放在图下方（正文 Markdown 的 '**图 N　...**' 题注），
因此这里不再在图内绘制标题，避免与题注重复。
"""
from __future__ import annotations
import csv
import json
import os
from typing import List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import font_manager

from graph_core import WeightedGraph
from tsp_core import tour_length, nearest_neighbor, two_opt, held_karp, random_tour
from data_io import build_graph, load_nodes, load_edges, delivery_points

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGS = os.path.join(BASE, "figs")
OUT = os.path.join(BASE, "out")

# ---------------- 中文字体 ----------------
_CANDIDATES = ["PingFang SC", "Heiti SC", "Hiragino Sans GB",
               "Songti SC", "STHeiti", "Arial Unicode MS", "Noto Sans CJK SC"]
_Avail = {f.name for f in font_manager.fontManager.ttflist}
_CN = next((c for c in _CANDIDATES if c in _Avail), None)
if _CN:
    plt.rcParams["font.sans-serif"] = [_CN]
plt.rcParams["axes.unicode_minus"] = False

C_STATION = "#C0392B"
C_DELIV = "#E67E22"
C_JUNC = "#2C3E50"
C_EDGE = "#95A5A6"
C_OPT = "#16A085"
C_MAN = "#8E44AD"
C_DROP = "#3498DB"

plt.rcParams.update({
    "figure.dpi": 160, "savefig.dpi": 160, "font.size": 10,
    "axes.edgecolor": "#BDC3C7", "axes.labelcolor": "#2C3E50",
    "text.color": "#2C3E50", "xtick.color": "#566573", "ytick.color": "#566573",
})


def _load_csv(name: str) -> List[dict]:
    with open(os.path.join(OUT, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _edge_id_map(edges):
    m = {}
    for e in edges:
        m[frozenset((e["source"], e["target"]))] = e["eid"]
    return m


# =============================================================== 图 1
def fig1_road_network(g, nodes, edges, path=None):
    path = path or os.path.join(FIGS, "fig1_road_network.png")
    fig, ax = plt.subplots(figsize=(11, 8.2))
    # 边
    for u, v, w in g.edges():
        x1, y1 = g.nodes[u]["x"], g.nodes[u]["y"]
        x2, y2 = g.nodes[v]["x"], g.nodes[v]["y"]
        ax.plot([x1, x2], [y1, y2], color=C_EDGE, lw=2.0, zorder=1,
                solid_capstyle="round")
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my, f"{w:.0f}", fontsize=6.5, color="#7F8C8D",
                ha="center", va="center", zorder=2,
                bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none", alpha=0.9))

    # 节点
    for nid, a in g.nodes.items():
        t = a["type"]
        if t == "station":
            ax.scatter(a["x"], a["y"], s=300, marker="*", c=C_STATION,
                       edgecolors="white", linewidths=1.4, zorder=6)
            ax.text(a["x"], a["y"] - 52, nid, fontsize=9, fontweight="bold",
                    color=C_STATION, ha="center",
                    bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none", alpha=0.85))
        elif t == "delivery":
            ax.scatter(a["x"], a["y"], s=135, marker="o", c=C_DELIV,
                       edgecolors="white", linewidths=1.2, zorder=6)
            ax.text(a["x"], a["y"] - 52, nid, fontsize=9, fontweight="bold",
                    color=C_DELIV, ha="center",
                    bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none", alpha=0.85))
        else:
            ax.scatter(a["x"], a["y"], s=55, marker="o", c=C_JUNC,
                       edgecolors="white", linewidths=1.0, zorder=5)
            ax.text(a["x"], a["y"] + 26, nid, fontsize=7.5, color=C_JUNC, ha="center")

    # 配送点中文名：逐点指定偏移，避免北部标签互相重叠
    NAME_OFF = {
        "S00": (-118, -26, "right"),
        "D01": (40, 26, "left"),
        "D02": (-108, 30, "right"),
        "D03": (12, 40, "center"),
        "D04": (44, -30, "left"),
        "D05": (46, 18, "left"),
        "D06": (46, 8, "left"),
    }
    for nid, a in g.nodes.items():
        if a["type"] in ("station", "delivery"):
            dx, dy, ha = NAME_OFF.get(nid, (42, -6, "left"))
            ax.annotate(a["name"], (a["x"], a["y"]),
                        xytext=(dx, dy), textcoords="offset points",
                        fontsize=9.5, color="#2C3E50", ha=ha,
                        arrowprops=dict(arrowstyle="-", color="#BDC3C7", lw=0.9))

    ax.set_xlabel("局部平面坐标 X / 米"); ax.set_ylabel("局部平面坐标 Y / 米")
    ax.set_aspect("equal"); ax.grid(True, ls=":", alpha=0.35)
    ax.set_xlim(20, 1130); ax.set_ylim(40, 1060)
    handles = [mpatches.Patch(color=C_EDGE, label="道路边（长度=权重）"),
               plt.Line2D([], [], marker="*", ls="", ms=15, color=C_STATION, label="S00 快递服务站"),
               plt.Line2D([], [], marker="o", ls="", ms=9, color=C_DELIV, label="D01–D06 宿舍配送点"),
               plt.Line2D([], [], marker="o", ls="", ms=6, color=C_JUNC, label="J01–J16 道路节点")]
    ax.legend(handles=handles, loc="lower left", fontsize=9, framealpha=0.95)
    fig.tight_layout(); fig.savefig(path, bbox_inches="tight"); plt.close(fig)
    return path


# =============================================================== 图 2
def fig2_distance_matrix(P, D, path=None):
    path = path or os.path.join(FIGS, "fig2_distance_matrix.png")
    import numpy as np
    M = np.array(D)
    fig, ax = plt.subplots(figsize=(8.4, 7.2))
    im = ax.imshow(M, cmap="YlOrRd")
    ax.set_xticks(range(len(P))); ax.set_yticks(range(len(P)))
    ax.set_xticklabels(P); ax.set_yticklabels(P)
    for i in range(len(P)):
        for j in range(len(P)):
            v = M[i, j]
            ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=8.5,
                    color="white" if v > M.max() * 0.55 else "#2C3E50")
    ax.set_xlabel("起点"); ax.set_ylabel("终点")
    for lb in ax.get_xticklabels(): lb.set_fontweight("bold")
    for lb in ax.get_yticklabels(): lb.set_fontweight("bold")
    cb = fig.colorbar(im, ax=ax, shrink=0.86)
    cb.set_label("最短距离 (m)")
    fig.tight_layout(); fig.savefig(path, bbox_inches="tight"); plt.close(fig)
    return path


# =============================================================== 图 3
def fig4_route_comparison(g, P, D, path=None):
    path = path or os.path.join(FIGS, "fig4_route_comparison.png")
    nn = nearest_neighbor(D, 0)
    opt_order, opt_len, _ = two_opt(nn, D)
    hk_len, hk_order = held_karp(D)
    if hk_len is not None and hk_len <= opt_len:
        opt_order, opt_len = hk_order, hk_len
    manual = [0] + list(range(1, len(P)))
    manual_len = tour_length(manual, D)

    fig, ax = plt.subplots(figsize=(11, 8.2))
    for u, v, w in g.edges():
        x1, y1 = g.nodes[u]["x"], g.nodes[u]["y"]
        x2, y2 = g.nodes[v]["x"], g.nodes[v]["y"]
        ax.plot([x1, x2], [y1, y2], color="#D5DBDB", lw=1.7, zorder=1)

    def draw(order, color, lw, alpha, label):
        seq = order + [order[0]]
        first = True
        for a, b in zip(seq, seq[1:]):
            _, p = g.shortest_path(P[a], P[b])
            xs = [g.nodes[n]["x"] for n in p]; ys = [g.nodes[n]["y"] for n in p]
            ax.plot(xs, ys, color=color, lw=lw, alpha=alpha, zorder=4,
                    solid_capstyle="round", solid_joinstyle="round",
                    label=label if first else None)
            first = False
        for i in order:
            ax.scatter(g.nodes[P[i]]["x"], g.nodes[P[i]]["y"], s=190,
                       c=color, edgecolors="white", linewidths=1.6, zorder=6)

    draw(manual, C_MAN, 2.6, 0.55, f"人工顺时针顺序  {manual_len:.0f} m")
    draw(opt_order, C_OPT, 3.6, 0.95, f"最优配送路线  {opt_len:.0f} m")

    for nid, a in g.nodes.items():
        if a["type"] == "station":
            ax.scatter(a["x"], a["y"], s=330, marker="*", c=C_STATION,
                       edgecolors="white", linewidths=1.5, zorder=7)
        elif a["type"] == "delivery":
            ax.scatter(a["x"], a["y"], s=95, marker="o", c="#7F8C8D",
                       edgecolors="white", linewidths=1.0, zorder=3)
        else:
            ax.scatter(a["x"], a["y"], s=42, marker="o", c=C_JUNC,
                       edgecolors="white", linewidths=0.9, zorder=5)

    ROUTE_OFF = {0: (34, -42, "left"), 1: (-38, 30, "right"), 2: (0, 46, "center"),
                 3: (4, 46, "center"), 4: (52, -36, "left"), 5: (58, 26, "left"),
                 6: (58, 4, "left")}
    for i in opt_order:
        nid = P[i]
        dx, dy, ha = ROUTE_OFF.get(i, (46, 16, "left"))
        ax.annotate(f"{i}. {g.nodes[nid]['name']}", (g.nodes[nid]["x"], g.nodes[nid]["y"]),
                    xytext=(dx, dy), textcoords="offset points", fontsize=9.5,
                    fontweight="bold", color=C_OPT, ha=ha,
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.92),
                    arrowprops=dict(arrowstyle="-", color=C_OPT, lw=1.0))

    ax.set_xlabel("局部平面坐标 X / 米"); ax.set_ylabel("局部平面坐标 Y / 米")
    ax.set_aspect("equal"); ax.grid(True, ls=":", alpha=0.3)
    ax.set_xlim(20, 1130); ax.set_ylim(40, 1060)
    ax.legend(loc="lower left", fontsize=10, framealpha=0.95)
    fig.tight_layout(); fig.savefig(path, bbox_inches="tight"); plt.close(fig)
    return path


# =============================================================== 图 4
def fig3_algorithm_comparison(path=None):
    path = path or os.path.join(FIGS, "fig3_algorithm_comparison.png")
    rows = _load_csv("E2_algorithm_comparison.csv")
    names = [r["algorithm"] for r in rows]
    vals = [float(r["length_m"]) for r in rows]
    colors = [C_MAN, C_MAN, C_DROP, C_DROP, "#16A085", C_OPT]
    fig, ax = plt.subplots(figsize=(10, 5.6))
    bars = ax.bar(range(len(names)), vals, color=colors, edgecolor="white", width=0.62)
    base = min(vals)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 60, f"{v:.0f}\n(+{(v-base)/base*100:.1f}%)",
                ha="center", fontsize=9.5, fontweight="bold")
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels([n.replace("(", "\n(").replace(")", ")") for n in names], fontsize=9)
    ax.set_ylabel("闭合巡回总路程 (m)")
    ax.grid(axis="y", ls=":", alpha=0.4); ax.set_ylim(0, max(vals) * 1.22)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig(path, bbox_inches="tight"); plt.close(fig)
    return path


# =============================================================== 图 5
def fig5_closure_impact(path=None):
    path = path or os.path.join(FIGS, "fig5_closure_impact.png")
    rows = [r for r in _load_csv("E5_closure.csv") if r["feasible"] == "yes"]
    rows.sort(key=lambda r: -float(r["delta_pct"]))
    names = [r["closed_edge"] for r in rows]
    vals = [float(r["delta_pct"]) for r in rows]
    colors = [C_STATION if v >= 40 else (C_DELIV if v >= 15 else C_DROP) for v in vals]
    fig, ax = plt.subplots(figsize=(10.5, 5.6))
    bars = ax.bar(range(len(names)), vals, color=colors, edgecolor="white", width=0.66)
    for b, v, r in zip(bars, vals, rows):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.2,
                f"+{v:.1f}%\n(+{float(r['delta_m']):.0f} m)", ha="center", fontsize=8.6)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, fontsize=9.5, rotation=30, ha="right")
    ax.set_ylabel("最优总路程增加比例 (%)")
    ax.grid(axis="y", ls=":", alpha=0.4); ax.set_ylim(0, max(vals) * 1.28)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig(path, bbox_inches="tight"); plt.close(fig)
    return path


def run_all():
    os.makedirs(FIGS, exist_ok=True)
    g, edges = build_graph()
    nodes = load_nodes()
    P = delivery_points(nodes)
    D = g.distance_matrix(P)
    out = [
        fig1_road_network(g, nodes, edges),
        fig2_distance_matrix(P, D),
        fig3_algorithm_comparison(),
        fig4_route_comparison(g, P, D),
        fig5_closure_impact(),
    ]
    return out


if __name__ == "__main__":
    for p in run_all():
        print("[fig]", p)
