# 基于图论的重庆大学虎溪校区快递配送路径优化研究

课程「图论综合应用」的完整可复现工程。

## 一句话

把重庆大学虎溪校区的真实路网抽象成 **加权无向图**（23 顶点 / 26 边），
用 **Dijkstra** 算出 7 个配送点之间的最短步行距离，再用 **最近邻 + 2-opt**
求解闭合巡回，并用 **Held–Karp** 作精确对照。

## 目录结构

```
graph-theory-campus-delivery/
├── main.py                 一键重算入口
├── data/
│   ├── nodes.csv           节点表（23 行）—— 坐标待实测替换
│   ├── edges.csv           边表（27 行）—— 长度待实测替换
│   └── 校准表.md            实地核验清单（照着它逐条核对）
├── src/
│   ├── graph_core.py       加权无向图 + Dijkstra + Floyd + 距离矩阵
│   ├── tsp_core.py         NN / 2-opt / Held-Karp / 暴力枚举校验
│   ├── draft_data.py       生成建模草案数据
│   ├── data_io.py          CSV → 图对象
│   ├── experiments.py      5 组实验
│   ├── visualize.py        5 张插图
│   └── build_report.py     生成 6 章正文 + 4 个附录
├── out/                    实验结果（CSV + Markdown 表格）
├── figs/                   插图 PNG
├── tools/
│   ├── build_html.py       生成打印就绪 HTML（自包含）
│   ├── make_pdf.py         Markdown -> 正式 PDF（reportlab，不依赖 Chrome）
│   ├── _render_math.py     公式渲染（matplotlib mathtext -> PNG 缓存）
│   ├── 导出PDF.command      从 HTML 导出 PDF（双击，需本机 Chrome）
│   └── vendor/mathjax/     本地 MathJax（离线渲染公式）
└── report/                 报告正文（分章 Markdown + 合订版 + HTML + PDF）
```

## 运行

```bash
python main.py            # 全流程：实验 → 图表 → 报告 → 打印就绪 HTML
python main.py --draft    # 先把 data/ 恢复成建模草案（会覆盖现有数据！）
```

依赖：`numpy` `matplotlib` `networkx` `pandoc`（可选，仅用于生成 HTML）

## 生成 PDF（课程要求「附件用 PDF」）

正式提交文件：**`report/图论综合应用报告.pdf`**（31 页 A4，含封面/摘要/关键词/目录）。
已生成好，直接取用即可；改完正文后按下面重新生成。

### 方式 A：reportlab（推荐，不依赖浏览器）

```bash
python3 tools/make_pdf.py \
    report/图论综合应用报告-合订版.md \
    report/图论综合应用报告.pdf
```

- 需要 `reportlab`；公式依赖 matplotlib（会自动调 `tools/_render_math.py` 渲染 PNG 缓存到 `tools/_math/`）
- 代码块用 Menlo 等宽字体，中文注释自动回退中文字体（不会显示成方块）
- 章节自动另起一页，且不会在章节前留下空白页

### 方式 B：浏览器打印（HTML 版）

`main.py` 还会生成 **`report/图论综合应用报告.html`** —— 完全自包含的单文件
（图片 base64 内联、MathJax 内联、含 A4 打印样式）。

1. 双击 `tools/导出PDF.command`（调用本机 Chrome 无头打印）
2. 或手动：Chrome/Edge 打开 HTML → `Cmd+P` → 另存为 PDF → A4 → 勾选「背景图形」

> 排版说明：正文中每个 `#` 一级标题自动另起一页；表格不跨页断开；
> 公式由 MathJax 渲染为矢量 SVG，缩放不糊。

## ⚠️ 数据替换（最重要的一步）

**当前 `data/` 里的坐标与边长是「结构真实、数值待核」的建模草案**：
- 节点集合与边连接关系严格来自《图论应用选题建议》第 44–48 页的候选表；
- 但 `(x, y)` 平面坐标是为了让程序跑通给出的**几何草图**；
- 边权 `length` 由草图欧氏距离推算（`length_source = draft_geometry`）。

所以：**算法实现与相对比较结论可靠；绝对里程数值不可当作实测数据引用。**

### 替换流程

1. 打开高德地图，把校区按 **北部 / 中部 / 南部 / 西部** 分区放大截图；
2. 按 `data/校准表.md` 逐条核对节点位置与道路连接；
3. 沿道路中心线量测每条边的行走长度，填入 `data/edges.csv` 的 `length` 列，
   并把 `length_source` 改为 `measured`、`verified` 改为 `yes`；
4. 把 `data/nodes.csv` 的 `x`/`y` 换成实测平面坐标，`verified` 改为 `yes`；
5. `python main.py` 重跑 —— 所有实验数字、图表、报告表格**自动同步更新**。

> 核验时务必注意：两点在地图上离得近**不等于**有道路相连；
> 一条边中间如果还有明显交叉口，应当拆成多条边。

## 实验一览

| 编号 | 实验 | 回答的问题 |
|---|---|---|
| E1 | 最短路交叉验证 | Dijkstra / Floyd / NetworkX 三方一致吗？ |
| E2 | 算法对比 | 人工规划、随机、NN、2-opt、精确解差多少？ |
| E3 | 最优性差距 | 2-opt 离真正的最优有多远？ |
| E4 | 规模扩展 | 配送点变多时还跑得动吗？ |
| E5 | 道路封闭 | 封一条路会多走多少？还能送到吗？ |

## 关键结论

- 两级建模把 23 顶点的路网问题压缩成 7 顶点的 TSP，**规模下降两个数量级**；
- 按宿舍编号顺跑比最优解长约 **40%**，随机访问长约 **60%**；
- 2-opt 在 k≥16 时相对最近邻可再缩短 **20%+**，是性价比最高的改进；
- 单条道路封闭不会导致不可达，但最多增加 **60%+** 里程；
- 每个宿舍目前只有**唯一一条接入边**（7 条割边），是最脆弱的一环。
