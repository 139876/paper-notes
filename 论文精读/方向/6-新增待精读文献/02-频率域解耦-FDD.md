---
track: 论文精读
tags:
  - 域泛化
  - CVPR2023
  - UAV检测
  - 频率域
  - 待精读
aliases:
  - FDD
  - Frequency Domain Disentanglement
  - 频率域解耦
created: 2026-11-24
updated: 2026-11-25
related:
  - "[[paper-notes/论文精读/方向/6-新增待精读文献/00-索引 MOC]]"
  - "[[文献地图-四层优先级]]"
  - "[[paper-notes/论文精读/0-公共基础知识/09-域泛化与不变学习/01-域泛化机制精讲-MMD-GRL-IRM与偏移三分类]]"
status: 待精读 · ⚪ 第三层 · 条件触发
---

## 📎 原文与存档

- 📄 **论文 PDF 原文** → [[FDD-论文原文.pdf|FDD 原文 PDF]]（CVPR 2023）
- 📝 **全文纯文本** → [[FDD-论文正文-全文文本.txt|FDD 全文文本]]（方便全文检索 / 摘抄）


# 02 · Generalized UAV Object Detection via Frequency Domain Disentanglement

**CVPR 2023** · [CVPR 官方页面](https://openaccess.thecvf.com/content/CVPR2023/html/Wang_Generalized_UAV_Object_Detection_via_Frequency_Domain_Disentanglement_CVPR_2023_paper.html)

---

## 一句话定位

**严格域泛化的基线 + 实验协议范本**：直接研究 UAV 检测在**未见真实场景**中的泛化。

---

## 精读重点

- [ ] 域不变频谱（domain-invariant）怎么定义、怎么解耦
- [ ] 域特定频谱（domain-specific）保留了什么
- [ ] **实例级对比损失**的构造与作用
- [ ] **三个未见目标域的划分方式** ← 直接抄进你的实验协议

---

## 与我的研究关系

| 维度 | 判断 |
|---|---|
| 能不能复现 | ✅ 能，作为**域泛化对照基线**必须有 |
| 能不能改 | ✅ 可以往里加类别—尺度条件、恢复可靠性约束 |
| 能不能当创新 | ❌ 不能，CVPR 2023 已发表 |

> [!tip] 它给你的是**方法工具 + 实验纪律**
> - **工具**：频域解耦可以作为你「域不变特征」的备选实现路径
> - **纪律**：它怎么定义「未见场景」，你就要怎么定义——否则你的泛化结论不可信

---

## 复现清单

- [ ] 抄下它的**域划分表**（源域 → 目标域），对照你的场景划分
- [ ] 检查它的域划分有没有**场景泄漏**
- [ ] 跑通后在你的 HazyDet 划分上复现一遍
- [ ] 对比：CCFA-Net 的跨域实验 vs 它的严格 DG —— **谁更严格**
- [ ] 写清楚你的「未见场景」定义（地点 / 飞行高度 / 雾浓度，三个维度分别怎么切）

---

## 相关笔记

- [[paper-notes/论文精读/0-公共基础知识/09-域泛化与不变学习/01-域泛化机制精讲-MMD-GRL-IRM与偏移三分类|域泛化机制精讲]]
- [[paper-notes/论文精读/0-公共基础知识/07-方向知识脉络/03-域适应域泛化与测试时适应|域适应域泛化与测试时适应]]
- [[paper-notes/论文精读/UAV_Research_Plan_Refined_CCFA_TDRE|UAV 研究方案（Refined）]]

**返回** → [[paper-notes/论文精读/方向/6-新增待精读文献/00-索引 MOC]]
