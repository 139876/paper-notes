# 📚 paper-notes

计算机视觉 / 遥感方向的 **论文精读笔记库**。四篇论文按 **角色** 排序，
统一放在 `论文精读/` 目录下，按 **1 / 2 / 3 / 4** 编号。

每篇论文一个独立目录，统一按
「知识地图 → 分讲拆解 → 批判性评价 → 复现清单」推进。

> 用 **Obsidian** 撰写，由 **Obsidian Git** 自动同步到本仓库 —— 提交历史即修改时间线。

---

## 🚪 入口

- **[四篇论文总索引](论文精读/00-总索引-四篇论文.md)** —— 目录结构、互链关系图、跨论文选题线索
- [阅读清单](paper-notes/论文精读/00-索引%20MOC.md) —— 各篇产出明细
- [仓库说明](#-关于这些笔记) —— 语法与同步

---

## 📖 阅读清单

| # | 论文 | 角色 | 精读产出 | 状态 |
|---|---|---|---|---|
| 1 | CCFA-Net: Cross-domain collaborative and foreground-aware for UAV object detection in hazy scenes | 背景 + baseline | [00-索引 MOC](论文精读/1-CCFA-Net精读/00-%E7%B4%A2%E5%BC%95%20MOC.md) · [详细索引](论文精读/1-CCFA-Net精读/README.md) | ✅ 44 篇 + 38 附件 |
| 2 | Cross-Modal Object Detection via UAV | 方法 | [00-索引 MOC](论文精读/2-Cross-Modal-UAV精读/00-%E7%B4%A2%E5%BC%95%20MOC.md) | ✅ 14 篇 + 13 附件 |
| 3 | HazyDet: Open-Source Benchmark for Drone-View Object Detection With Depth Cues in Hazy Scenes | 数据 | [00-索引 MOC](论文精读/3-HazyDet精读/00-%E7%B4%A2%E5%BC%95%20MOC.md) | ✅ 5 篇 |
| 4 | Cross-Domain Hyperspectral Image Generalization Based on Joint Variable Consistency and Anchor Structure Invariance | 理论 | [00-索引 MOC](论文精读/4-跨域高光谱精读/00-%E7%B4%A2%E5%BC%95%20MOC.md) | ✅ 13 篇（依据 IEEE 原文摘要 + 专利重写） |

---

## 📦 四个精读项目

### 1️⃣ CCFA-Net 精读 · 背景 + baseline

**论文**：Cross-domain collaborative and foreground-aware for UAV object detection in hazy scenes
**出处**：ISPRS Journal of Photogrammetry and Remote Sensing, 2026
**DOI**：[10.1016/j.isprsjprs.2026.04.020](https://doi.org/10.1016/j.isprsjprs.2026.04.020)
**规模**：44 篇笔记（18 公共基础 + 9 方向脉络 + 17 论文精读）+ 38 个附件

> 像素级的好看 ≠ 任务级的有用 —— 去雾指标涨了，检测反而跌，这是全文的立身之本。

[→ 进入项目](论文精读/1-CCFA-Net精读/00-%E7%B4%A2%E5%BC%95%20MOC.md) · [详细索引](论文精读/1-CCFA-Net精读/README.md)

### 2️⃣ Cross-Modal UAV 精读 · 方法

**论文**：Cross-Modal Object Detection via UAV
**出处**：IEEE Transactions on Vehicular Technology, Vol. 72, No. 8, pp. 10894–10905, Aug. 2023
**DOI**：[10.1109/TVT.2023.3262129](https://doi.org/10.1109/TVT.2023.3262129)
**规模**：14 篇笔记 + 13 个附件

> 模态鸿沟怎么跨？答案不是特征对齐，是**预测模仿** —— 让 IR 分支去模仿 RGB 分支的输出。

[→ 进入项目](论文精读/2-Cross-Modal-UAV精读/00-%E7%B4%A2%E5%BC%95%20MOC.md)

### 3️⃣ HazyDet 精读 · 数据

**论文**：HazyDet: Open-Source Benchmark for Drone-View Object Detection With Depth Cues in Hazy Scenes
**出处**：arXiv:2409.19833（2024）
**仓库**：[GrokCV/HazyDet](https://github.com/GrokCV/HazyDet)
**规模**：5 篇笔记

> 11000 对配对图像、364,393 个框、只有 3 类（Car 占 91.6%），而且**带深度标注** ——
> 这是 CCFA-Net 完全没用上的那条线。

[→ 进入项目](论文精读/3-HazyDet精读/00-%E7%B4%A2%E5%BC%95%20MOC.md)

### 4️⃣ 跨域高光谱精读 · 理论

**论文**：Cross-Domain Hyperspectral Image Generalization Based on Joint Variable Consistency and Anchor Structure Invariance
**出处**：IEEE Transactions on Geoscience and Remote Sensing, Vol. 64, Art. 5520916, 2026-07-06
**DOI**：[10.1109/TGRS.2026.3710332](https://doi.org/10.1109/TGRS.2026.3710332)
**配套专利**：CN202610642401（2026-07-03 公开）
**定位**：**域泛化（MDG）** · 多源训练 → 未见目标域零样本 · 跨传感器 / 跨场景高光谱分类
**规模**：13 篇（00 索引 + 01 速览 + 9 讲 + 3 附录）

> 三个模块分工：**JVC 管"别学错"**（联合变量分布对齐 + 互信息最小化），
> **ASI 管"别拉歪"**（动态簇锚点保住几何结构），**DBFDF 管"分得清"**（域特有 / 域共性解耦后融合）。
> 真实基准：Houston 2013 / Pavia University / Indian Pines，平均 OA **+1.74%**，std **相对降 11.25%**。

[→ 进入项目](论文精读/4-跨域高光谱精读/00-%E7%B4%A2%E5%BC%95%20MOC.md)

---

## 📁 目录结构

```
paper-notes/
├── README.md                       # 本文件
├── 00-索引 MOC.md                  # 阅读清单（跳转页）
└── 论文精读/                       # ← 四篇论文统一在这里
    ├── 00-总索引-四篇论文.md        # ★ 主索引：互链图 + 选题线索
    ├── 1-CCFA-Net精读/             # 第 1 篇 · 背景 + baseline
    │   ├── 00-索引 MOC.md
    │   ├── README.md
    │   ├── CCFA-Net.md
    │   ├── 01-公共基础知识/         # 18 篇
    │   ├── 02-方向知识脉络/         # 9 篇
    │   ├── 03-CCFA-Net论文精读/     # 17 篇
    │   └── 附件/                   # 38 个附件
    ├── 2-Cross-Modal-UAV精读/      # 第 2 篇 · 方法（14 篇）
    ├── 3-HazyDet精读/              # 第 3 篇 · 数据（5 篇）
    └── 4-跨域高光谱精读/            # 第 4 篇 · 理论（13 篇）
```

> 📌 **历史目录已合并**
> 旧结构 `计算机视觉/CCFA-Net精读/`、`计算机视觉/Cross-Modal-UAV精读/`、`遥感/跨域高光谱精读/`
> 已全部并入 `论文精读/` 下并按 1/2/3/4 编号。
> Git 历史保留了完整 rename 记录。

---

## ⚙️ 自动同步

本仓库由 **Obsidian Git** 插件自动同步，Obsidian 里的每一次修改都会自动 commit 并 push：

- 仓库地址：`https://github.com/139876/paper-notes`
- 同步范围：Obsidian 库中的 `paper-notes/` 目录（四个精读项目全部在内）
- 自动策略：每 5 分钟自动提交并推送一次，启动时自动拉取
- 手动操作：Obsidian 左侧 **Source Control** 面板 → `Sync` / `Push`

---

## 📝 关于这些笔记

笔记使用 Obsidian 专有语法（双链 `[[...]]`、嵌入 `![[附件/x.png]]`、Callout、块级公式 `$$...$$`）。
在 Obsidian 中阅读体验最佳；在 GitHub 网页端，公式、表格、代码块正常，双链与图片会显示为原始文本。

> ⚠️ **公式约定**：本库统一**只用 `$$` 独立块**渲染公式，不使用行内 `$...$`。

---

## 📌 声明

本仓库为个人学习笔记，仅供学习交流。论文版权归原作者所有。
