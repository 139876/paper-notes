---
track: 论文精读
tags: [FPD, 伪域生成, 域泛化, CVPR2021, 数据增强, 待精读]
aliases: [FPD, Frequency-based Pseudo-domain Generation, 频率伪域生成]
created: 2026-11-24
updated: 2026-11-24
related: ["[[00-索引 MOC]]", "[[paper-notes/论文精读/文献地图-四层优先级]]", "[[02-频率域解耦-FDD]]", "[[07-DIDN]]"]
status: 待精读 · 🟢 第三层
---

## 📎 原文与存档

- 📄 **论文 PDF 原文** → [[paper-notes/论文精读/6-新增待精读文献/附件/FPD-论文原文.pdf|FPD 原文 PDF]]（CVPR 2021）
- 📝 **全文纯文本** → [[paper-notes/论文精读/6-新增待精读文献/附件/FPD-全文文本.txt|FPD 全文文本]]（方便全文检索 / 摘抄）


# 08 · FPD（Frequency-based Pseudo-domain Generation for Domain Generalizable Object Detection）

**CVPR 2021** · [CVPR 官方页面](https://openaccess.thecvf.com/content/CVPR2021/html/Li_Frequency-Based_Pseudo-Domain_Generation_for_Domain_Generalizable_Object_Detection_CVPR_2021_paper.html)

---

## 一句话定位

**不靠模型改结构，靠「造数据」提升域泛化**：在**频域**里造出假的域，把训练分布撑开。

---

## 精读重点

- [ ] **频域伪域怎么生成的**（哪个频段？加什么扰动？）
- [ ] 伪域**标签怎么给**（检测任务里伪造域，检测标注怎么处理？）
- [ ] 生成的伪域与真实域的**相似度**怎么验证
- [ ] 它和 **MixStyle / Mixup / 风格迁移类增强**的差别在哪

---

## 与我的研究关系

| 维度 | 判断 |
|---|---|
| 能不能复现 | ✅ 能，核心是一个频域增强模块 |
| 能不能改 | ✅ 可以把「随机频域扰动」换成「**与雾浓度 / 尺度相关的定向扰动**」 |
| 能不能当创新 | ❌ 不能，但**容易变成你实验里的加分项** |

> [!tip] 最容易被忽略的一条线
> 你的方向是「**恢复可靠性约束**」，方向二是「**类别—尺度条件泛化**」。
> FPD 提供的第三条低成本路径：
> **用频域伪域扩充训练场景多样性** →
> 训练时见过更多「不同雾浓度 / 不同尺度」的组合 → 严格 DG 下的 AP 更稳。
> 它可以作为你的**训练数据增强模块**，
> 而不是核心创新点——但审稿人经常会问「为什么不加频域增强」，所以必须读过。

---

## 复现清单

- [ ] 抄下频域扰动的具体做法（频带选择 + 扰动强度）
- [ ] 在你的 HazyDet 划分上试一次，看 AP / AP_small 变化
- [ ] 对照实验：**FPD 增强 vs 你的恢复可靠性约束**，谁涨得多
- [ ] 检查有无「伪域与真实域差距过大导致负收益」的情况

---

## 相关笔记

- [[02-频率域解耦-FDD|02 · 频率域解耦（FDD）]]
- [[07-DIDN|07 · DIDN]]

**返回** → [[00-索引 MOC]]
