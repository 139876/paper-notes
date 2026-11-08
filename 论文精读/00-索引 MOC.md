---
tags: [MOC, 阅读清单, 入口]
aliases: [索引, 阅读清单, MOC]
created: 2026-11-04
status: 进行中
---

# 📚 四篇论文 · 阅读清单（入口）

> [!info] 主入口已迁移
> 本页现在是**跳转页**。
> 👉 **主索引** → [[paper-notes/论文精读/00-总索引-四篇论文|四篇论文总索引]]

---

## 📋 阅读清单

| # | 论文 | 角色 | 索引 |
|---|---|---|---|
| **1** | CCFA-Net: Cross-domain collaborative and foreground-aware for UAV object detection in hazy scenes | 背景 + baseline | [[paper-notes/论文精读/1-CCFA-Net精读/00-索引 MOC\|00-索引 MOC]] · [[paper-notes/论文精读/1-CCFA-Net精读/README\|详细索引]] |
| **2** | Cross-Modal Object Detection via UAV ([DOI](https://doi.org/10.1109/TVT.2023.3262129)) | 方法 | [[paper-notes/论文精读/2-Cross-Modal-UAV精读/00-索引 MOC\|00-索引 MOC]] |
| **3** | HazyDet: Open-Source Benchmark for Drone-View Object Detection With Depth Cues in Hazy Scenes | 数据 | [[paper-notes/论文精读/3-HazyDet精读/00-索引 MOC\|00-索引 MOC]] |
| **4** | Cross-Domain Hyperspectral Image Generalization Based on Joint Variable Consistency and Anchor Structure Invariance<br>[IEEE TGRS 2026, DOI 10.1109/TGRS.2026.3710332](https://doi.org/10.1109/TGRS.2026.3710332) | 理论 | [[paper-notes/论文精读/4-跨域高光谱精读/00-索引 MOC\|00-索引 MOC]] |

> 📌 四篇**统一放在** `paper-notes/论文精读/` 下，按 **1 / 2 / 3 / 4** 编号排序。
> 目录结构、互链关系、选题线索 → [[paper-notes/论文精读/00-总索引-四篇论文|四篇论文总索引]]

---

## 📦 各篇精读产出

### (1) CCFA-Net · [[paper-notes/论文精读/1-CCFA-Net精读/00-索引 MOC|索引 MOC]]

| 轨道 | 内容 | 篇数 |
|---|---|---|
| 🧱 公共基础知识 | 技术地基（卷积/padding/池化/感受野/PixelShuffle/注意力/FPN/激活/梯度/损失/ResNet/检测/mAP/两阶段/单阶段/COCO/置信度/优化器） | 18 |
| 🗺️ 方向知识脉络 | 技术地图（复原谱系/恶劣天气/域适应/多任务/注意力/UAV 特性/检测谱系/遥感基础） | 9 |
| 📄 CCFA-Net 论文精读 | 本文专属（速览 + 12 讲 + 3 附录） | 17 |

### (2) Cross-Modal Object Detection via UAV · [[paper-notes/论文精读/2-Cross-Modal-UAV精读/00-索引 MOC|索引 MOC]]

| 产物 | 说明 |
|---|---|
| [[paper-notes/论文精读/2-Cross-Modal-UAV精读/01-论文速览\|论文速览]] | 问题、方案对比、三个创新点 |
| [[paper-notes/论文精读/2-Cross-Modal-UAV精读/02-第1讲-知识蒸馏与模态鸿沟\|第1讲 · KD 与模态鸿沟]] | 全文最大知识空白 |
| [[paper-notes/论文精读/2-Cross-Modal-UAV精读/03-第2讲-基线与旋转框检测\|第2讲 · Oriented R-CNN]] | 旋转框为什么必要 |
| [[paper-notes/论文精读/2-Cross-Modal-UAV精读/04-第3讲-SFI选择性特征模仿\|第3讲 · SFI]] | 创新点①（共性/残差分解） |
| [[paper-notes/论文精读/2-Cross-Modal-UAV精读/05-第4讲-API自适应预测模仿\|第4讲 · API]] | 创新点②（IoU 信任度旋钮） |
| [[paper-notes/论文精读/2-Cross-Modal-UAV精读/06-第5讲-总目标训练流程与部署\|第5讲 · 训练与部署]] | Algorithm 1 + 部署删什么 |
| [[paper-notes/论文精读/2-Cross-Modal-UAV精读/07-第6讲-实验设置与主结果解读\|第6讲 · 主结果]] | Table III 怎么读 |
| [[paper-notes/论文精读/2-Cross-Modal-UAV精读/08-第7讲-消融与定性结果精读\|第7讲 · 消融]] | Fig.5/6/7 + Fig.4 定性 |
| [[paper-notes/论文精读/2-Cross-Modal-UAV精读/09-第8讲-批判性评价与可做选题\|第8讲 · 批判与选题]] | 七条批评 + 八个方向 |
| [[paper-notes/论文精读/2-Cross-Modal-UAV精读/10-附录-公式速查手册\|公式速查]] | 14 条公式 |
| [[paper-notes/论文精读/2-Cross-Modal-UAV精读/11-附录-术语表与自测题库\|术语表 + 自测题]] | 16 题 |
| [[paper-notes/论文精读/2-Cross-Modal-UAV精读/附件/Cross-Modal-UAV-论文汇报.pptx\|汇报 PPT]] | 19 页，含演讲者备注 |

### (3) HazyDet · [[paper-notes/论文精读/3-HazyDet精读/00-索引 MOC|索引 MOC]]

| 产物 | 说明 |
|---|---|
| [[paper-notes/论文精读/3-HazyDet精读/01-论文速览\|论文速览]] | 数据集定位、规模表、与 CCFA-Net 的关系 |
| [[paper-notes/论文精读/3-HazyDet精读/02-数据集构成与标注格式\|数据集构成与标注格式]] | 合成雾流程、COCO JSON、bbox 转换、丢弃规则 |
| [[paper-notes/论文精读/3-HazyDet精读/03-深度标注与被浪费的多模态线索\|深度标注与被浪费的多模态线索]] | ★ 深度 / SiLog / DeCoDet 头 / CCFA-Net 的缺口 |
| [[paper-notes/论文精读/3-HazyDet精读/04-复现必查项与坑\|复现必查项与坑]] | ★ 5 个坑 + 上手清单 + 对账表 |

### (4) 跨域高光谱 · [[paper-notes/论文精读/4-跨域高光谱精读/00-索引 MOC|索引 MOC]]

| 产物 | 说明 | 状态 |
|---|---|---|
| [[paper-notes/论文精读/4-跨域高光谱精读/01-论文速览\|论文速览]] | 真实三贡献 / DG vs UDA / 与经典方法的关系 | ✅ 已重写 |
| [[paper-notes/论文精读/4-跨域高光谱精读/02-第1讲-域偏移三大来源与光谱分辨率\|第1讲 · 域偏移与光谱分辨率]] | HSI 入门地基 | ✅ 保留 |
| [[paper-notes/论文精读/4-跨域高光谱精读/03-第2讲-多模态与跨域的辨析\|第2讲 · 多模态 vs 跨域]] | 概念辨析 | ✅ 保留 |
| [[paper-notes/论文精读/4-跨域高光谱精读/04-第3讲-张量预备知识\|第3讲 · 张量预备知识]] | Kronecker / Khatri-Rao / Hadamard | ✅ 保留 |
| [[paper-notes/论文精读/4-跨域高光谱精读/05-第4讲-JVC联合变量一致性\|第4讲 · JVC]] | 联合变量 + 互信息 + 变分下界 + KDE | ✅ 已重写 |
| [[paper-notes/论文精读/4-跨域高光谱精读/06-第5讲-ASI锚点结构不变性\|第5讲 · ASI]] | 动态簇锚点 + 压缩锚图 | ✅ 已重写 |
| [[paper-notes/论文精读/4-跨域高光谱精读/07-第6讲-DBFDF双分支骨干网络\|第6讲 · DBFDF 骨干]] | 双分支解耦与融合 | ✅ 已重写 |
| [[paper-notes/论文精读/4-跨域高光谱精读/08-第7讲-实验结果与消融\|第7讲 · 实验与消融]] | 真实基准 + 读表方法论 | ✅ 已重写 |
| [[paper-notes/论文精读/4-跨域高光谱精读/09-第8讲-批判性评价与可做选题\|第8讲 · 批判与选题]] | 6 条批评 + 6 个选题 | ✅ 已重写 |
| [[paper-notes/论文精读/4-跨域高光谱精读/10-附录A-公式速查手册\|附录A · 公式速查]] | 11 条公式 + 可靠度标注 | ✅ 已重写 |
| [[paper-notes/论文精读/4-跨域高光谱精读/11-附录B-复现清单与实验设计\|附录B · 复现清单]] | 协议 + 超参 + 6 个坑 | ✅ 已重写 |
| [[paper-notes/论文精读/4-跨域高光谱精读/12-附录C-自测题库\|附录C · 自测题]] | 23 题 + 折叠答案 | ✅ 已重写 |

---

## 🔗 其它入口

- [[paper-notes/论文精读/00-总索引-四篇论文|四篇论文总索引]] —— **主索引**（目录结构 + 互链图 + 选题线索）
- [[TVT_UAV_跨场景泛化与感知友好去雾_研究方案|TVT_UAV 研究方案]] —— 课题方向文档（未编号）
- [[paper-notes/README|README]] —— 仓库说明

---

**索引 →** 本页 ｜ **主索引 →** [[paper-notes/论文精读/00-总索引-四篇论文|四篇论文总索引]]
