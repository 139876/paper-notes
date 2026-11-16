# -*- coding: utf-8 -*-
"""
数据加载层：把 data/nodes.csv + data/edges.csv 读成图论模型对象。

对应报告第三章「校园道路网络的图论抽象」。
"""
from __future__ import annotations
import csv
import os
from typing import Dict, List, Tuple

from graph_core import WeightedGraph

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")

STATION = "S00"


def _read_csv(path: str) -> List[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_nodes(path: str = None) -> List[dict]:
    return _read_csv(path or os.path.join(DATA, "nodes.csv"))


def load_edges(path: str = None) -> List[dict]:
    return _read_csv(path or os.path.join(DATA, "edges.csv"))


def build_graph(nodes_path: str = None, edges_path: str = None,
                skip_edges: set = None) -> Tuple[WeightedGraph, List[dict]]:
    """构建校园道路加权无向图 G=(V,E,W)。

    skip_edges: 需要临时删除的边编号集合（用于第 5.6 节道路封闭实验）。
    """
    nodes = load_nodes(nodes_path)
    edges = load_edges(edges_path)
    skip_edges = skip_edges or set()

    g = WeightedGraph()
    for r in nodes:
        g.add_node(r["id"], name=r["name"], type=r["type"], role=r.get("role", ""),
                   x=float(r["x"]), y=float(r["y"]), verified=r.get("verified", "no"))
    for r in edges:
        if r["eid"] in skip_edges:
            continue
        g.add_edge(r["source"], r["target"], float(r["length"]))
    return g, edges


def delivery_points(nodes: List[dict]) -> List[str]:
    """配送图顶点 P = {S00, D01..D06}，S00 固定为 0 号点（TSP 起点）。"""
    station = [n["id"] for n in nodes if n["type"] == "station"]
    dels = sorted(n["id"] for n in nodes if n["type"] == "delivery")
    if not station:
        raise ValueError("nodes.csv 中没有 type=station 的节点")
    return [station[0]] + dels


def junction_points(nodes: List[dict]) -> List[str]:
    return sorted(n["id"] for n in nodes if n["type"] == "junction")


def verification_report(nodes: List[dict], edges: List[dict]) -> Dict[str, object]:
    """数据核验状态统计 —— 写进报告里，避免把草图数据当成实测数据。"""
    n_unv = sum(1 for n in nodes if n.get("verified", "no") != "yes")
    e_unv = sum(1 for e in edges if e.get("verified", "no") != "yes")
    srcs: Dict[str, int] = {}
    for e in edges:
        srcs[e.get("length_source", "unknown")] = srcs.get(e.get("length_source", "unknown"), 0) + 1
    return {
        "nodes_total": len(nodes),
        "nodes_unverified": n_unv,
        "edges_total": len(edges),
        "edges_unverified": e_unv,
        "length_sources": srcs,
        "is_real": (n_unv == 0 and e_unv == 0),
    }
