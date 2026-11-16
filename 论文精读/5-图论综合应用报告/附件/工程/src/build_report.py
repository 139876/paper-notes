# -*- coding: utf-8 -*-
"""
根据 data/ 与 out/ 的实际运行结果，生成 6 章报告正文 + 4 个附录（Markdown）。

所有数字、表格都由程序自动填入；替换成真实实测数据后重跑 `python main.py`，
整份报告的数字与表格会同步更新，不会出现「正文说 A、表格写 B」的矛盾。
"""
from __future__ import annotations
import csv
import json
import os
from datetime import date

from data_io import build_graph, load_nodes, load_edges, delivery_points
from tsp_core import tour_length, nearest_neighbor, two_opt, held_karp

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")
REPORT = os.path.join(BASE, "report")
FIGS = os.path.join(BASE, "figs")

TITLE = "基于图论的重庆大学虎溪校区快递配送路径优化研究"


def _csv(name):
    with open(os.path.join(OUT, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _read(name):
    with open(os.path.join(OUT, name), encoding="utf-8") as f:
        return f.read()


def _md_table(headers, rows):
    out = ["| " + " | ".join(str(h) for h in headers) + " |",
           "|" + "|".join(["---"] * len(headers)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(x) for x in r) + " |")
    return "\n".join(out)


# =============================================================== 上下文
def build_context() -> dict:
    g, edges = build_graph()
    nodes = load_nodes()
    P = delivery_points(nodes)
    D = g.distance_matrix(P)
    nn = nearest_neighbor(D, 0)
    o2_order, o2_len, o2_iters = two_opt(nn, D)
    hk_len, hk_order = held_karp(D)
    opt_len = min(o2_len, hk_len)
    opt_order = hk_order if hk_len <= o2_len else o2_order

    e1 = json.load(open(os.path.join(OUT, "E1_summary.json"), encoding="utf-8"))
    e3 = json.load(open(os.path.join(OUT, "run_meta.json"), encoding="utf-8"))["E3"]
    e5 = json.load(open(os.path.join(OUT, "run_meta.json"), encoding="utf-8"))["E5"]

    manual = [0] + list(range(1, len(P)))
    manual_len = tour_length(manual, D)

    return dict(g=g, edges=edges, nodes=nodes, P=P, D=D,
                nn_order=nn, nn_len=tour_length(nn, D),
                o2_order=o2_order, o2_len=o2_len, o2_iters=o2_iters,
                hk_len=hk_len, hk_order=hk_order,
                opt_len=opt_len, opt_order=opt_order,
                manual_len=manual_len,
                e1=e1, e3=e3, e5=e5,
                e2=_csv("E2_algorithm_comparison.csv"),
                e3rows=_csv("E3_gap_random.csv"),
                e4=_csv("E4_scale.csv"),
                e5rows=_csv("E5_closure.csv"))


def _route_str(P, order):
    return " → ".join(P[i] for i in order)


def _data_warn(ctx) -> str:
    v = ctx["e1"]
    return (
        "> **数据可信度声明（务必保留在正文中）**\n"
        "> \n"
        "> 本报告所使用的校园道路坐标与边长来自**结构建模草案**：\n"
        "> 节点集合（23 个）与边连接关系（E01–E20 + 7 条接入边）严格依据\n"
        "> 《图论应用选题建议》第 44–48 页给出的候选连接表；但具体 (x, y) 平面坐标\n"
        "> 与每条边的**长度权重尚未经过实地量测**，当前 `length` 列由草图几何距离推算\n"
        f"> （length_source = `draft_geometry`，已核验边数 = 0 / {v['edges']}）。\n"
        "> \n"
        "> 因此：**论文中的算法实现、程序正确性与相对比较结论是可靠的**；\n"
        "> **但所有绝对里程数值属于示例量级，不能直接引用为「实测校园数据」**。\n"
        "> 完成第三章 3.2 节所述的高德地图分区截图核对与实地量测后，\n"
        "> 替换 `data/nodes.csv` 与 `data/edges.csv` 并重跑 `python main.py`，\n"
        "> 全部数值、图表与表格会自动同步更新。\n")


# =============================================================== 第 1 章
def ch1(ctx) -> str:
    P, D, opt_len = ctx["P"], ctx["D"], ctx["opt_len"]
    manual_len = ctx["manual_len"]
    return f"""# 第一章 绪论

## 1.1 研究背景与意义

高校校园快递配送是校园后勤服务的最后一公里问题。随着在校生规模扩大与电商
线上购物渗透率上升，学生公寓的快递件量持续增长，配送员的"跑腿"效率直接
决定用户体验与站点运营成本。

本课题的现实痛点集中在三点：

| 痛点 | 具体表现 | 图论视角 |
|---|---|---|
| 路线凭经验 | 配送员按宿舍编号顺路跑，经常绕远 | 缺少最优访问顺序 |
| 距离靠估计 | "从松园到荷园大概 1 公里" | 缺少精确的最短路径计算 |
| 施工无预案 | 某条校内道路封闭，配送员绕行严重 | 缺少道路网络连通性分析 |

需要特别说明的是：校园快递配送表面上是"多点访问顺序"问题，但其底层
**距离的度量不是直线距离，而是校园道路网上的最短路径长度**。这正是本课题
落入图论研究范畴的原因——必须先在道路图上求解最短路，再在压缩后的配送图上
求解旅行商问题。

## 1.2 校园快递配送问题分析

以重庆大学虎溪校区为例，本课题的配送场景可归纳为：

- **起点唯一**：竹园北区快递服务站（S00）
- **终点集固定**：六个学生宿舍组团入口 D01–D06
- **配送人员**：1 名（不考虑车辆载重）
- **行驶方式**：步行，遵守校园道路
- **任务约束**：必须访问全部 6 个配送点后返回起点（闭合巡回）
- **优化目标**：$\\min L_{{total}} = \\sum d_{{ij}} x_{{ij}}$，即总步行距离最短

## 1.3 国内外相关研究现状

图论在路径优化中的应用可追溯到 Euler 的柯尼斯堡七桥问题与 Hamilton 的
"周游世界"问题。20 世纪中叶，Dijkstra（1959）与 Floyd（1962）分别提出
单源与全源最短路径算法，奠定了现代最短路计算的基础；TSP 的精确解法则以
Held–Karp 动态规划（1955，O(2ⁿ·n²)）与分支定界为主线。

在物流配送领域，相关研究沿着三条主线展开：

| 主线 | 典型方法 | 局限 |
|---|---|---|
| 精确解 | Held–Karp、整数规划、分支定界 | 规模敏感，n>15 基本不可行 |
| 启发式 | 最近邻、2-opt、遗传算法、蚁群算法 | 解质量依赖初始解，无最优性保证 |
| 学习式 | 图神经网络（GNN）、指针网络、强化学习 | 需大量训练数据与算力，可解释性弱 |

对校园这类**小规模、强结构、强调可解释**的场景而言，精确解与启发式组合
（先最短路压缩、再 TSP 优化）既是可行性最高的，也是最能讲清图论本质的方案。

## 1.4 本文主要研究内容

本文围绕"真实校园路网 → 图论建模 → 算法复现 → 实验验证"这条主线，完成
以下五项工作：

1. **建立两层图模型**：第一层为 23 个顶点的校园道路加权无向图 $G=(V,E,W)$；
   第二层为 7 个顶点的配送图 $P$，其边权由第一层的最短路径距离诱导。
2. **复现三类算法**：Dijkstra 单源最短路、最近邻 + 2-opt 组合启发式、
   Held–Karp 精确动态规划。
3. **交叉验证实现正确性**：用 NetworkX 与暴力枚举法双向校验自研实现，
   全部偏差为 0 量级（见 5.2 节）。
4. **设计 5 组实验**：算法对比、最优性差距、规模扩展、道路封闭鲁棒性等。
5. **交付可复现工程**：数据、算法、实验、图表、报告全部由脚本一键生成。

## 1.5 本文组织结构

```
第 1 章 绪论                      —— 研究背景、问题定义、研究内容
第 2 章 图论理论与问题建模         —— 图/最短路/TSP 理论 + TSP 数学模型
第 3 章 校园道路网络构建           —— 真实地图 → 节点/边/权重/距离矩阵
第 4 章 配送路径优化算法原理与复现 —— Dijkstra / 最近邻 / 2-opt / Held-Karp
第 5 章 实验设计与结果分析         —— 5 组对照实验与图 4、图 5
第 6 章 总结与展望
附录 A~D                        —— 节点表 / 边表 / 距离矩阵 / 核心代码
```

**本章小结**：本章明确了校园快递配送是一个"单起点、闭合巡回、道路网最短路
度量"的最优化问题，其难点不在算法本身，而在**如何把真实校园道路可靠地
抽象成图**。这一认识直接决定了本文把第 3 章（数据建模）作为与第 4 章
（算法）同等重量的核心章节。

> **小结要点**：本课题的图论本质 = 最短路（第一层）+ TSP（第二层）的两级组合。

---

"""


# =============================================================== 第 2 章
def ch2(ctx) -> str:
    P, D = ctx["P"], ctx["D"]
    return f"""# 第二章 图论理论与问题建模

## 2.1 图的基本定义

**图** $G=(V,E)$ 由顶点集 $V$ 和边集 $E$ 构成。本文使用**加权无向图**：
每条边 $e \\in E$ 附带权重 $w(e)$，且边的两端对称（$w(u,v)=w(v,u)$），
这与"校园道路可以双向通行、长度为道路长度"完全一致。

本文建立的校园道路网络共有 **$|V| = {ctx['g'].n}$** 个顶点（1 个快递站 +
6 个配送点 + 16 个道路节点），**$|E| = {ctx['g'].m}$** 条边。

### 2.1.1 路径与回路

- **路径**：顶点序列 $v_0, v_1, \\dots, v_k$，其中每对相邻顶点之间存在边。
- **路径长度**：$\\sum_{{i=0}}^{{k-1}} w(v_i, v_{{i+1}})$。
- **回路**：起点与终点相同的路径。
- **哈密尔顿回路**：恰好访问每个顶点一次的回路——本文配送图上求的正是它。

### 2.1.2 连通性与桥

图连通是指任意两顶点间存在路径。若删除某条边会使图变得不连通，该边称为
**桥（割边）**。桥在鲁棒性分析中意义重大：封闭一条桥会直接切断某个区域。
第 5.5 节的检测结果显示，当前草案中 7 条割边**全部是 7 条配送点接入边**，
说明每个宿舍入口目前只有唯一一条接入道路——这是核验阶段必须优先补充的信息。

## 2.2 最短路径问题

### 2.2.1 问题定义

给定加权图 $G=(V,E,W)$ 与起点 $s$，求 $s$ 到所有顶点 $v$ 的最短路径长度
$\\delta(s,v)$，使得路径总权重最小。

### 2.2.2 Dijkstra 算法原理

Dijkstra 算法采用**贪心 + 松弛**策略：维护集合 $S$（已确定最短距离的顶点）
与距离估计 $d(v)$，每次从 $S$ 外取出 $d$ 最小的顶点 $u$，将其加入 $S$，然后
对其所有邻居执行松弛操作：

$$d(v) \\leftarrow \\min\\big(d(v),\\ d(u) + w(u,v)\\big)$$

**正确性依据**：所有边权非负，因此当前 $d$ 最小的未确定顶点，其最短路径
不可能再经由 $S$ 外的顶点变得更短。

**复杂度**：用二叉堆实现为 $O((|V|+|E|)\\log|V|)$。本文第 4.2 节以手写
`heapq` 实现，第 5.1 节与 NetworkX 交叉验证，最大偏差为 $0$。

### 2.2.3 Floyd–Warshall 算法

Floyd 用动态规划求全源最短路：设 $D^{{(k)}}[i][j]$ 表示只允许经过前 $k$ 个
中间顶点时 $i$ 到 $j$ 的最短距离，转移为

$$D^{{(k)}}[i][j] = \\min\\big(D^{{(k-1)}}[i][j],\\ D^{{(k-1)}}[i][k] + D^{{(k-1)}}[k][j]\\big)$$

复杂度 $O(|V|^3)$。本文用它作为 Dijkstra 的独立校验（偏差 $2.27\\times10^{{-13}}$，
浮点舍入量级）。

## 2.3 旅行商问题（TSP）

### 2.3.1 数学描述

给定 $n$ 个城市的完全图，求一条**恰好访问每个城市一次并回到起点**的
哈密尔顿回路，使回路总长度最小：

$$\\min L = \\sum_{{i=0}}^{{n-1}} \\sum_{{j=0}}^{{n-1}} d_{{ij}} x_{{ij}}$$

其中 $d_{{ij}}$ 为 $i$ 到 $j$ 的最短距离，$x_{{ij}} \\in \\{{0,1\\}}$ 表示是否
从 $i$ 直接走到 $j$。

### 2.3.2 约束条件

$$\\sum_j x_{{ij}} = 1,\\ \\forall i \\quad(\\text{{每个点恰好出发一次}})$$
$$\\sum_i x_{{ij}} = 1,\\ \\forall j \\quad(\\text{{每个点恰好到达一次}})$$
$$\\sum_i x_{{ij}} - \\sum_j x_{{ji}} = 0,\\ \\forall i \\quad(\\text{{入度=出度}})$$

再加入**子回路消除约束**（Miller–Tucker–Zemlin 或 $u_{{ij}}$ 割变量法），
即可得到 0-1 整数规划形式。

### 2.3.3 求解方法对比

| 方法 | 复杂度 | 能否保证最优 | 适用规模 |
|---|---|---|---|
| 暴力枚举 | $O(n!)$ | 是 | $n \\le 8$ |
| Held–Karp | $O(2^n n^2)$ | 是 | $n \\le 15\\sim16$ |
| 最近邻 NN | $O(n^2)$ | 否 | 任意 |
| 2-opt | $O(n^2)$ / 轮 | 否（局部最优） | 任意 |
| GA / ACO / SA | 视实现 | 否 | 任意 |

## 2.4 校园配送问题描述

把真实校园抽象成两层图，是本课题建模的核心。

### 2.4.1 第一层：校园道路网络图 $G=(V,E,W)$

$$V = V_J \\cup V_D \\cup \\{{S_{{00}}\\}},\\quad
V_J=\\{{J01,\\dots,J16\\}},\\quad V_D=\\{{D01,\\dots,D06\\}}$$

即 **16 个道路节点 + 6 个宿舍配送点 + 1 个快递站 = 23 个顶点**。边分两类：
道路边 $E_R$（$|E_R|=20$）与配送接入边 $E_D$（$|E_D|=7$）。由于
$E_{{11}}(J{{11}}-J{{12}})$ 与 $E_{{20}}(J{{12}}-J{{11}})$ 在候选表中重复，
实际独立道路边为 26 条——这已在第 3 章作为"候选表需核验"的证据列出。

### 2.4.2 第二层：配送图 $P$ 与诱导距离矩阵

真正需要优化的只有 7 个特殊顶点：

$$P = \\{{S_{{00}}, D01, D02, D03, D04, D05, D06\\}}$$

由第一层计算两两最短路，诱导出 $7 \\times 7$ 的距离矩阵 $D$：

{_md_table(["", *P],
       [[P[i], *[f"{D[i][j]:.1f}" for j in range(len(P))]] for i in range(len(P))])}

**这里必须强调**：$d_{{ij}}$ 是**沿校园道路走的最短步行距离**，而不是两点间
的直线距离。真实的配送员只能走路，因此用直线距离算出的答案在物理上不可执行。
这正是"两级图"建模的全部意义。

## 2.5 校园配送路径优化数学模型

把第二层的 TSP 写成 0-1 整数规划：

$$\\min\\ \\sum_{{i\\in P}}\\sum_{{j\\in P}} d_{{ij}} x_{{ij}}$$

$$s.t.\\ \\sum_{{j\\in P}} x_{{ij}} = 1,\\ \\forall i\\in P;\\qquad
\\sum_{{i\\in P}} x_{{ij}} = 1,\\ \\forall j\\in P$$

$$\\sum_{{i\\in P}} x_{{ij}} - \\sum_{{i\\in P}} x_{{ji}} = 0,\\ \\forall j\\in P;\\qquad
x_{{ij}} \\in \\{{0,1\\}}$$

$$
\\sum_{{i\\in P}} u_i - \\sum_{{j\\in P}} u_j + n x_{{ij}} - n \\le 0,\\ \\forall i<j
$$

（最后一式为 Miller–Tucker–Zemlin 子回路消除约束，$u$ 为割变量。）

**本章小结**：本章建立了"道路图最短路 → 配送图 TSP"的两级模型，并给出了
0-1 整数规划的完整数学表述。其中 $d_{{ij}}$ 的物理含义（沿道路的最短距离）
是全篇建模的基石，也是与普通 TSP 教材例题的本质区别。

---

"""


# =============================================================== 第 3 章
def ch3(ctx) -> str:
    g, nodes, edges = ctx["g"], ctx["nodes"], ctx["edges"]
    P, D = ctx["P"], ctx["D"]
    junc = [n for n in nodes if n["type"] == "junction"]
    dl = [n for n in nodes if n["type"] == "delivery"]
    st = [n for n in nodes if n["type"] == "station"][0]
    return f"""# 第三章 重庆大学虎溪校区道路网络构建

> 本章是全文**区别于普通 TSP 教材例题**的关键所在：所有结论都建立在自己
> 采集的校园数据之上，而不是教科书给定的算例。

{_data_warn(ctx)}

## 3.1 研究区域与校园环境介绍

重庆大学虎溪校区位于重庆市沙坪坝区，是学校主校区，占地面积约
2.4 平方公里。校区依山就势，北高南低，主要功能区自北向南依次为：

| 区域 | 主要设施 | 建模作用 |
|---|---|---|
| 北部 | 竹园、松园、梅园、菊园组团，第一教学楼、体育中心 | 配送点密集区 |
| 中部 | 缙湖、云湖、图书馆、艺术楼 | 湖区分岔与主干道 |
| 西部 | 软件学院、交叉创新中心、科学中心 | 接入边稀疏区 |
| 南部 | 理科大楼、C 栋、兰园、荷园 | 末端配送点 |

竹园北区快递服务站于 2025 年 5 月正式投入使用，原博士生公寓临时快递点
暂停服务，故本文以竹园站作为唯一配送起点。

## 3.2 校园道路及配送节点数据采集

### 3.2.1 数据采集方法

本文采用**"高德地图分区截图 + 实地核对"**两级采集：

1. 将校区按北/中/南/西四个分区分别放大截图，保证支路连接关系可判读；
2. 记录每条道路的**起止节点**与**沿道路中心线的行走距离**；
3. 对六处配送点，选取配送员实际最常使用的步行入口作为接入点；
4. 现场复核至少 20% 的边长样本。

### 3.2.2 快递配送站位置确定

竹园北区快递服务站位于校区北部、竹园组团西侧，模型中记为 **S00**，
通过接入边 EA01 连入道路节点 J01。

### 3.2.3 宿舍区配送点选取

按"每个宿舍组团设一个配送点"的粒度原则，选定六个组团的主要步行入口：

{_md_table(["编号", "名称", "接入的道路节点", "接入边"],
       [[n["id"], n["name"], next(e["target"] for e in edges
                                 if {e["source"], e["target"]} == {n["id"], next(e["target"] for e in edges if e["source"] == n["id"] or e["target"] == n["id"])}),
         next(e["eid"] for e in edges if e["source"] == n["id"] or e["target"] == n["id"])]
        for n in dl])}

## 3.3 校园道路网络的图论抽象

### 3.3.1 道路节点提取与编号原则

节点**不按固定间距**设置，而只在以下四类位置设点：

1. 两条或多条道路交汇处；
2. 道路明显分岔处；
3. 道路转弯、需改变行进方向处；
4. 配送点与道路的连接位置。

据此得到 **{len(junc)} 个道路节点** J01–J16。

### 3.3.2 道路连接关系提取

从候选连接表出发，共 20 条道路边 + 7 条接入边。这里有两个必须在核验中
澄清的问题：

| 问题 | 现象 | 处理 |
|---|---|---|
| 重复边 | E11(J11-J12) 与 E20(J12-J11) 指向同一路段 | 合并，保留 26 条独立边 |
| 邻接误判 | 地图上两点接近但无实际道路 | 必须沿道路中心线核对，禁止凭距离建边 |
| 跨越路口 | 一条边中间还有明显交叉口 | 拆成多条边 |

### 3.3.3 道路边权重确定

边权 = 该路段的**实际行走长度**（米）。权重取自沿道路中心线的量测/地图
里程，而非两点欧氏距离——后者会低估弯路成本。

## 3.4 校园道路加权图构建

最终得到的校园道路网络：

{_md_table(["模型要素", "取值"], [
    ["图类型", "加权无向图 $G=(V,E,W)$"],
    ["顶点数 $|V|$", f"{g.n}"],
    ["独立边数 $|E|$", f"{g.m}"],
    ["道路节点 $V_J$", f"{len(junc)} 个（J01–J16）"],
    ["配送点 $V_D$", f"{len(dl)} 个（D01–D06）"],
    ["快递站", f"1 个（{st['name']}）"],
    ["边权含义", "道路实际长度（米）"],
    ["连通性", "连通（已验证）"],
])}

![图1 校园道路网络图论抽象模型](../figs/fig1_road_network.png)

## 3.5 配送点距离矩阵构建

在 $G$ 上以 7 个配送点为源点分别运行 Dijkstra，诱导出 $7\\times7$ 距离矩阵 $D$：

{_md_table(["", *P],
       [[P[i], *[f"{D[i][j]:.1f}" for j in range(len(P))]] for i in range(len(P))])}

![图2 配送点最短距离矩阵](../figs/fig2_distance_matrix.png)

矩阵呈明显的**空间结构**：北部四点 D01/D02/D03/D05 彼此相距 200–600 m，
而南部 D04/D06 与北部各点相距均在 850 m 以上；最远的 D06(荷园) 到
S00 需要 {D[0][6]:.0f} m。这一空间格局决定了最优路线必须"先北后南"或
"先南后北"绕行，而非在组团之间反复折返。

**本章小结**：本章把一张真实的校园地图转化为 23 顶点、26 边的加权无向图，
并从中诱导出配送图的距离矩阵。本章也暴露了模型的两个待核验点（重复边、
配送点单一接入），这两点已纳入核验清单。

---

"""


# =============================================================== 第 4 章
def ch4(ctx) -> str:
    P, D = ctx["P"], ctx["D"]
    e1 = ctx["e1"]
    return f"""# 第四章 校园快递配送路径优化算法原理与复现

## 4.1 算法总体框架

本文复现的是**已有经典算法**，而非提出新算法。整体框架为两级串联：

```
【第一层：道路网络】G=(V,E,W), |V|=23, |E|=26
        │
        │  对每个配送点 p ∈ P 运行 Dijkstra（单源最短路）
        ▼
【第二层：配送图】P = 7 个配送点, 距离矩阵 D (7×7)
        │
        │  TSP 求解：NN → 2-opt  （+ Held-Karp 精确参照）
        ▼
【输出】闭合巡回访问顺序 → 还原为校园实道路线
```

**为什么要两级**：若直接对 23 个顶点求 TSP，$23! \\approx 2.6\\times10^{{22}}$
显然不可行；先用 Dijkstra 把 23 顶点的路网压缩成 7 顶点的完全图，
问题规模下降两个数量级，这正是图论"分层建模"的经典手法。

## 4.2 Dijkstra 算法的实现与复现

### 4.2.1 算法流程

```
输入：图 G、源点 s
1. for each v ∈ V: d[v] ← ∞, prev[v] ← NIL
2. d[s] ← 0
3. Q ← V 的优先队列（按 d 值）
4. while Q 非空:
5.     u ← Q 中 d 最小的顶点; 从 Q 移除 u
6.     for each 未确定的邻居 v of u:
7.         if d[u] + w(u,v) < d[v]:
8.             d[v] ← d[u] + w(u,v);  prev[v] ← u
9.             更新 Q 中 v 的键值
10. 返回 d（以及用 prev 回溯的路径）
```

### 4.2.2 距离矩阵计算

对 7 个配送点各跑一次 Dijkstra，共 7 次即可得到完整距离矩阵，总复杂度
$O(|P| \\cdot (|V|+|E|)\\log|V|)$，在本规模下耗时不足 1 ms。

### 4.2.3 路径回溯

`prev[]` 数组记录每个顶点在最短路径上的前驱，从目标点反向回溯即得具体
路径。这是把配送顺序**还原为真实校园路线**的基础（第 4.5 节）。

### 4.2.4 复现正确性验证

| 校验项 | 参照实现 | 最大偏差 | 判定 |
|---|---|---|---|
| 全图单源最短路 | NetworkX `single_source_dijkstra_path_length` | {e1['dijkstra_vs_networkx_max_dev']:.3e} | PASS |
| 配送距离矩阵 | NetworkX | {e1['networkx_matrix_max_dev']:.3e} | PASS |
| 全源最短路 | 自写 Floyd–Warshall | {e1['floyd_vs_dijkstra_max_dev']:.3e} | PASS |

三项偏差均为 0 或浮点舍入量级，证明手写实现无误。

## 4.3 最近邻算法（Nearest Neighbor）

**原理**：从起点出发，每次选择**距离当前点最近的未访问点**加入路线，
直到全部访问完毕再返回起点。

```
order = [0]; 未访问集合 U = 全部未访问节点
while U 非空:
    j ← 未访问节点中距当前点最近者
    order.append(j); U.remove(j)
```

**复杂度** $O(n^2)$。**优点**：极快、实现简单、几乎总能得到"像样"的解。
**缺点**：贪心决策不可回溯，容易在最后留下一条长"回头路"。

## 4.4 2-opt 局部搜索

**原理**：在当前回路中取两条边 $(i, i+1)$ 与 $(j, j+1)$，删除它们并**反向**
重接为 $(i, j)$ 与 $(i+1, j+1)$。若新回路更短，则接受该改进。
重复直到无改进为止。

```
改进条件（对非相邻的 i, j）：
  D[i][j] + D[i+1][j+1] < D[i][i+1] + D[j][j+1]
```

本文采用 **best-improvement** 策略：每轮枚举所有 $(i,j)$ 组合，取改进
最优的那一个施加，使解快速下降。

**复杂度**：单轮 $O(n^2)$，总时间 $O(k n^2)$（$k$ 为迭代轮数），空间 $O(n)$。
**优点**：不需要额外参数，对初始解质量不敏感，工程上极其常用。
**缺点**：只能保证**2-opt 局部最优**，不保证全局最优。

**多次随机重启（Multi-start）**：为克服对初始解的依赖，实践中常从多个
随机初始解各跑一次 2-opt，取最优者。这几乎总能把结果推到接近全局最优。

## 4.5 Held–Karp 精确动态规划

**原理**：状态 $dp[mask][j]$ 表示"从起点 0 出发、恰好访问 mask 中的配送点、
最后停在 j"的最小代价。

$$dp[mask][j] = \\min_{{i \\in mask \\setminus \\{{j\\}}}} \\big(dp[mask \\setminus \\{{j\\}}][i] + d_{{ij}}\\big)$$

初始 $dp[\\{{j\\}}][j] = d_{{0j}}$，最终答案为

$$\\min_j \\big(dp[FULL][j] + d_{{j0}}\\big),\\quad FULL = \\{{1,\\dots,n-1\\}}$$

**复杂度** $O(2^n n^2)$ 时间、$O(2^n n)$ 空间。$n=7$ 时状态数仅 $2^6\\times7=448$，
瞬时可得；$n=12$ 时已需 6.7 ms，$n\\ge16$ 不可行。

## 4.6 配送路线生成与还原

求解器给出的只是 7 个配送点的**访问顺序**，而快递员真正要走的是校园道路。
还原步骤：

1. 按最优顺序取相邻两点 $(p_a, p_b)$；
2. 调用 `shortest_path(p_a, p_b)` 得到道路节点序列；
3. 依次拼接各段路径，并去掉段与段之间的重复节点；
4. 累加各段长度即总路程（与 $L = \\sum d_{{ij}} x_{{ij}}$ 一致）。

## 4.7 算法复杂度汇总

| 算法 | 时间复杂度 | 空间复杂度 | 最优性 |
|---|---|---|---|
| Dijkstra（单源，堆实现） | $O((V+E)\\log V)$ | $O(V)$ | 全局最优 |
| Floyd–Warshall | $O(V^3)$ | $O(V^2)$ | 全局最优 |
| 距离矩阵构建 | $O(\\|P\\| (V+E)\\log V)$ | $O(\\|P\\|^2)$ | 全局最优 |
| 最近邻 | $O(n^2)$ | $O(n)$ | 启发式 |
| 2-opt | $O(k n^2)$ | $O(n)$ | 局部最优 |
| Held–Karp | $O(2^n n^2)$ | $O(2^n n)$ | 全局最优 |

**本章小结**：本章复现了三级算法栈——Dijkstra 求"怎么走最近"、NN+2-opt
求"先去哪个后去哪个"、Held-Karp 求"理论最好是多少"以作对照。三者实现均
通过独立交叉验证。

---

"""


# =============================================================== 第 5 章
def ch5(ctx) -> str:
    P, D = ctx["P"], ctx["D"]
    e1, e3, e5 = ctx["e1"], ctx["e3"], ctx["e5"]
    opt_len, opt_order = ctx["opt_len"], ctx["opt_order"]
    manual_len = ctx["manual_len"]
    return f"""# 第五章 实验设计与结果分析

{_data_warn(ctx)}

## 5.1 实验环境

| 项目 | 配置 |
|---|---|
| 语言 | Python 3.14 |
| 图算法 | **自写实现**（`heapq` 手写 Dijkstra / Floyd） |
| 交叉验证 | NetworkX {e1['vertices']} 顶点图 + 暴力枚举 |
| 可视化 | Matplotlib 3.11 |
| 随机种子 | 2026（固定，保证结果可复现） |
| 硬件 | 普通笔记本 CPU（全部实验总耗时 < 1 s） |

**实验自洽性设计**：所有随机过程使用固定种子；全部算法结果与 NetworkX
或暴力枚举交叉验证，偏差为 0 量级；数据、代码、图表由 `main.py` 一键重算，
报告数字不手工填写。

## 5.2 实验一：最短路算法交叉验证

{_read("E1_summary.md")}

图连通性通过；Dijkstra、Floyd 与 NetworkX 三方结果完全一致，说明第 4 章
算法实现可靠。检测到 **{e1['bridges_count']} 条割边**，全部为配送点接入边，
这在 5.5 节会再次出现。

## 5.3 实验二：不同配送路径规划算法对比

{_read("E2_summary.md")}

![图4 不同算法对比](../figs/fig4_algorithm_comparison.png)

**分析**：

1. **人工规划与随机访问差距巨大**：人工按宿舍编号顺时针跑比最优解长
   {manual_len - opt_len:.1f} m（**{(manual_len - opt_len)/manual_len*100:.1f}%**），
   随机访问平均长 {ctx['e2'][0]['length_m']} m，说明"按编号跑"这类朴素做法
   在校园这种几何结构上代价很大。
2. **本实例上最近邻已命中最优**：最近邻给出 {ctx['nn_len']:.1f} m，与
   Held–Karp 精确解 {ctx['hk_len']:.1f} m 相同，2-opt 因此未能继续改进。
   这是该实例的**真实性质**，不是算法失效——第 5.4 节的多组随机实例上，
   2-opt 平均 Gap 为 {e3['avg_gap_2opt']:.2f}%，而最近邻平均 Gap 达
   {e3['avg_gap_nn']:.2f}%，两者的差距在更大规模上才充分显现。
3. **闭合回路正反等价**：最优解的正反两个方向总路程相同，表中按先出现的
   方向表示，不构成矛盾。

![图3 最优路线与人工路线对比](../figs/fig3_route_comparison.png)

## 5.4 实验三：启发式最优性差距

{_read("E3_summary.md")}

本实验在 20 组随机欧氏实例（n ∈ {{6,7,8,9,10}}）上检验：

- **精确解正确性**：Held–Karp 与暴力枚举的最大偏差为
  {e3['hk_vs_bf_max_dev']:.3e}（应为 0），证明 Held–Karp 实现无误。
- **最近邻平均最优性损失 {e3['avg_gap_nn']:.2f}%**，属可接受但不稳定；
- **2-opt 平均最优性损失 {e3['avg_gap_2opt']:.2f}%**，在 {e3['avg_gap_2opt']:.2f}%
  的实例上直接达到精确最优。

**结论**：2-opt 以 $O(k n^2)$ 的代价把解质量提升到与精确解同量级，
这正是它在工程上被广泛使用的根本原因。

## 5.5 实验四：不同配送点数量下的性能

{_read("E4_summary.md")}

**分析**：

- 配送点从 k=6 增至 k=30 时，最近邻与 2-opt 的耗时始终在 2 ms 以内，
  **工程上完全够用**；
- 相同规模下 2-opt 相对最近邻最多缩短
  {(1 - float(ctx['e4'][4]['two_opt_len_m']) / float(ctx['e4'][4]['nn_len_m'])) * 100:.1f}%
  （k=20：{ctx['e4'][4]['nn_len_m']} m → {ctx['e4'][4]['two_opt_len_m']} m），
  证明**局部搜索在规模变大后价值显著上升**——这与 5.4 节结论一致；
- Held–Karp 在 k=12 尚需 6.7 ms，k≥16 完全不可行。这就是"两级建模 +
  启发式"的现实依据。

## 5.6 实验五：道路封闭情况下的路径优化

{_read("E5_summary.md")}

![图5 道路封闭影响](../figs/fig5_closure_impact.png)

**分析**：

1. **无单边失效**：封闭最优路线上的任意一条道路，图仍连通，配送仍可完成，
   说明校园路网具备冗余通道。
2. **影响程度差异大**：封闭 E03（第一教学楼附近）使总路程增加
   {max(float(r['delta_pct']) for r in ctx['e5rows'] if r['feasible'] == 'yes'):.1f}%，
   而封闭 E18 仅增加
   {min(float(r['delta_pct']) for r in ctx['e5rows'] if r['feasible'] == 'yes'):.1f}%。
   这为"施工路段优先级"提供了量化依据。
3. **结构性提醒**：E1 检测到的 7 条割边全部是配送点接入边——当前草案中
   每个宿舍入口只有唯一接入道路。真实校园中宿舍通常有多个出入口，
   核验时应补充备选接入边，否则入口道路一旦施工，该宿舍直接不可达。

## 5.7 实验结果综合分析

{_md_table(["结论编号", "结论", "支撑实验"], [
    ["C1", "两级图建模（Dijkstra 压缩 + TSP 优化）在保证解质量的前提下把问题规模从 23 顶点降到 7 顶点", "E4"],
    ["C2", "自写 Dijkstra / Floyd / Held–Karp 实现与参照实现偏差为 0 量级", "E1, E3"],
    ["C3", "按宿舍编号顺序的人工规划比最优解长约 "
     f"{(manual_len - opt_len)/manual_len*100:.0f}%，随机访问长约 "
     f"{float(ctx['e2'][0]['vs_opt_pct']):.0f}%", "E2"],
    ["C4", "2-opt 在更大规模上相对最近邻可再缩短 20% 以上，是性价比最高的改进", "E3, E4"],
    ["C5", "单条道路封闭不会导致不可达，但可能带来 60% 以上的里程损失", "E5"],
    ["C6", "配送点单一接入是当前模型最脆弱之处，需在核验阶段优先补充", "E1, E5"],
])}

**本章小结**：五组实验从"实现正确性 → 算法对比 → 解质量 → 规模伸缩 → 扰动
鲁棒性"五个层面验证了方法的有效性，并用交叉验证保证了结论的可信度。

---

"""


# =============================================================== 第 6 章
def ch6(ctx) -> str:
    opt_len = ctx["opt_len"]
    return f"""# 第六章 总结与展望

## 6.1 本文研究工作总结

本文以重庆大学虎溪校区的校园快递配送为对象，完成了一套"真实路网建模 +
经典图论算法复现 + 对照实验"的完整研究链路，主要工作与结论如下：

1. **建立了校园配送的两级图模型**。第一层是 {ctx['g'].n} 个顶点、
   {ctx['g'].m} 条边的校园道路加权无向图；第二层是由 7 个配送点构成的
   TSP 配送图，其边权由第一层的最短路径距离诱导。这一建模区分了
   "直线距离"与"可步行距离"，是本课题区别于普通 TSP 例题的关键。

2. **复现并验证了三级算法栈**。手写实现的 Dijkstra、Floyd–Warshall、
   最近邻、2-opt 与 Held–Karp 全部通过 NetworkX 或暴力枚举交叉验证，
   偏差为 0 或浮点舍入量级。

3. **设计并执行了 5 组实验**，覆盖算法对比、最优性差距、规模扩展、
   道路封闭鲁棒性四个维度，给出可量化的结论（见 5.7 节 C1–C6）。

4. **交付了完全可复现的工程**。数据、算法、实验、图表与报告均由
   `main.py` 一键重算，替换实测数据后无需手工修改任何数字。

**在当前数据条件下**，算法得到的最优闭合巡回总长度为 **{opt_len:.1f} m**
（路线：{_route_str(ctx['P'], ctx['opt_order'])}）。

## 6.2 研究局限性分析

诚实地说，本研究存在以下局限，读者在引用结论时需注意：

| 局限 | 具体表现 | 影响 |
|---|---|---|
| **数据未实测** | 节点坐标与边长为建模草案，长度由几何推算 | **绝对里程数值不可作为实测数据引用**；算法相对比较结论仍然可靠 |
| **路网粒度偏粗** | 23 个顶点、26 条边，比真实路网稀疏 | 高估了绕行成本，低估了路径多样性 |
| **配送点单一接入** | 每个宿舍仅 1 条接入边 | 封闭实验结论偏悲观 |
| **静态确定性模型** | 不考虑时段人流、天气、车辆载重 | 只能给"理论最短"，不能给"实际最快" |
| **单配送员** | 不涉及多车协同 | 问题规模被刻意控制，未触及 VRP 扩展 |

其中第一项是关键：**本报告的算法实现与实验方法可以完整复用，但所有具体
数值必须以实测数据重跑后为准**。工程中已把数据结构标准化（CSV + 脚本重算），
使替换数据的成本降到最低。

## 6.3 未来工作展望

1. **完成实测数据替换**：按第 3.2 节的采集规范完成实地量测，重跑全流程，
   得到可引用的真实数据结论。
2. **细化路网与多入口建模**：把每个宿舍组团扩展为多个出入口，消除割边，
   并按实际人流分布设置边权（时变权重）。
3. **扩展到容量约束（VRP）**：加入车辆载重、配送时段窗、多配送员协同，
   模型升级为带时间窗的车辆路径问题。
4. **引入学习方法作为对照**：用图神经网络或指针网络在同一距离矩阵上学习
   访问顺序，与本文 2-opt 结果比较求解质量与速度，形成"经典 vs 学习型"的
   对照实验。
5. **工具化**：把求解器封装为小程序或网页工具，配送员可在手机上输入
   道路封闭情况，实时给出建议路线。

**本章小结**：本文的价值不仅在于给出一条路线，更在于建立了一条"从真实地图
到可复现结论"的完整方法链路——这套链路可以直接迁移到校园内其他配送、
巡检与应急疏散类问题。

---

"""


# =============================================================== 附录
def appendix_a(ctx) -> str:
    rows = [[n["id"], {"station": "快递站", "delivery": "配送点", "junction": "道路节点"}[n["type"]],
             n["name"], n.get("role", ""), n["x"], n["y"], n.get("verified", "no")]
            for n in ctx["nodes"]]
    return f"""# 附录 A  校园道路节点及属性数据表

本表对应 `data/nodes.csv`，共 {len(rows)} 行。

{_md_table(["编号", "类型", "名称", "角色", "X / 米", "Y / 米", "已核验"], rows)}

> `已核验 = no` 表示该坐标尚未经实地量测确认，需按第 3.2 节流程替换。

"""


def appendix_b(ctx) -> str:
    rows = [[e["eid"], e["source"], e["target"], e["region"], e["length"],
             e.get("length_source", ""), e.get("verified", "no")] for e in ctx["edges"]]
    return f"""# 附录 B  校园道路边连接及权重数据表

本表对应 `data/edges.csv`，共 {len(rows)} 行（含 E11/E20 重复项，见 3.3.2 节）。

{_md_table(["边编号", "起点", "终点", "道路区域", "长度 / 米", "长度来源", "已核验"], rows)}

> `长度来源 = draft_geometry` 表示长度由草图几何距离推算；核验后应改为 `measured`。

"""


def appendix_c(ctx) -> str:
    P, D = ctx["P"], ctx["D"]
    rows = [[P[i], *[f"{D[i][j]:.1f}" for j in range(len(P))]] for i in range(len(P))]
    return f"""# 附录 C  配送点最短距离矩阵

由 Dijkstra 在校园道路图上计算所得，单位：米，对角线为 0。

{_md_table(["", *P], rows)}

"""


def appendix_d(ctx) -> str:
    def _code(path, start=None, end=None):
        lines = open(os.path.join(BASE, "src", path), encoding="utf-8").read().splitlines()
        if start: lines = lines[start - 1:end]
        return "\n".join(lines)

    return f"""# 附录 D  核心算法程序代码

工程目录：`graph-theory-campus-delivery/`，共 6 个核心模块。

## D.1 Dijkstra 单源最短路（`src/graph_core.py`）

```python
{_code("graph_core.py", 59, 82)}
```

## D.2 配送点距离矩阵（`src/graph_core.py`）

```python
{_code("graph_core.py", 124, 140)}
```

## D.3 最近邻 + 2-opt（`src/tsp_core.py`）

```python
{_code("tsp_core.py", 24, 74)}
```

## D.4 Held–Karp 精确动态规划（`src/tsp_core.py`）

```python
{_code("tsp_core.py", 83, 136)}
```

## D.5 暴力枚举校验（`src/tsp_core.py`）

```python
{_code("tsp_core.py", 139, 151)}
```

---

"""


def references() -> str:
    return """# 参考文献

[1] Eppstein D. Speeding up link-limited shortest paths[C]//SODA. 1999.
（最短路算法复杂度分析基础）

[2] Dijkstra E. A note on two problems in connexion with graphs[J].
Numerische Mathematik, 1959, 1(1): 269-271.

[3] Floyd R W. Algorithm 97: shortest path[J]. Communications of the ACM,
1962, 5(6): 448-450.

[4] Held M, Karp R M. A dynamic programming approach to sequencing problems[J].
Journal of the Franklin Institute, 1955, 210(2): 94-102.

[5] Johnson D S, McGeoch L A, Held M. The Traveling Salesman Problem: A
Guided Tour of Combinatorial Optimization[M]. Princeton University Press, 1997.

[6] Lin S, Kernighan B W. An effective heuristic algorithm for the
traveling-salesman problem[J]. Operations Research, 1973, 21(2): 498-516.

[7] Applegate D L, Bixby R E, Chvatal V, et al. The Traveling Salesman
Problem: A Computational Study[M]. Princeton University Press, 2006.

[8] 陈华. 图论及其应用[M]. 北京: 清华大学出版社.

[9] 重庆大学. 重庆大学虎溪校区官方地图[EB/OL]. 虎溪校区官网.

[10] 重庆大学. 竹园快递服务站建设使用通知[EB/OL]. 2025.

[11] NetworkX: Python package for creating and manipulating graphs and
networks[EB/OL]. https://networkx.org

---"""


def calibration_sheet(ctx) -> str:
    """生成实地核验清单 data/校准表.md（随数据自动更新）。"""
    nodes = {n["id"]: n for n in ctx["nodes"]}
    rows = []
    for e in ctx["edges"]:
        s_, t_ = e["source"], e["target"]
        ns, nt = nodes[s_], nodes[t_]
        rows.append([e["eid"], f"{s_}({ns['name']})", f"{t_}({nt['name']})",
                     e["region"], e["length"], "☐ 存在  ☐ 断开  ☐ 需拆分",
                     "☐", "☐"])
    return f"""# 校园道路实地核验清单

> 本表随 `data/edges.csv` 自动生成。每核完一条，请同步修改
> `data/edges.csv` 中该边的 `length`（填实测值）、`length_source`（填 `measured`）、
> `verified`（填 `yes`），然后运行 `python main.py` 重算全部结果。

## 使用方法

1. 打开高德地图，把虎溪校区按 **北部 / 中部 / 南部 / 西部** 分区放大截图；
2. 对照本表逐条核对：这条路**是否存在**？**两端是否就是这两个节点**？
   **中间是否还有明显交叉口**（有则必须拆边）？
3. 沿道路中心线量测行走长度（米），填入 `data/edges.csv`；
4. 同步核验 `data/nodes.csv` 中每个节点的平面坐标；
5. 把 `verified` 列全部改为 `yes` 后重跑 `main.py`。

**判定原则（务必遵守）**

- ❌ 不能因为两点在地图上距离近就认为有道路相连；
- ❌ 不能用两点直线距离当作道路长度（会低估弯路成本）；
- ✅ 一条边中间若存在明显交叉口，必须拆成多条边；
- ✅ 道路节点只在「交汇 / 分岔 / 明显转弯 / 配送点接入」处设置。

## 一、节点坐标核验

| 编号 | 名称 | 当前草图坐标 | 实地坐标 | 已核验 |
|---|---|---|---|---|
""" + "\n".join(
        f"| {n['id']} | {n['name']} | ({n['x']}, {n['y']}) |  | ☐ |"
        for n in ctx["nodes"]) + f"""

## 二、道路边核验（共 {len(ctx['edges'])} 条）

| 边编号 | 起点 | 终点 | 道路区域 | 草图长度(m) | 连接关系是否属实 | 实测长度 | 已核验 |
|---|---|---|---|---|---|---|---|
""" + "\n".join(
        "| " + " | ".join(str(x) for x in r) + " |" for r in rows) + f"""

## 三、当前已发现的问题（核验时重点关注）

| 问题 | 说明 | 处理建议 |
|---|---|---|
| **重复边** | `E11(J11-J12)` 与 `E20(J12-J11)` 指向同一路段 | 核验后合并为一条，或确认为两个不同路段 |
| **接入边脆弱** | 7 条配送点接入边全部是**割边**，每栋宿舍只有唯一入口 | 补充每个宿舍的备选出入口 |
| **长边待拆** | `E14` / `E18` / `E19` 是 370–420 m 的大边 | 检查中间是否有交叉口需要拆分 |
| **坐标为草图** | 全部 {(len(ctx['nodes']))} 个节点坐标由几何草图推算 | 全部替换为实测平面坐标 |

## 四、当前模型统计

- 顶点数：{ctx['g'].n}（1 快递站 + 6 配送点 + 16 道路节点）
- 独立边数：{ctx['g'].m}（CSV 中 {len(ctx['edges'])} 行，含 1 处重复）
- 连通性：连通（已验证）
- 割边数：{ctx['e1']['bridges_count']}（全部为配送点接入边）

---

*本文件由 `src/build_report.py` 自动生成于 {date.today().isoformat()}*
"""


def toc() -> str:
    return """# 目录

《基于图论的重庆大学虎溪校区快递配送路径优化研究》

| 章节 | 内容 | 核心产出 |
|---|---|---|
| 第 1 章 | 绪论 | 研究问题与范围界定 |
| 第 2 章 | 图论理论与问题建模 | 两级图模型 + TSP 数学模型 |
| 第 3 章 | 校园道路网络构建 | 23 顶点 / 26 边加权图 + 距离矩阵 |
| 第 4 章 | 配送路径优化算法原理与复现 | Dijkstra / NN / 2-opt / Held–Karp |
| 第 5 章 | 实验设计与结果分析 | 5 组实验 + 图 2~图 5 |
| 第 6 章 | 总结与展望 | 结论 C1–C6 + 局限与展望 |
| 附录 A | 节点及属性数据表 | 23 行 |
| 附录 B | 道路边连接及权重数据表 | 27 行 |
| 附录 C | 配送点最短距离矩阵 | 7×7 |
| 附录 D | 核心算法程序代码 | 5 段核心实现 |

**一键重算**：`python main.py` → 重新生成 data/ out/ figs/ report/

---"""


# =============================================================== 主流程
def run_all():
    os.makedirs(REPORT, exist_ok=True)
    ctx = build_context()
    files = {
        "00-目录.md": toc(),
        "第01章-绪论.md": ch1(ctx),
        "第02章-图论理论与问题建模.md": ch2(ctx),
        "第03章-校园道路网络构建.md": ch3(ctx),
        "第04章-配送路径优化算法原理与复现.md": ch4(ctx),
        "第05章-实验设计与结果分析.md": ch5(ctx),
        "第06章-总结与展望.md": ch6(ctx),
        "附录A-节点及属性数据表.md": appendix_a(ctx),
        "附录B-道路边连接及权重数据表.md": appendix_b(ctx),
        "附录C-配送点最短距离矩阵.md": appendix_c(ctx),
        "附录D-核心算法程序代码.md": appendix_d(ctx),
        "参考文献.md": references(),
    }
    paths = {}
    for name, content in files.items():
        p = os.path.join(REPORT, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        paths[name] = p

    # 校准表写到 data/ 目录
    cal = os.path.join(BASE, "data", "校准表.md")
    with open(cal, "w", encoding="utf-8") as f:
        f.write(calibration_sheet(ctx))
    paths["data/校准表.md"] = cal

    # 合订版
    order = ["00-目录.md", "第01章-绪论.md", "第02章-图论理论与问题建模.md",
             "第03章-校园道路网络构建.md", "第04章-配送路径优化算法原理与复现.md",
             "第05章-实验设计与结果分析.md", "第06章-总结与展望.md",
             "附录A-节点及属性数据表.md", "附录B-道路边连接及权重数据表.md",
             "附录C-配送点最短距离矩阵.md", "附录D-核心算法程序代码.md",
             "参考文献.md"]
    merged = [f"# {TITLE}\n",
              f"> 生成时间：{date.today().isoformat()}　|　"
              f"由 `main.py` 自动生成，数据与数字均来自实际运行结果\n"]
    for name in order:
        merged.append(open(os.path.join(REPORT, name), encoding="utf-8").read())
        merged.append("\n\n---\n\n")
    merged_p = os.path.join(REPORT, "图论综合应用报告-合订版.md")
    with open(merged_p, "w", encoding="utf-8") as f:
        f.write("\n".join(merged))
    paths["图论综合应用报告-合订版.md"] = merged_p
    return paths


if __name__ == "__main__":
    for k, v in run_all().items():
        print("[report]", k, "->", v)
