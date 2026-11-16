# -*- coding: utf-8 -*-
"""
一键重算：数据 -> 实验 -> 图表 -> 报告

用法：
    python main.py            # 全流程
    python main.py --draft    # 先重新生成建模草案数据（会覆盖 data/*.csv！）

依赖：numpy / matplotlib / networkx
"""
from __future__ import annotations
import os
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "src"))

os.environ.setdefault("MPLCONFIGDIR", "/tmp/mpl")


def main() -> None:
    t0 = time.time()
    if "--draft" in sys.argv:
        import draft_data
        draft_data.write_nodes(os.path.join(BASE, "data", "nodes.csv"))
        draft_data.write_edges(os.path.join(BASE, "data", "edges.csv"))
        print("[0/4] 已重新生成建模草案数据（data/*.csv 已覆盖）")

    import experiments
    import visualize
    import build_report

    print("[1/4] 运行 5 组实验 ...")
    meta = experiments.run_all()

    print("[2/4] 生成图表 ...")
    figs = visualize.run_all()

    print("[3/4] 生成报告 ...")
    paths = build_report.run_all()

    print("[4/4] 完成")
    print("-" * 62)
    v = meta["verification"]
    print(f"顶点 {v['nodes_total']} / 边 {v['edges_total']}  "
          f"已核验节点 {v['nodes_total'] - v['nodes_unverified']}  "
          f"已核验边 {v['edges_total'] - v['edges_unverified']}")
    if not v["is_real"]:
        print("⚠️  数据仍为建模草案（未实测）。见 data/校准表.md 与 README.md「数据替换」一节。")
    print(f"最优总路程 {meta['E5']['base_len']:.1f} m")
    print("-" * 62)
    for f in figs:
        print("  fig  ", os.path.relpath(f, BASE))
    for k in sorted(paths):
        print("  rep  ", os.path.relpath(paths[k], BASE))
    print(f"用时 {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
