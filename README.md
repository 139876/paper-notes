# 📑 CCFA-Net 精读笔记

> 无人机在大雾天飞，画面像隔着一层毛玻璃。旧做法是「**先擦玻璃再找车**」，
> 但擦玻璃的工艺（追求平滑、像素级还原）和找车的工艺（需要放大微小差别）**性格相反**。

对 ISPRS JPRS 2026 论文 **CCFA-Net** 的系统性精读笔记，共 14 篇，覆盖领域知识补齐、
逐模块拆解、批判性评价与复现清单。

📖 从 [00-索引 MOC](00-%E7%B4%A2%E5%BC%95 MOC.md) 开始阅读。

---

## 📄 论文信息

| 项 | 内容 |
|---|---|
| 标题 | CCFA-Net: Cross-domain collaborative and foreground-aware for UAV object detection in hazy scenes |
| 作者 | Feng Xie, Yuanyuan Li, Zhiqin Zhu, Penglong Li, Xin Huang, Yiyao An |
| 单位 | 重庆邮电大学 + 重庆市测绘遥感中心 |
| 期刊 | ISPRS J. Photogrammetry & Remote Sensing, **236** (2026) 552–568 |
| DOI | [10.1016/j.isprsjprs.2026.04.020](https://doi.org/10.1016/j.isprsjprs.2026.04.020) |
| 官方代码 | <https://github.com/XFCV26/CCFA-Net> |
| 状态 | Received 2025-11-23 · Accepted 2026-04-08 · Online 2026-04-13 |

## ⚡ 三句话抓住全文

1. **像素级的好看 ≠ 任务级的有用。** 去雾指标涨了，检测反而跌——这是全文的立身之本。
2. **把辅助任务「降格」为正则化约束**，而不是让它当上游工序。CCDD 不交出图像，只交出特征 + 一份约束。
3. **不要盲信论文的效率表。** 参数量能验算通过，FLOPs 差 3.6 倍——**复现第一步是量，不是训**。

## 🗺️ 阅读路线

| 阶段 | 笔记 | 说明 |
|---|---|---|
| 阶段零 · 建立直觉（30 min） | [01-论文速览](01-%E8%AE%BA%E6%96%87%E9%80%9F%E8%A7%88.md) | 三类策略为什么全都不行 |
| 阶段一 · 补齐领域知识 | [02-第1讲-去雾物理模型与DCP](02-%E7%AC%AC1%E8%AE%B2-%E5%8E%BB%E9%9B%BE%E7%89%A9%E7%90%86%E6%A8%A1%E5%9E%8B%E4%B8%8EDCP.md) | ★ 必读 · 补本文最大空白 |
| 阶段一 | [03-第2讲-架构张量尺寸逐层推导](03-%E7%AC%AC2%E8%AE%B2-%E6%9E%B6%E6%9E%84%E5%BC%A0%E9%87%8F%E5%B0%BA%E5%AF%B8%E9%80%90%E5%B1%82%E6%8E%A8%E5%AF%BC.md) | ★ 必读 · 逐层 shape 对齐 |
| 阶段一 | [04-第3讲-Lipschitz不匹配](04-%E7%AC%AC3%E8%AE%B2-Lipschitz%E4%B8%8D%E5%8C%B9%E9%85%8D.md) | ★ 论文的理论卖点 |
| 阶段一 | [05-第4讲-多任务损失与梯度冲突](05-%E7%AC%AC4%E8%AE%B2-%E5%A4%9A%E4%BB%BB%E5%8A%A1%E6%8D%9F%E5%A4%B1%E4%B8%8E%E6%A2%AF%E5%BA%A6%E5%86%B2%E7%AA%81.md) | ★ 论文没讲但你必须懂 |
| 阶段一 | [06-第5讲-评价指标与复现必查项](06-%E7%AC%AC5%E8%AE%B2-%E8%AF%84%E4%BB%B7%E6%8C%87%E6%A0%87%E4%B8%8E%E5%A4%8D%E7%8E%B0%E5%BF%85%E6%9F%A5%E9%A1%B9.md) | ★ 含 GFLOPs 质疑 |
| 阶段二 · 研究者视角 | [07-第6讲-批判性评价与可做选题](07-%E7%AC%AC6%E8%AE%B2-%E6%89%B9%E5%88%A4%E6%80%A7%E8%AF%84%E4%BB%B7%E4%B8%8E%E5%8F%AF%E5%81%9A%E9%80%89%E9%A2%98.md) | ★ 找选题从这里开始 |
| 专项精讲 | [11-补充-DCP假设3精讲](11-%E8%A1%A5%E5%85%85-DCP%E5%81%87%E8%AE%BE3%E7%B2%BE%E8%AE%B2.md) | DCP 心脏 / 黑电平标定类比 |
| 专项精讲 | [12-第7讲-CCDD结构精讲](12-%E7%AC%AC7%E8%AE%B2-CCDD%E7%BB%93%E6%9E%84%E7%B2%BE%E8%AE%B2.md) | ★★ 核心模块 · 双出口逻辑 |
| 专项精讲 | [13-第8讲-PixelShuffle与上采样vs采样](13-%E7%AC%AC8%E8%AE%B2-PixelShuffle%E4%B8%8E%E4%B8%8A%E9%87%87%E6%A0%B7vs%E9%87%87%E6%A0%B7.md) | ★ 上采样 vs 采样 概念澄清 |
| 附录 | [08-附录-公式速查手册](08-%E9%99%84%E5%BD%95-%E5%85%AC%E5%BC%8F%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md) | 公式速查 |
| 附录 | [09-附录-复现清单与实验设计](09-%E9%99%84%E5%BD%95-%E5%A4%8D%E7%8E%B0%E6%B8%85%E5%8D%95%E4%B8%8E%E5%AE%9E%E9%AA%8C%E8%AE%BE%E8%AE%A1.md) | 复现 checklist |
| 附录 | [10-附录-自测题库](10-%E9%99%84%E5%BD%95-%E8%87%AA%E6%B5%8B%E9%A2%98%E5%BA%93.md) | 自测题 |

## 📊 核心数字速查

| 数据集 / 项目 | 数值 | 说明 |
|---|---|---|
| HazyDet mAP | **54.6%** | 主结果，超 DeCoDet **+3.1** |
| Car / Truck / Bus AP | 62.2 / 37.5 / 64.2 | Truck 最低（长尾） |
| vs Direct 最优 NIRNet | +5.1 | 49.5 → 54.6 |
| vs Separate 最优 DehazeFormer | **+10.5** | 44.1 → 54.6，Separate 全线垫底 |
| RDDTS（真实，零微调） | **28.7%** | 超 DeCoDet +2.8；全行业仅 22–29% |
| VisDrone-Hazy | 42.6% | 超 DeCoDet +3.9 |
| DroneVehicle | 27.7% | 超 DeCoDet +1.5，零重训 |
| VOChaze（地面场景） | 60.9% | 超 DeCoDet +6.2 |
| 消融 基线 → 全模型 | 50.8 → **54.6** | 三模块有**超线性协同** |
| Params / GFLOPs / FPS | 36.61M / 193.72G / 47.6 | ⚠️ GFLOPs 存疑，见 06-第5讲 |
| 训练配置 | TOOD+R50, SGD, 24ep, lr 0.01, bs 2, λ=0.5 | RTX 4090，输入 1333×800 |

## 📁 目录结构

```
obsidian-CCFA-Net精读/
├── 00-索引 MOC.md          # 总索引 / 阅读路线 / 核心数字
├── 01-论文速览.md
├── 02 ~ 07                # 第 1~6 讲：领域知识与批判性评价
├── 08 ~ 10                # 附录：公式速查 / 复现清单 / 自测题库
├── 11 ~ 13                # 补充与专项精讲
└── 附件/                  # 4 张示意图（PNG）
```

## ⚙️ 关于这些笔记

笔记用 [Obsidian](https://obsidian.md) 撰写，因此使用了它的专有语法：

- **双链** `[[02-第1讲-去雾物理模型与DCP]]` —— 在 Obsidian 里可点击跳转
- **嵌入** `![[附件/fig1_strategies.png]]` —— 图片嵌入
- **Callout** `> [!question]` —— 提示框
- **块级公式** `$$...$$` —— GitHub 原生支持，可直接渲染

在 Obsidian 中阅读体验最佳；在 GitHub 网页端，公式、表格、代码块正常，
而双链与图片会显示为原始文本（可用转换脚本自动处理）。

---

📌 本仓库为个人学习笔记，仅供学习交流。论文版权归原作者所有。
