---
track: 论文精读
tags:
  - FriendNet
  - 感知友好去雾
  - 检测友好
  - 撤稿
  - 待精读
aliases:
  - FriendNet
  - Detection-Friendly Dehazing Network
created: 2026-11-24
updated: 2026-11-25
related:
  - "[[paper-notes/论文精读/6-新增待精读文献/00-索引 MOC]]"
  - "[[文献地图-四层优先级]]"
  - "[[paper-notes/论文精读/1-CCFA-Net精读/00-索引 MOC]]"
status: ⚠️ 已撤稿 · 仅作思路参考 · 第二层 · 创新候选二对照
---

# 04 · FriendNet（Detection-Friendly Dehazing Network）

**2024 · arXiv 2403.04443** · [论文主页](https://arxiv.org/abs/2403.04443) · [官方代码](https://github.com/fanyihua0309/FriendNet)

## 📎 原文与存档

- 📄 **论文 PDF 原文** → [[FriendNet-论文原文.pdf|FriendNet 原文 PDF（v1）]]
- 📝 **全文纯文本** → [[FriendNet-论文正文-全文文本.txt|FriendNet 全文文本]]

> [!danger] ⚠️ 该论文已被作者**主动撤稿**（arXiv:2403.04443 withdrawn，2025-04-02 修订）
> 作者原话：*「We identified a fundamental flaw in the theoretical framework of this submission, rendering the main argument unsound. To maintain academic rigor, we request withdrawal and will submit a revised version after thorough validation.」*
> **本仓库存档的是 v1（撤稿前版本）**，仅供你了解「感知友好去雾」这个思路长什么样。
> ❌ 不要引用它作为方法依据；❌ 不要在论文里当 related work 引用；✅ 只当**反面教材**读。

---

## 一句话定位

**「为检测而生的去雾」**——检测监督直接参与去雾网络优化。

---

## 精读重点

- [ ] **GFB（Guidance Fusion Block）**：检测信息怎么注入去雾网络
- [ ] **GAB（Guidance Attention Block）**：注意力引导的具体形式
- [ ] **PFEB（Physics-aware Feature Enhancement Block）**：物理先验（大气散射模型）怎么进特征
- [ ] **task-driven learning**：去雾损失 + 检测损失的**联合优化目标**怎么写
- [ ] ⚠️ **重点找「撤稿理由」**：它到底错在哪？→ 这正是你方向一要**重新做一遍**的地方

> [!important] 对你最重要的一点
> 这篇的**直觉是对的**：去雾不该只优化「人眼清晰度」，应该让**下游检测任务**来指导。
> 但它的**理论框架被作者自己判定为不成立**。
> → 你的方向一「**恢复信息可信度建模**」正好是把这个直觉**做扎实**的机会：
> 别人试过、翻车了、你能指出为什么翻车、并且给出更严谨的替代。

---

## 与我的研究关系

| 维度 | 判断 |
|---|---|
| 能不能复现 | ⚠️ 论文已撤稿，**不建议复现**；代码可跑通但结论不可信 |
| 能不能改 | ⚠️ 只能借鉴结构（GFB/GAB/PFEB），不能引用其结论 |
| 能不能当创新 | ❌ 不能（已撤稿）；且「检测引导去雾」这个想法本身也已被 CCFA-Net 做过 |

> [!tip] 它在你的实验矩阵里的位置
> **不作为对照基线**，而作为**「为什么这件事需要更严谨的可靠性建模」的论据**。
> 写 related work 时：可以用它说明「检测友好去雾」方向被尝试过，
> 但**不要**引用它支撑任何方法有效性结论。

---

## 复现清单（可选，低优先级）

- [ ] 只读 v1 原文的**模块设计**（GFB / GAB / PFEB），不看它的实验结论
- [ ] 找出它的**理论漏洞**并写成一页笔记 → 这是你方向一的**问题定义来源**
- [ ] 正式写作时**不引用**；必要时只在「已有尝试及其局限」中提及（并注明已撤稿）

---

## 相关笔记

- [[文献地图-四层优先级|四层优先级文献地图]]
- [[paper-notes/论文精读/1-CCFA-Net精读/00-索引 MOC|CCFA-Net 精读索引]]
- [[03-UDN-不确定性驱动去雾|03 · UDN（不确定性驱动去雾）]]

**返回** → [[paper-notes/论文精读/6-新增待精读文献/00-索引 MOC]]
