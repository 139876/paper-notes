---
track: 论文精读
tags: [DehazeFormer, 去雾, TIP, 待精读, 对照基线]
aliases: [DehazeFormer]
created: 2026-11-24
updated: 2026-11-24
related: ["[[00-索引 MOC]]", "[[paper-notes/论文精读/文献地图-四层优先级]]", "[[paper-notes/论文精读/0-公共基础知识/07-方向知识脉络/01-图像复原谱系-从DCP到DehazeFormer]]"]
status: 待精读 · 🔴 第一层
---

## 📎 原文与存档

- 📄 **论文 PDF 原文** → [[paper-notes/论文精读/6-新增待精读文献/附件/DehazeFormer-论文原文.pdf|DehazeFormer 原文 PDF]]（arxiv:2204.03883）
- 📝 **全文纯文本** → [[paper-notes/论文精读/6-新增待精读文献/附件/DehazeFormer-全文文本.txt|DehazeFormer 全文文本]]（方便全文检索 / 摘抄）


# 01 · DehazeFormer

*Transformer-Based Feature Learning for Image Dehazing* · **TIP 2023**
[官方代码](https://github.com/IDKiro/DehazeFormer)

---

## 一句话定位

**独立去雾基线**，用来回答你方向一的第一个问题：**「图像变清晰」是否一定有利于小目标检测**。

---

## 精读重点

- [ ] 多尺度特征是怎么组织的
- [ ] Transformer 结构（哪几个模块、放在哪一级）
- [ ] 去雾的**推理流程**（训练时用了什么、推理时需要什么）
- [ ] **去雾输出与检测器的串联方式** ← 最关键，直接决定你的对照实验怎么搭

---

## 与我的研究关系

| 维度 | 判断 |
|---|---|
| 能不能复现 | ✅ 能，官方开源，作为**对照基线**必须有 |
| 能不能改 | ⚠️ 可以，但你的创新不在去雾网络结构上 |
| 能不能当创新 | ❌ 不能，TIP 2023 已发表 |

> [!tip] 它在你的实验矩阵里的位置
> 三组对照：**原始雾图** / **DehazeFormer 去雾图** / **联合检测（CCFA-Net 式）**
> → 这是第 3 阶段的**核心实验**，也是你「恢复信息未必可靠」这一立论的**第一块证据**。

---

## 复现清单

- [ ] 拉代码、跑通官方预训练权重推理
- [ ] 在 HazyDet 上生成去雾图（记录雾浓度 / 场景分组）
- [ ] 接入 HazyDet 检测器，测 AP / AP_small
- [ ] **重点记录**：小目标 + 远距离 + 浓雾区域，去雾后 AP 是升还是降
- [ ] 保存异常样本截图（去雾后纹理崩坏但检测反而变好的）

---

## 相关笔记

- [[paper-notes/论文精读/0-公共基础知识/07-方向知识脉络/01-图像复原谱系-从DCP到DehazeFormer|图像复原谱系（含 DehazeFormer）]]
- [[paper-notes/论文精读/1-CCFA-Net精读/01-论文精读/10-第9讲-数据集与实验设置|第 9 讲 · 数据集与实验设置]]

**返回** → [[00-索引 MOC]]
