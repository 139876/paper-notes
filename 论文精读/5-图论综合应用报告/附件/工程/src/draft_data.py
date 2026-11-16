# -*- coding: utf-8 -*-
"""
生成「建模草案版」校园路网数据（nodes.csv / edges.csv）。

诚实声明
--------
本文件生成的是【结构真实、坐标待核验】的建模草案：
  * 节点集合 (23 个) 与边连接关系 (E01-E20 + 7 条接入边) 严格来自
    《图论应用选题建议》第 44-48 页给出的候选表；
  * 但 (x, y) 局部平面坐标是为了让程序能跑通而给出的【几何草图】，
    并非高德/实地量测结果；
  * 边权 length 由草图坐标的欧氏距离推算，单位：米。

正式实验前必须用高德地图分区截图 + 实地核对替换：
  1) nodes.csv 的 x / y（改为实测平面坐标）
  2) edges.csv 的 length（改为沿道路中心线量测值）
  3) 把 verified 列改为 yes

改完只需重跑 `python main.py`，全部实验与图表会自动重算。
"""
from __future__ import annotations
import csv
import math
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")

# ---------------------------------------------------------------- 节点定义
# id, type, name, 角色说明, x(东,米), y(北,米)
# type: station(快递站) / delivery(配送点) / junction(道路节点)
NODES = [
    ("S00", "station",  "竹园北区快递服务站",   "唯一配送起点",          168, 795),
    ("D01", "delivery", "竹园学生公寓入口",     "配送点",                375, 915),
    ("D02", "delivery", "松园学生公寓入口",     "配送点",                170, 862),
    ("D03", "delivery", "梅园学生公寓入口",     "配送点",                555, 955),
    ("D04", "delivery", "兰园学生公寓入口",     "配送点",                455, 130),
    ("D05", "delivery", "菊园学生公寓入口",     "配送点",                700, 945),
    ("D06", "delivery", "荷园学生公寓入口",     "配送点",                805, 235),

    ("J01", "junction", "松园西侧道路转弯处",   "道路转弯",              200, 830),
    ("J02", "junction", "松园与梅园之间的北部道路", "道路交汇",          330, 900),
    ("J03", "junction", "第一教学楼西北侧",     "道路交汇",              520, 930),
    ("J04", "junction", "校车站附近",           "道路交汇",              690, 905),
    ("J05", "junction", "体育中心南侧道路",     "道路交汇",              860, 855),
    ("J06", "junction", "艺术楼附近",           "道路分岔",              950, 700),
    ("J07", "junction", "校园东侧南部道路转弯处", "道路转弯",            975, 545),
    ("J08", "junction", "东南部道路弯道",       "道路转弯",              920, 400),
    ("J09", "junction", "荷园附近道路交汇处",   "道路交汇",              790, 280),
    ("J10", "junction", "C栋附近道路交汇处",    "道路交汇",              630, 205),
    ("J11", "junction", "理科大楼北侧道路",     "道路交汇",              470, 165),
    ("J12", "junction", "图书馆西侧道路",       "道路交汇",              400, 340),
    ("J13", "junction", "云湖西侧道路分岔",     "道路分岔",              500, 540),
    ("J14", "junction", "云湖东侧道路分岔",     "道路分岔",              700, 555),
    ("J15", "junction", "软件学院南侧道路",     "道路交汇",              215, 480),
    ("J16", "junction", "校园西侧中部主干道",   "道路交汇",              145, 660),
]

# ---------------------------------------------------------------- 边定义
# eid, source, target, 道路区域说明   —— 拓扑严格照 PDF 第 45-46 页 E01-E20
EDGES = [
    ("E01", "J01", "J02", "北部道路"),
    ("E02", "J02", "J03", "北部道路"),
    ("E03", "J03", "J04", "第一教学楼附近"),
    ("E04", "J04", "J05", "体育中心附近"),
    ("E05", "J05", "J06", "东部道路"),
    ("E06", "J06", "J07", "东侧道路"),
    ("E07", "J07", "J08", "东南部道路"),
    ("E08", "J08", "J09", "南部道路"),
    ("E09", "J09", "J10", "荷园、C栋附近"),
    ("E10", "J10", "J11", "理科大楼附近"),
    ("E11", "J11", "J12", "中南部道路"),
    ("E12", "J12", "J13", "图书馆附近"),
    ("E13", "J13", "J14", "湖区道路"),
    ("E14", "J14", "J03", "东北部连接道路"),
    ("E15", "J13", "J15", "湖区西侧道路"),
    ("E16", "J15", "J16", "西部道路"),
    ("E17", "J16", "J01", "西北部道路"),
    ("E18", "J15", "J11", "西南方向连接道路"),
    ("E19", "J13", "J11", "湖区西南连接道路"),
    ("E20", "J12", "J11", "中部连接道路"),
]

# 配送节点接入边 E_D = {(S00,Js), (Di,Ji)}，PDF 第 46 页
ACCESS = [
    ("EA01", "S00", "J01", "快递站入口接入"),
    ("EA02", "D01", "J02", "竹园入口接入"),
    ("EA03", "D02", "J01", "松园入口接入"),
    ("EA04", "D03", "J03", "梅园入口接入"),
    ("EA05", "D04", "J11", "兰园入口接入"),
    ("EA06", "D05", "J04", "菊园入口接入"),
    ("EA07", "D06", "J09", "荷园入口接入"),
]

COORD = {n[0]: (n[4], n[5]) for n in NODES}


def euclid(a: str, b: str) -> float:
    (x1, y1), (x2, y2) = COORD[a], COORD[b]
    return math.hypot(x2 - x1, y2 - y1)


def write_nodes(path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "type", "name", "role", "x", "y", "verified"])
        for nid, typ, name, role, x, y in NODES:
            w.writerow([nid, typ, name, role, x, y, "no"])


def write_edges(path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["eid", "source", "target", "region", "length", "length_source", "verified"])
        for eid, s, t, region in EDGES + ACCESS:
            w.writerow([eid, s, t, region, f"{euclid(s, t):.1f}", "draft_geometry", "no"])


if __name__ == "__main__":
    os.makedirs(DATA, exist_ok=True)
    write_nodes(os.path.join(DATA, "nodes.csv"))
    write_edges(os.path.join(DATA, "edges.csv"))
    print(f"[draft_data] 已生成 nodes.csv / edges.csv  -> {DATA}")
    print(f"[draft_data] 顶点数 = {len(NODES)}，边数 = {len(EDGES) + len(ACCESS)}")
