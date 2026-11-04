# 📚 paper-notes

计算机视觉 / 遥感方向的 **论文精读笔记库**。每篇论文一个独立目录，统一按
「知识地图 → 分讲拆解 → 批判性评价 → 复现清单」推进。

> 用 **Obsidian** 撰写，由 **Obsidian Git** 自动同步到本仓库 —— 提交历史即修改时间线。

---

## 📖 阅读清单

| # | 论文 | 角色 | 精读产出 |
|---|---|---|---|
| 1 | CCFA-Net: Cross-domain collaborative and foreground-aware for UAV object detection in hazy scenes | 背景 + baseline | [00-索引 MOC](计算机视觉/CCFA-Net%E7%B2%BE%E8%AF%BB/00-%E7%B4%A2%E5%BC%95%20MOC.md) · [详细索引](计算机视觉/CCFA-Net%E7%B2%BE%E8%AF%BB/README.md) |
| 2 | Cross-Modal Object Detection via UAV | 方法 | [00-索引 MOC](计算机视觉/Cross-Modal-UAV%E7%B2%BE%E8%AF%BB/00-%E7%B4%A2%E5%BC%95%20MOC.md) |
| 3 | HazyDet: Open-Source Benchmark for Drone-View Object Detection With Depth Cues in Hazy Scenes | 数据 | 进行中 |
| 4 | Cross-Domain Hyperspectral Image Generalization Based on Joint Variable Consistency and Anchor Structure Invariance | 理论 | [00-索引 MOC](遥感/%E8%B7%A8%E5%9F%9F%E9%AB%98%E5%85%89%E8%B0%B1%E7%B2%BE%E8%AF%BB/00-%E7%B4%A2%E5%BC%95%20MOC.md) |

---

## 📦 三个精读项目

### 1️⃣ CCFA-Net 精读 · 背景 + baseline

**论文**：Cross-domain collaborative and foreground-aware for UAV object detection in hazy scenes  
**出处**：ISPRS Journal of Photogrammetry and Remote Sensing, 2026  
**DOI**：[10.1016/j.isprsjprs.2026.04.020](https://doi.org/10.1016/j.isprsjprs.2026.04.020)  
**规模**：24 篇笔记 + 13 张示意图

> 像素级的好看 ≠ 任务级的有用 —— 去雾指标涨了，检测反而跌，这是全文的立身之本。

[→ 进入项目](计算机视觉/CCFA-Net%E7%B2%BE%E8%AF%BB/00-%E7%B4%A2%E5%BC%95%20MOC.md)  ·  [详细索引](计算机视觉/CCFA-Net%E7%B2%BE%E8%AF%BB/README.md)

### 2️⃣ Cross-Modal UAV 精读 · 方法

**论文**：Cross-Modal Object Detection via UAV  
**出处**：IEEE Transactions on Vehicular Technology, Vol. 72, No. 8, pp. 10894–10905, Aug. 2023  
**DOI**：[10.1109/TVT.2023.3262129](https://doi.org/10.1109/TVT.2023.3262129)  
**规模**：14 篇笔记 + 13 张示意图 + 1 个附件

> 模态鸿沟怎么跨？答案不是特征对齐，是**预测模仿** —— 让 IR 分支去模仿 RGB 分支的输出。

[→ 进入项目](计算机视觉/Cross-Modal-UAV%E7%B2%BE%E8%AF%BB/00-%E7%B4%A2%E5%BC%95%20MOC.md)

### 3️⃣ 跨域高光谱精读 · 理论

**论文**：Cross-Domain Hyperspectral Image Generalization Based on Joint Variable Consistency and Anchor Structure Invariance  
**出处**：无监督域适应（UDA）· 跨传感器 / 跨场景高光谱分类  
**规模**：5 篇笔记

> 两个损失同时上：变量一致（JVC）守光谱，锚结构不变（ASI）守几何。

[→ 进入项目](遥感/%E8%B7%A8%E5%9F%9F%E9%AB%98%E5%85%89%E8%B0%B1%E7%B2%BE%E8%AF%BB/00-%E7%B4%A2%E5%BC%95%20MOC.md)

---

## 📁 目录结构

```
paper-notes/
├── README.md                       # 本文件
├── 00-索引 MOC.md                  # 四篇论文的推进清单
├── 计算机视觉/
│   ├── CCFA-Net.md                 # CCFA-Net 论文正文笔记
│   ├── TVT_UAV_跨场景泛化与感知友好去雾_研究方案.md
│   ├── CCFA-Net精读/               # 项目 1 · 背景 + baseline
│   └── Cross-Modal-UAV精读/        # 项目 2 · 方法
└── 遥感/
    └── 跨域高光谱精读/             # 项目 3 · 理论
```

---

## ⚙️ 自动同步

本仓库由 **Obsidian Git** 插件自动同步，Obsidian 里的每一次修改都会自动 commit 并 push：

- 仓库地址：`https://github.com/139876/paper-notes`
- 同步范围：Obsidian 库中的 `paper-notes/` 目录（三个精读项目全部在内）
- 自动策略：每 5 分钟自动提交并推送一次，启动时自动拉取
- 手动操作：Obsidian 左侧 **Source Control** 面板 → `Sync` / `Push`

> 笔记使用 Obsidian 专有语法（双链 `[[...]]`、嵌入 `![[附件/x.png]]`、Callout、块级公式 `$$...$$`）。
> 在 Obsidian 中阅读体验最佳；在 GitHub 网页端，公式、表格、代码块正常，双链与图片会显示为原始文本。

---

## 📌 声明

本仓库为个人学习笔记，仅供学习交流。论文版权归原作者所有。
