---
tags: [MOC, 阅读清单, 入口]
aliases: [索引, 阅读清单, MOC]
created: 2026-11-04
status: 进行中
---

# 📚 五篇论文 · 阅读清单（入口）

> [!info] 主入口已迁移
> 本页现在是**跳转页**。
> 👉 **主索引** → [[paper-notes/论文精读/00-总索引-五篇论文|五篇论文总索引]]

---

## 📋 阅读清单

| # | 论文 | 角色 | 索引 |
|---|---|---|---|
| **0** | **📚 公共基础知识**（39 篇） | 地基 | [[paper-notes/论文精读/0-公共基础知识/00-公共知识总览\|00-公共知识总览]] |
| **1** | CCFA-Net: Cross-domain collaborative and foreground-aware for UAV object detection in hazy scenes | 背景 + baseline | [[paper-notes/论文精读/1-CCFA-Net精读/00-索引 MOC\|00-索引 MOC]] · [[paper-notes/论文精读/1-CCFA-Net精读/README\|详细索引]] |
| **2** | Cross-Modal Object Detection via UAV ([DOI](https://doi.org/10.1109/TVT.2023.3262129)) | 方法 | [[paper-notes/论文精读/2-Cross-Modal-UAV精读/00-索引 MOC\|00-索引 MOC]] |
| **3** | HazyDet: Open-Source Benchmark for Drone-View Object Detection With Depth Cues in Hazy Scenes | 数据 | [[paper-notes/论文精读/3-HazyDet精读/00-索引 MOC\|00-索引 MOC]] |
| **4** | Cross-Domain Hyperspectral Image Generalization Based on Joint Variable Consistency and Anchor Structure Invariance<br>[IEEE TGRS 2026, DOI 10.1109/TGRS.2026.3710332](https://doi.org/10.1109/TGRS.2026.3710332) | 理论 | [[paper-notes/论文精读/4-跨域高光谱精读/00-索引 MOC\|00-索引 MOC]] |
| **5** | **TDRE**: Bridging the domain gap: A transferable dynamic routing enhancer for robust aerial detection under adverse weather<br>[ISPRS JPRS 2026, DOI 10.1016/j.isprsjprs.2026.08.041](https://doi.org/10.1016/j.isprsjprs.2026.08.041) | **方法主线**（研究计划的方法起点） | [[paper-notes/论文精读/5-TDRE精读/00-索引 MOC\|00-索引 MOC]] |
| **M** | 📚 **文献地图 · 四层优先级**（基线 / 创新支撑 / 域泛化专项 / 补充） | **路线图** | [[文献地图-四层优先级\|文献地图]] |
| **N** | 📖 **新增待精读文献**（DehazeFormer · FDD · UDN · FriendNet · CSDA · AOD-Net） | **待读清单** | [[paper-notes/论文精读/6-新增待精读文献/00-索引 MOC\|00-索引 MOC]] |
| **6** | 📐 **图论综合应用报告**：基于图论的重庆大学虎溪校区快递配送路径优化研究 | 独立课题 | [[paper-notes/图论综合应用报告/00-索引 MOC\|00-索引 MOC]] |
| **P** | 📋 **雾天 UAV 小目标检测 · 可靠性引导跨场景域泛化**（TDRE 动态增强主线 · 先复现、再诊断、后创新 · 严格 DG 协议） | **执行总纲（权威版）** | [[TDRE面向雾天无人机小目标检测的可靠性引导跨场景域泛化研究-\|研究计划 · 权威版]] |

> 📌 五篇**统一放在** `paper-notes/论文精读/` 下，按 **1 / 2 / 3 / 4 / 5** 编号排序。
> 🗺️ **不知道该读哪篇 → 看 [[文献地图-四层优先级|四层优先级文献地图]]**（含精读模板与五阶段排期）。
> 目录结构、互链关系、选题线索 → [[paper-notes/论文精读/00-总索引-五篇论文|五篇论文总索引]]

---

## 📐 图论轨（独立课题）

| 产物 | 说明 |
|---|---|
| [[paper-notes/图论综合应用报告/00-索引 MOC\|图论综合应用报告 · 索引 MOC]] | 🗺️ 主索引（题目：基于图论的重庆大学虎溪校区快递配送路径优化研究） |
| [[01-研究方案与建模思路\|研究方案与建模思路]] | 题目怎么定的、约束、算法路线、课程硬性要求 |
| [[03-图论算法速查（复习版）\|图论算法速查（复习版）]] | 用报告实例复述 Dijkstra / TSP / 2-opt / Held–Karp |
| [[04-实验结果速览\|实验结果速览]] | 5 组实验的关键数字与图 |
| [[05-数据核验清单\|数据核验清单]] | ⚠️ 待办：实地量测边长与坐标 |
| 公共知识已提上来 | [[01-图论算法速查\|图论算法速查]] · [[02-图论建模套路-从真实地图到加权图\|图论建模套路]] |

---

## 📦 各篇精读产出

### (0) 📚 公共基础知识 · [[paper-notes/论文精读/0-公共基础知识/00-公共知识总览|总览]]

| 主题目录 | 内容 | 篇数 |
|---|---|---|
| 01 · 图像与卷积基础 | 卷积/padding/池化/感受野/PixelShuffle/空间注意力/激活函数 | 7 |
| 02 · 骨干网络与特征融合 | ResNet / ResNet50 分层冻结 / FPN / 检测器三段式与创新落点 / **MoE 与动态路由** | 6 |
| 03 · 训练与优化 | 深度监督三件套与 SiLog / 梯度下降 / 损失函数 / 优化器与学习率策略 | 4 |
| 04 · 检测任务与评测 | bbox / 目标检测与 mAP / 两阶段 / 单阶段与样本分配 / 置信度与质量感知 | 5 |
| 05 · 数据标注与协议 | COCO 与评测标准 / train-val-test 与 pipeline / 标注文件与 gt | 3 |
| 06 · 模型压缩与跨模态 | 模型压缩全景 / 知识蒸馏详解 / 跨模态技术全景 | 3 |
| 07 · 方向知识脉络 | 复原谱系 / 恶劣天气 / DA-DG-TTA / 多任务 / 注意力 / UAV 特性 / 检测谱系 / 遥感基础 | 9 |
| 09 · 域泛化与不变学习 | MMD / GRL / IRM / 偏移三分类（JVC · ASI 的机制底座） | 1 |

### (1) CCFA-Net · [[paper-notes/论文精读/1-CCFA-Net精读/00-索引 MOC|索引 MOC]]

| 轨道 | 内容 | 篇数 |
|---|---|---|
| 🧱 公共基础知识 | **已提到 `0-公共基础知识/`**（卷积/FPN/ResNet/检测/mAP/优化器…） | 18（共享） |
| 🗺️ 方向知识脉络 | **已提到 `0-公共基础知识/07-方向知识脉络/`**（复原谱系/恶劣天气/域适应/多任务/注意力/UAV 特性/检测谱系/遥感基础） | 9（共享） |
| 📄 CCFA-Net 论文精读 | 本文专属（速览 + 12 讲 + 4 附录），在 `1-CCFA-Net精读/01-论文精读/` | 18 |
| 🔁 公共知识回顾 | **本篇用到的公共基础（复述版）** | 1 |

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
| [[paper-notes/论文精读/2-Cross-Modal-UAV精读/13-公共知识回顾\|公共知识回顾]] | ★ 本篇用到的公共基础（蒸馏 / 跨模态 / 检测评测）**复述版** |

### (3) HazyDet · [[paper-notes/论文精读/3-HazyDet精读/00-索引 MOC|索引 MOC]]

| 产物 | 说明 |
|---|---|
| [[paper-notes/论文精读/3-HazyDet精读/01-论文速览\|论文速览]] | 数据集定位、规模表、与 CCFA-Net 的关系 |
| [[paper-notes/论文精读/3-HazyDet精读/02-数据集构成与标注格式\|数据集构成与标注格式]] | 合成雾流程、COCO JSON、bbox 转换、丢弃规则 |
| [[paper-notes/论文精读/3-HazyDet精读/03-深度标注与被浪费的多模态线索\|深度标注与被浪费的多模态线索]] | ★ 深度 / SiLog / DeCoDet 头 / CCFA-Net 的缺口 |
| [[paper-notes/论文精读/3-HazyDet精读/04-复现必查项与坑\|复现必查项与坑]] | ★ 5 个坑 + 上手清单 + 对账表 |
| [[paper-notes/论文精读/3-HazyDet精读/05-DeCoDet原理精读\|DeCoDet原理精读]] | ★★ MSDP / DCK / SIRLoss 公式、消融表、论文 vs 代码 |
| [[paper-notes/论文精读/3-HazyDet精读/06-PDFT渐进域微调精读\|PDFT渐进域微调精读]] | ★★ **训练策略侧**：§4.2 两阶段域微调、Algorithm 1 逐行、真实域 +10.0、官方零实现 |
| [[paper-notes/论文精读/3-HazyDet精读/07-实验部分精读\|实验部分精读]] | ★★ **实验侧**：§5.1 实现细节对账 / Tab.3 逐列拆解 / Tab.4 消融逐行读 / Tab.5 去雾对比 |
| [[paper-notes/论文精读/3-HazyDet精读/09-实验部分总结\|实验部分总结]] | ★★ **实验一页速查卡**：三条核心发现 + 复现决策 |
| [[paper-notes/论文精读/3-HazyDet精读/08-公共知识回顾\|公共知识回顾]] | ★ 本篇用到的公共基础**复述版** |
| [[paper-notes/论文精读/0-公共基础知识/00-公共知识总览\|公共基础知识总览]] | ★ 通用地基（已提到 `0-公共基础知识/`）：bbox / train-val-test / 标注文件与 gt |

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
| [[paper-notes/论文精读/4-跨域高光谱精读/13-公共知识回顾\|公共知识回顾]] | ★ 本篇用到的公共基础（高光谱张量 / DA-DG-TTA / 遥感基础）**复述版** | ✅ 新增 |
| [[paper-notes/论文精读/4-跨域高光谱精读/14-第9讲-架构图逐块解析\|第9讲 · 架构图逐块解析]] | DBFDF 双分支 + JVC + ASI 的**张量级**拆解 | ✅ 新增 |

---

### (5) TDRE · [[paper-notes/论文精读/5-TDRE精读/00-索引 MOC|索引 MOC]]

| 产物 | 说明 |
|---|---|
| [[paper-notes/论文精读/5-TDRE精读/01-论文速览\|论文速览]] | 问题 / 三大贡献 / 与前四篇的关系 / 核心数字 |
| [[paper-notes/论文精读/5-TDRE精读/02-第1讲-问题定义与两个陷阱\|第1讲 · 两个陷阱]] | 灾难性遗忘 + human-visual bias 的机制级拆解 + **与第 1 篇 Lipschitz 的对照** |
| [[paper-notes/论文精读/5-TDRE精读/03-第2讲-三阶段架构与清晰天感知器\|第2讲 · 三阶段架构与清晰天感知器]] | 式 (1)(2)(3) + 硬门控 + Sca 阈值 Table 7 + **参数账反推** |
| [[paper-notes/论文精读/5-TDRE精读/04-第3讲-DR-MoE动态路由专家\|第3讲 · DR-MoE]] | 式 (4)(5)(6)(7)(8) + **Top-3 routing 的真相** + 大气先验 |
| [[paper-notes/论文精读/5-TDRE精读/05-第4讲-协同优化与任务对齐\|第4讲 · 协同优化]] | 式 (9)–(14) + MSR 三色彩空间 + **DE 掩码损失** + Table 4/5 |
| [[paper-notes/论文精读/5-TDRE精读/06-第5讲-数据集CAD-ADD与实验结果\|第5讲 · CAD-ADD 与实验]] | Table 1–10 逐表精读 + **126.9 口径核对** + 复现必查项 |
| [[paper-notes/论文精读/5-TDRE精读/07-第6讲-批判性评价与可做选题\|第6讲 · 批判与选题]] | 7 条批评 + **7 个可做选题**（含与第 1 篇缝合的方案） |
| [[paper-notes/论文精读/5-TDRE精读/08-附录A-公式速查手册\|附录A · 公式速查]] | 14 条公式（带可靠度标注）+ **12 项复现空缺清单** |
| [[paper-notes/论文精读/5-TDRE精读/09-附录B-自测题库\|附录B · 自测题库]] | 24 题 + 折叠答案 + 成绩自评表 |
| [[paper-notes/论文精读/5-TDRE精读/附件/TDRE-论文原文.pdf\|📄 论文 PDF 原文]] | 18 页原文存档 |

## 🔗 其它入口

- [[paper-notes/论文精读/00-总索引-五篇论文|五篇论文总索引]] —— **主索引**（目录结构 + 互链图 + 选题线索 + **检测器三段式与五篇落点**）
- [[TVT_UAV_跨场景泛化检测_研究方案|TVT_UAV 研究方案]] —— 课题方向文档（未编号）
- [[TDRE面向雾天无人机小目标检测的可靠性引导跨场景域泛化研究-|雾天 UAV 可靠性引导跨场景域泛化]] —— **当前研究执行总纲 · 权威版**（方法路线与科学问题；P0–P3 与 8 周排期见 [[UAV_Research_Plan_Refined_CCFA_TDRE|UAV_Research_Plan_Refined_CCFA_TDRE]]）
- [[paper-notes/论文精读/README|README]] —— 仓库说明

---

**索引 →** 本页 ｜ **主索引 →** [[paper-notes/论文精读/00-总索引-五篇论文|五篇论文总索引]]
