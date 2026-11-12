---
tags: [HazyDet, PDFT, 域适应, 微调, 域间隙, 消融实验, 复现, 研究生]
aliases: [PDFT 精读, HazyDet 4.2, 渐进域微调, Progressive Domain Fine-Tuning]
created: 2026-11-12
stage: 2 · 模型原理
series: HazyDet 精读 · 第 06 篇
related: "[[00-索引 MOC]]", "[[05-DeCoDet原理精读]]", "[[04-复现必查项与坑]]", "[[公共基础知识/04-深度监督三件套与SiLog尺度性质]]"
track: HazyDet
---

# 06 · §4.2 PDFT 渐进域微调精读

> [!abstract] 本讲要回答
> 1. §4.2 到底在解决什么问题？（合成雾 → 真实雾那 **10 个点**的断崖）
> 2. Algorithm 1 逐行怎么读？**$\theta^1$ / $\theta^{2:k}$ 的上标到底是"第几阶段训练"？**
> 3. 为什么第二阶段要**冻结**前几层 + **降学习率**？不这么做会怎样？
> 4. SIRLoss 在这一节里扮演什么角色？它和 PDFT 是一回事吗？
> 5. 🔴 **论文说的和官方代码做的，对不上**——哪些？复现时怎么补？

> [!note] 本讲定位
> §4.2 是 HazyDet 论文里**最"工程"、也最容易被跳过**的一节。
> 它不含任何新模块、不加任何参数，纯粹是**训练策略**——
> 但正是它把真实雾 mAP 从 25.6 拉到 35.6（**+10.0**），是全篇性价比最高的一招。

---

## 0. 结论先行

| 问题 | 答案 |
|---|---|
| PDFT 是什么？ | **两阶段微调**：先在合成雾上学，再在真实雾上接着学 |
| 收益多大？ | 真实域 **+10.0 mAP**（25.6 → 35.6），合成域 **+0.0**（49.5 → 49.5） |
| 加了多少参数？ | **0**。参数量 32.71M → 32.71M，GFLOPs 184.32 → 184.32 |
| 官方代码实现了吗？ | 🔴 **完全没有**。全仓库零实现，得自己手写 |
| 复现难点？ | ① 官方没代码 ② **400 张真实雾训练集没有官方 config** ③ 得懂 mmcv 的 `frozen_stages` |

> [!tip] 一句话类比
> **PDFT = "先在模拟考里刷题，再上实战考场"。**
> 直接拿真实雾（只有 400 张）去训练 → 就像不做模拟考直接上考场，见过 5 道真题就去考 200 道真题，必然崩。
> 先在 8000 张合成雾（**逐像素配对**、标注完美）上把"雾天怎么认车"学会，
> 再用**小学习率**去适应真实雾的质感差异。

---

## 1. 它要解决的病：合成雾 → 真实雾的断崖

### 1.1 病根：三个域，三种分布

论文 §4.2 第一句话就点题：

> Training a robust object detector for real-world hazy drone imagery presents a significant challenge due to the inherent discrepancies between **clear, simulated hazy, and real hazy data distributions**.

| 域 | 符号 | 是什么 | 规模 | 有什么问题 |
|---|---|---|---|---|
| 源域 | $\mathcal{D}_s$ | ImageNet 清晰自然图 | 128 万张（分类） | 域差最大：没有雾、没有无人机俯视 |
| 中间域 | $\mathcal{D}_m$ | **合成雾** HazyDet 训练集 | 8000 张 | 分布干净、可配对、但**雾的质感是假的** |
| 目标域 | $\mathcal{D}_t$ | **真实雾** | **400 张**（Table 2：Real-world Train） | 质感真，但**样本极少** |

> [!warning] 中间域为什么值得当"桥"
> 合成雾 = 清晰无人机图 + 大气散射模型（Eq.1）合成的雾。
> 所以它和清晰图**逐像素配对**，标注**完美无噪声**、数量**充足**。
> 它是"既有雾、又多、还准"的**唯一**数据源——所以当桥。

### 1.2 两种朴素做法为什么都不行

论文 Fig. S5(a) 用一张图讲清了三种策略，我把它翻译成表格：

| 策略 | 做法 | 问题 |
|---|---|---|
| **Real-data only** | 直接拿真实雾 400 张微调 | ① 域差：ImageNet→真实雾 一步跨太大 ② **样本少 → 过拟合** |
| **Syn-data only** | 只在合成雾上训 | 合成雾的雾"质感是合成的"，泛化不到真实雾 |
| **PDFT（本文）** | 合成雾 →（中间域）→ 真实雾 | ✅ 用合成雾当桥，两头问题都缓解 |

论文 Appendix B.1 原文：

> Direct fine-tuning on real-world data, however, consistently encounters severe domain shift and overfitting... In contrast, fine-tuning with simulated data leads to notable improvements... Building on this observation, our proposed PDFT method utilizes **simulated data as a bridging domain**.

### 1.3 🔍 补一个 handoff 常见误读

> [!warning] Fig. S5(b) 是**跨 17 个模型的雷达图**，不是"三种策略各一个数"
> 很多人会以为"论文给了三种策略的 mAP 对比表"——**没有**。
> Fig. S5(b) 的每一根轴是一个检测器（VFNet / ATSS / TOOD / DeCoDet / DAB-DETR …），
> 三条曲线分别是 Real-data only / Syn-data only / PDFT。
>
> 📐 **本次实测标定**（像素级测量 + 用 Table 3 的真实域 mAP 做标定集）：
> **绿色（PDFT）曲线逐轴精确对上 Table 3 的 "AP on Real-World Test-Set" 那一列**——
> 因为 §5.2 明说 Table 3 里**除 3 个雾专用模型外，其余 16 个都用了 PDFT**。
> ⇒ 绿线 = Table 3 的数字，**不是额外的新结果**。
>
> 👉 所以：**Fig. S5 能证明的只有"顺序"**（PDFT > Syn-only > Real-only，几乎所有轴都成立），
> **不能**从里面读出"PDFT 比 Real-only 高多少"这种精确差值。

---

## 2. Algorithm 1 逐行拆解

论文 Algorithm 1 原文结构（我按行注释）：

```
Require: 预训练模型 M(θ0) [来自源域 Ds], 中间域 Dm, 目标域 Dt, 学习率 η1, epochs E1,E2, 衰减 γ
Ensure:  域适应后的模型 M(θt)

 1: Stage 1: normal → simulated haze (中间域)
 2:   θm ← θ0,  冻结 θm^1 (第一段 backbone)
 3:   for epoch = 1 to E1:
 4:     for batch bm in Dm:
 5:       Lm = L_task( M(θm)(bm) )
 6:       θm \ θm^1 ← θm \ θm^1 − η1 · ∇Lm
 7:     end
 8:   end
 9:   中间域模型: M(θm)

10: Stage 2: simulated → real haze (目标域)
11:   θt ← θm,  冻结 {θt^1, θt^{2:k}} (第一段 & 中间几段)
12:   η2 = η1 · γ   (γ < 1)
13:   for epoch = 1 to E2:
14:     for batch bt in Dt:
15:       Lt = L_task( M(θt)(bt) )
16:       θt \ {θt^1, θt^{2:k}} ← ... − η2 · ∇Lt
17:     end
18:   end
19:   return M(θt)
```

### 2.1 🔥 最容易读错的一点：上标 ≠ 训练阶段

> [!danger] **$\theta^1$ / $\theta^{2:k}$ 的上标是 "backbone 的第几段"，不是"第几阶段训练"**
>
> 论文 Algorithm 1 的 Requirement 写的是：
> `Pre-trained model M(θ0) from source Ds`
> 而第 2 行 `Initialize θm ← θ0` —— **θ0 是一个整体模型**，
> 但第 2 行又说要"冻结 $\theta_m^1$（第一段 backbone）"。
>
> ⇒ 所以 $\theta^1, \theta^2, \theta^3, \theta^4$ 指的是 **ResNet 的 stage1~stage4**，
> **不是** "Stage 1 / Stage 2 训练"。
> 算法里的 "Stage 1 / Stage 2" 才是训练阶段。
>
> 这两个 "stage" 在同一页纸上出现，**语义完全不同**，是最容易看晕的地方。

对照 ResNet-50 的四段：

| 记号 | 对应 | 输出 stride | 作用 |
|---|---|---|---|
| $\theta^1$ | `layer1`（stage1） | 4 | 边缘/纹理等低级特征 |
| $\theta^2$ | `layer2` | 8 | 低层形状 |
| $\theta^3$ | `layer3` | 16 | 中层语义 |
| $\theta^4$ | `layer4` | 32 | 高层语义（+ FPN + 检测头） |

### 2.2 两个阶段分别干什么

论文 §4.2 后面用三段散文解释，我翻译成中文要点：

**① Preliminary Adaptation（预备适应）**
> initialize our model with weights pre-trained on ImageNet and fine-tune it on our synthetic hazy dataset while **freezing only the initial backbone layer**.

- 从 ImageNet 预训练权重出发
- 只冻**第 1 段**（layer1）
- 其余全训：layer2/3/4 + FPN + head
- 目标：让**中间层表征**适应"模拟恶劣天气"

> [!tip] 冻结 layer1 的直觉
> layer1 是最底层的**边缘/纹理**提取器。
> 边缘这个物理量**不因雾而变**（雾只是加了个半透明的罩子，物体的边缘还在那儿），
> 所以它**跨域通用**，冻掉它可以省算力、还能防止 ImageNet 特征被冲掉。
> 反过来，layer3/layer4 决定"什么东西长得像车"，**雾一挡这个就变**，必须重新学。

**② Progressive Adaptation（渐进适应）**
> freezing both the early and middle backbone layers responsible for extracting low and mid-level features. We also employ a **reduced learning rate**.

- 接着 $\theta_m$ 继续训
- 冻 **layer1 + layer2 + layer3**（$k=3$ 时）
- 只训 **layer4 + FPN + 检测头**
- 学习率降到 $\eta_1 \cdot \gamma = 0.02 \times 0.1 = \mathbf{0.002}$

**③ Depth-Consistent Robust Learning（深度一致鲁棒学习）**
- 就是 SIRLoss（Eq.5），下一节单独讲

### 2.3 参数冻结表（k=3 的真实账）

> [!note] 本次用 torchvision ResNet-50 实测（含 BN 参数）
>
> | 部分 | 参数量 | 占 conv 部分 |
> |---|---|---|
> | stem (conv1 + bn1) | 9,536 | 0.04% |
> | layer1 (stage1) | 215,808 | 0.9% |
> | layer2 (stage2) | 1,219,584 | 5.2% |
> | layer3 (stage3) | 7,098,368 | 30.2% |
> | layer4 (stage4) | 14,964,736 | **63.7%** |
> | **conv 合计** | **23,507,904** | 100% |
>
> **Stage 1**（冻 layer1）→ 可训 **23,282,688（99.1%）** 的 conv 参数
> **Stage 2**（冻 layer1~3）→ 可训 **14,964,736（63.7%）** 的 conv 参数
> ＋ FPN（约 3.93M）＋ head（约 3.3M）⇒ **约 26.1M / 全模型 34.61M**
>
> 👉 **Stage 2 实际只更新 "stage4 + FPN + head"**，这正好对应论文说的
> "freezing the early and middle backbone layers... allows the network to adapt its **higher-level features**"。

### 2.4 为什么"冻结 + 降 lr"必须同时做？

> [!tip] 类比：**这是"外科手术"，不是"重装修"**
>
> - **冻结前几层** = 不动骨架。骨架（边缘、纹理、轮廓）在合成雾上已经学得很好了，
>   拿 400 张真实雾去动它，只会把它带偏（灾难性遗忘）。
> - **降 lr（0.02 → 0.002）** = 只做**微调**，不做**重训**。
>   如果 lr 还是 0.02，400 张图的梯度会把模型冲垮。
>
> 论文原话：*"preserving the learned feature extraction capabilities and **mitigating overfitting on the smaller real-world dataset**"*
> —— "在更小的真实雾数据集上缓解过拟合"，说的就是这两件事。

**为什么"只训高层"就能适配真实雾？**
因为雾主要改变的是**高层语义**（这团模糊的东西到底是不是车），
而**低层几何**（边界、纹理、轮廓）是**跨域稳定**的。
所以高层 = 需要适配的部分，低层 = 需要保护的部分。分层冻结正好对上这个物理直觉。

---

## 3. 收益有多大：Table 4 精确对账

> [!important] Table 4 的 "Progressive" 是**独立的一列**，第二行就是"只加 Progressive"
>
> 基线 = VFNet（不是 DeCoDet！），下面逐行看。

| Method | Progressive | MSDP | DCK | SIRLoss | M | Kernel | Group | β | Para(M) | GFLOPs | mAP–Test | mAP–Real |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DeCoDet (基线 VFNet) | – | – | – | – | – | – | – | – | 32.71 | 184.32 | 49.5 | **25.6** |
| **只加 Progressive** | ✓ | – | – | – | – | – | – | – | **32.71** | **184.32** | **49.5** | **35.6** |
| + MSDP | ✓ | ✓ | – | – | 3 | – | – | – | 34.59 | 221.14 | 49.8 | 35.8 |
| + DCK | ✓ | ✓ | ✓ | – | 3 | 7 | 16 | – | 34.61 | 230.41 | 50.6 | 36.9 |
| + SIRLoss | ✓ | ✓ | – | ✓ | 3 | – | – | 0.2 | 34.59 | 221.14 | 50.0 | 35.9 |
| **全量** | ✓ | ✓ | ✓ | ✓ | 3 | 7 | 16 | 0.2 | 34.61 | 230.41 | **52.0** | **38.0** |

### 3.1 三个关键读数

| 观察 | 数字 | 说明 |
|---|---|---|
| **只加 Progressive** | 49.5 → **49.5** / 25.6 → **35.6** | 合成域 **一点不变**，真实域 **+10.0** |
| **零参数开销** | 32.71M → 32.71M | 参数、GFLOPs **完全相同** |
| 全量 vs 基线 | 49.5 → 52.0（+2.5）/ 25.6 → 38.0（+12.4） | 三个模块加起来 |

> [!tip] 为什么合成域"一点不变"是**好事**而不是"没用"
> PDFT 的作用**完全**体现在真实域。合成域已经饱和了（49.5 是 VFNet 的水平），
> 冻结前几层 + 只训高层，本就不会破坏合成域的能力。
> 👉 **这是一个"只赚不亏"的策略**，这在论文里很常见（域适应类方法大多在源域会掉点）。

### 3.2 🔴 论文自身矛盾：38.0 还是 38.7？

| 出处 | 真实域 mAP |
|---|---|
| **Table 4** 全量行 | **38.0** |
| Table 3 的 DeCoDet 行 | **38.7** |
| §5.3 正文 | "achieves the best results (52.0% mAP on the test set, **38.0%** on real data)" |
| Table S1（不同深度损失）SIR Loss 行 | **38.7** |
| Table S2（不同深度估计模型）Metric3D 行 | **38.7** |

> [!warning] **同一个模型，同一个实验，论文里出现了两个值**
> 引用时**必须注明出处**。
> 我的建议：**写 38.0（Table 4，与消融表自洽）**，并在括号里补 "(Table 3 记为 38.7)"。
> 顺便：Table 3 的 DeCoDet 参数写 **34.62M / 225.37 GFLOPs**，
> 而 Table 4 写 **34.61M / 230.41 GFLOPs** —— **参数量和 GFLOPs 也对不上**。

### 3.3 PDFT 是"全篇通用底座"，不是 DeCoDet 专属

论文 §5.2（Detector Benchmark）原话：

> *all other models employ our **progressive fine-tune approach from Algorithm 1**, which involves training intermediate models on simulated data before real-world fine-tuning.*

👉 **Table 3 里那 16 个检测器全都用了 PDFT**（只有 IAYOLO / TogetherNet / MS-DAYOLO 这 3 个雾专用模型保持原协议）。

> [!important] 这条对你的意义
> 所以：
> - 论文 Table 3 里 VFNet 的真实域 35.6，**已经是 PDFT 之后的结果**
> - 你要复现 Table 3，**必须自己实现 PDFT**，否则所有数字都对不上
> - 而且 PDFT 的收益**不依赖 DeCoDet**——它对任何检测器都成立

---

## 4. SIRLoss 在这一节的角色

### 4.1 论文 Eq.5 原文

$$
\Delta d_i = \log(y_i) - \log\bigl(\alpha\, y_i^{*} + (1-\alpha)\, y_i\bigr), \qquad \alpha = 0.7
$$

$$
\mathcal{L}_{Dep} = \frac{1}{n}\sum_i (\Delta d_i)^2 - \frac{1}{n^2}\Bigl(\sum_i \Delta d_i\Bigr)^2 \tag{5}
$$

- $y_i$ = 模型预测的深度
- $y_i^{*}$ = 伪深度标签（pseudo label，来自 Metric3D 等单目估计）
- $\alpha = 0.7$ = **标签翻新（label refurbishment）的置信因子**

### 4.2 标签翻新在干嘛？

论文原话：

> the refurbished depth label is computed as a **weighted average of the prediction $y$ and a pseudo label $y^*$** ... with a confidence factor $\alpha = 0.7$

$$
\text{翻新标签} = 0.7 \times \underbrace{y^*}_{\text{伪标签}} + 0.3 \times \underbrace{y}_{\text{预测}}
$$

> [!tip] 类比：**老师批改作文**
> 伪标签（Metric3D 估的深度）就像"参考答案"，但它会错。
> 直接用参考答案罚学生 → 错的参考会误伤学生（**噪声放大**）。
> 翻新策略 = **拿学生的答案和参考答案按 7:3 混合**：
> 参考答案占大头保证方向对，学生答案占小头**稀释掉参考里的离群点**。
>
> 关键收益：**离群点被稀释了 0.7 倍**，误差被"抹平"，训练更稳。

### 4.3 SIRLoss ≠ PDFT，两者独立

> [!note] 容易混的一点
> §4.2 的标题是 "Progressive Domain Fine-Tuning **with Scale-Invariant Supervision**"，
> 但 **PDFT 和 SIRLoss 是两件独立的事**：
>
> | | PDFT | SIRLoss |
> |---|---|---|
> | 解决什么 | **跨域**（合成雾 → 真实雾） | **跨标签质量**（噪声伪深度） |
> | 作用对象 | 训练**流程**（冻结/学习率） | 训练**目标**（损失函数） |
> | Table 4 贡献 | 真实域 **+10.0** | 真实域 **+0.1 ~ +0.2** |
>
> PDFT 是**训练策略**（零参数），SIRLoss 是**损失函数**（零参数）。
> 两者都零参数，但作用完全不同。

论文 §5.3 的量化：
- MSDP：test **+0.3**，real **+0.2**
- MSDP + DCK：test **+0.8**，real **+1.1**
- SIRLoss：test **+0.2**，real **+0.1**

> [!tip] 对比一下量级
> **PDFT 一个策略 = +10.0**，**三个模块加起来 = +2.4（test）/+2.3（real）**。
> 👉 **PDFT 的收益是全模型模块收益的 4 倍多**，而且不花任何参数。
> 这是这篇论文最值得学的一点：**先把域间隙处理对，再谈架构花活。**

---

## 5. 🔴 论文 vs 代码：4 个对不上的地方

> [!danger] 这是本讲最有价值的部分
> **官方仓库里 PDFT 一行代码都没有。** 下面 4 条，前 2 条是"实现细节对不上"，
> 后 2 条是"根本没法跑"。

### 出入 ① SIRLoss 的 β：论文写 1，代码写 0.5

| | 公式 |
|---|---|
| 论文 Eq.5 | $\mathcal{L} = \frac{1}{n}\sum d_i^2 - \mathbf{1}\cdot\frac{(\sum d_i)^2}{n^2}$ |
| 代码 `SIRloss.py:76-78` | `- 0.5 * torch.sum(torch.sum(diff)**2)` |

```python
# HazyDet/models/losses/SIRloss.py:76-78
depth_cost = (torch.sum(nvalid_pix * torch.sum(diff**2))
              - 0.5 * torch.sum(torch.sum(diff)**2)) \
             / torch.maximum(torch.sum(nvalid_pix**2), torch.tensor(1.0, device=label.device))
```

> [!warning] 这意味着什么
> **β=1 时损失对"全局尺度偏移"严格免疫**（尺度项被完全消掉）；
> **β=0.5 时尺度项只被消一半**，模型整体偏个 10 倍仍要吃 `0.5·(ln10)² ≈ 2.65` 的罚。
>
> 📐 **本次数值实测**（64 像素，预测整体放大 1.5 倍 + 噪声）：
>
> | | 论文式 Δd | 代码式 Δd |
> |---|---|---|
> | β=1（论文） | 0.000347 | 0.000457 |
> | β=0.5（代码） | 0.035639 | 0.040763 |
>
> 👉 **同一组预测，论文公式和代码公式算出来的损失差 100 倍量级。**
> 想严格复现论文 Eq.5，得把 `0.5` 改成 `1.0`。
> 详见 [[公共基础知识/04-深度监督三件套与SiLog尺度性质]] §4.3。

> [!note] ⚠️ 千万别把两个 β 搞混
> - **Table 4 的 β = 0.2** 是 SIRLoss 的 **`loss_weight`**（损失整体乘 0.2）
> - **Eq.5 内部的系数 1 vs 0.5** 是**尺度项的消解比例**
>
> 两个都叫 β，但**不是一个东西**。代码里前者 = `loss_weight=0.2`，后者是写死在 `SIRloss.py:77` 的 `0.5`。

### 出入 ② 混合空间不同（线性 vs 对数）

| | 混合位置 |
|---|---|
| 论文 Eq.5 | **线性空间**混合：`log(α·y* + (1−α)·y)` —— 先混，再取 log |
| 代码 `SIRloss.py:60-67` | **对数空间**混合：先 `log`，再 `label = (1−ε)·label + ε·pred` |

```python
# HazyDet/models/losses/SIRloss.py:60-67
if self.log:
    pred  = torch.log(torch.clamp(pred,  min=1e-6))
    label = torch.log(torch.clamp(label, min=1e-6))
if self.smooth:
    label = (1 - self.epsilon) * label + self.epsilon * pred
```

系数对应关系：代码 `epsilon` ↔ 论文的 `1−α`（都乘在**预测**上）。

| config | 写法 | epsilon | 对应 α | 与论文 α=0.7 一致？ |
|---|---|---|---|---|
| `configs/vfnet/DeCoDet_vfnet_r50_fpn_1x_hazydet.py:50-56` | `smooth=True, epsilon=0.3` | 0.3 | 0.7 | ✅ |
| `configs/DeCoDet/DeCoDet_r50_1x_hazydet.py:61-66` | `smooth=True`，**未设 epsilon** | **0.1**（`SIRloss.py:26` 默认值） | 0.9 | ❌ |

> [!danger] FCOS 版的 DeCoDet config **漏设 epsilon**，实际用了 α=0.9 而不是 0.7
> 复现 FCOS DeCoDet 时要手动补上 `epsilon=0.3`。

> [!tip] 代码对数空间混合的**等价简化**（本次实测验证）
> 对数空间混合代入后：
> $$\Delta d_i = \log \hat y_i - [(1-\epsilon)\log y_i + \epsilon \log \hat y_i] = (1-\epsilon)\,[\log \hat y_i - \log y_i]$$
> ⇒ **代码的 `smooth` 实质上只是把 Δd 整体缩放了 $(1-\epsilon)$ 倍**，
> 相当于把 loss 乘 $(1-\epsilon)^2$，**并没有真的做"标签翻新"**。
> 实测：代码 `d / (1−ε)` 与纯 log 差的最大偏差 = **3.87e-07**（数值精度内完全一致）。
> 👉 详见 [[公共基础知识/04-深度监督三件套与SiLog尺度性质]] §4.4。

### 出入 ③ 官方仓库完全没有 PDFT 实现

实测（全仓库 grep `progressive|fine_tun|pdfmt|freeze`）：

```
$ grep -rniE "progressive|fine_tun|pdfmt|freeze" --include="*.py" --include="*.sh" --include="*.md" .
（0 命中）
```

- `tools/` 下只有 `train_det.py` / `test.py` / `get_flops.py` —— **没有两阶段训练脚本**
- 所有 config 的 `frozen_stages` **全是 1**（mmdet 默认行为，恰好等于 PDFT 的 Stage 1）
- **没有任何 `requires_grad=False` / 冻结逻辑**（命中的 `requires_grad` 全是 BN/GN 的）

> [!important] 唯一现成的"半成品"
> `configs/vfnet/DeCoDet_vfnet_r50_fpn_1x_hazydet.py:19` 的 `frozen_stages=1`
> —— 这正好就是 **PDFT Stage 1**（冻 layer1）。
> ⇒ **Stage 1 可以直接用官方 config 跑；Stage 2 必须自己写。**

### 出入 ④ 真实雾数据集没有官方 config

`configs/_base_/datasets/hazydet_dual.py` 里 `data_root` 指向：

```
/opt/data/private/fcf/Public_dataset/HazyDet-365K/data/HazyDet365K/
```

里面只有 `train/` `val/` `test/` 三份**合成雾**（`train/hazy_images/`、`val/hazy_images/`、`test/hazy_images/`）。

实测 `grep -rn "real" configs/` → **0 命中**。

> [!danger] ⇒ **Stage 2 需要的 400 张真实雾训练集，官方既没有 config，仓库里也没有**
> Table 2 标注：Real-world **Train 400 张 / 13,753 instances**；Real-world **Test 200 张 / 5,543 instances**。
> 这部分数据需要**自己收集或另找来源**。

---

## 6. 手把手复现 PDFT

### 6.1 你需要准备什么

| # | 事项 | 状态 |
|---|---|---|
| 1 | 合成雾训练集（HazyDet 8000 张） | ✅ 你本地已有（虽然只剩 1200 张，见 [[04-复现必查项与坑]]） |
| 2 | **真实雾训练集 400 张** | ❌ **没有**，得自己找 |
| 3 | 真实雾测试集 200 张 | ❌ 没有 |
| 4 | 深度图 | ✅ 只有 78 张（见 [[03-深度标注与被浪费的多模态线索]]） |
| 5 | mmcv-full + mmdet | ⚠️ macOS/arm64 **没有 wheel** |

### 6.2 Stage 1（在合成雾上训练）

**直接用官方 config 就行**——因为 `frozen_stages=1` 已经等于 Stage 1：

```bash
python tools/train_det.py \
  configs/vfnet/DeCoDet_vfnet_r50_fpn_1x_hazydet.py \
  --work-dir work_dirs/pdfmt_stage1
```

跑完得到 `work_dirs/pdfmt_stage1/epoch_12.pth` —— 这就是 Algorithm 1 第 9 行的 $M(\theta_m)$。

### 6.3 Stage 2（在真实雾上微调）—— 必须自己写 config

新建 `configs/vfnet/DeCoDet_vfnet_r50_fpn_1x_pdfmt_stage2.py`：

```python
_base_ = [
    '../_base_/datasets/hazydet_real.py',        # ← 你自己写的真实雾数据集配置
    '../_base_/schedules/schedule_1x.py',
    '../_base_/default_runtime.py'
]

model = dict(
    backbone=dict(
        frozen_stages=3,        # ← 🔴 核心：k=3 ⇒ 冻 layer1/2/3
        norm_cfg=dict(type='BN', requires_grad=True),
        norm_eval=True,
    ),
)

# ---- 学习率：η2 = η1 × γ = 0.02 × 0.1 = 0.002 ----
optim_wrapper = dict(
    optimizer=dict(type='SGD', lr=0.002, momentum=0.938, weight_decay=0.0001),
    clip_grad=dict(max_norm=35, norm_type=2),
    paramwise_cfg=dict(bias_decay_mult=0.0, bias_lr_mult=2.0),
)

# ---- 关掉 auto_scale_lr，否则 lr 会被再缩 8 倍 ----
auto_scale_lr = dict(base_batch_size=16, enable=False)   # 🔴 见下方坑①

load_from = 'work_dirs/pdfmt_stage1/epoch_12.pth'      # ← 从 Stage 1 加载

max_epochs = 12
work_dir = './work_dirs/pdfmt_stage2'
```

然后：

```bash
python tools/train_det.py \
  configs/vfnet/DeCoDet_vfnet_r50_fpn_1x_pdfmt_stage2.py
```

### 6.4 🔴 三个必踩的坑

> [!danger] 坑① `auto_scale_lr` 会把你的 lr 再缩 8 倍
> 官方 config 里有 `auto_scale_lr = dict(base_batch_size=16, enable=True)`，
> 而 `batch_size = 2`。mmdet 会按 `base_batch_size / batch_size = 8` **自动缩小 lr**：
> ```
> 0.002 → 0.002 / 8 = 0.00025
> ```
> → 你以为在用 η2=0.002，实际是 **0.00025**，比论文还小 8 倍，
> 第二阶段几乎学不动（或者学得极慢）。
> **解法**：Stage 2 里设 `auto_scale_lr = dict(enable=False)`。

> [!danger] 坑② `norm_eval` 必须保持 `True`
> 官方 config 里 `norm_cfg=dict(type='BN', requires_grad=True)` + `norm_eval=True`。
> 含义：**BN 的 running stats 冻结不更新，但 affine 参数（γ、β）仍然训练**。
>
> 为什么要冻 running stats？因为 **Stage 2 只有 400 张真实雾图**，
> 如果让 BN 统计量跟着这 400 张走，**均值/方差会被严重带偏**，
> 推理时用一批有偏的统计量去归一化 → 掉点。
> 👉 这是小数据微调的**经典陷阱**，几乎每个"少样本微调"教程都会提。

> [!danger] 坑③ 真实雾数据集配置要自己写，且注意深度图
> Stage 2 用的是真实雾图，**它们没有配对的深度图**（深度图只对合成数据有）。
> 但 DeCoDet 的 `loss_seg` 需要深度 GT！
>
> 论文的解法：**给真实雾图也生成一份伪深度**（用 Metric3D 等），
> 这也是 §4.2 "label refurbishment" 存在的原因——
> 真实域的伪深度更不准，所以要翻新。
>
> ⇒ 你的 `hazydet_real.py` 里，`data_prefix` 需要同时给 `img=` 和 `seg=`。

### 6.5 复现验收标准

| 检查项 | 期望 | 来源 |
|---|---|---|
| Stage 1 后在合成 test 上 | ≈ 49.5 mAP | Table 4 第 1 行 |
| Stage 2 后在合成 test 上 | ≈ 49.5 mAP（**不该掉**） | Table 4 第 2 行 |
| Stage 2 后在真实 test 上 | ≈ **35.6** mAP | Table 4 第 2 行 |
| 参数量 | Stage 1 = Stage 2（**必须完全相同**） | Table 4 |

> [!tip] 第三个检查项是最强证据
> 如果你的 Stage 2 **参数量变了**或者**合成集掉了几个点**，
> 说明冻结逻辑写错了（`frozen_stages` 没生效）或 lr 太大把模型冲垮了。

---

## 7. 自测题

<details>
<summary>Q1：Algorithm 1 里的 $\theta^2$ 是什么意思？</summary>

**A**：ResNet backbone 的**第 2 段**（layer2），**不是**"第 2 阶段训练"。
论文里 "Stage 1 / Stage 2" 才是训练阶段；$\theta^1..\theta^4$ 是 backbone 的 4 个 stage。
⚠️ 这是 §4.2 最容易看晕的地方。

</details>

<details>
<summary>Q2：PDFT 带来了多少 mAP？加了多少参数？</summary>

**A**：真实域 **+10.0**（25.6 → 35.6），合成域 **+0.0**（49.5 → 49.5）。
参数 **+0**（32.71M → 32.71M），GFLOPs **+0**（184.32 → 184.32）。

</details>

<details>
<summary>Q3：为什么 Stage 2 要降学习率？γ 是多少？</summary>

**A**：Stage 2 只有 **400 张**真实雾图，lr 太大 → 过拟合 + 冲垮 Stage 1 学到的特征。
$\eta_2 = \eta_1 \cdot \gamma$，$\gamma = 0.1$（§5.1 明确），
所以 lr 从 0.02 → **0.002**。

</details>

<details>
<summary>Q4：k=3 意味着冻掉哪些层？还剩多少参数能训？</summary>

**A**：冻 layer1 + layer2 + layer3，只训 **layer4 + FPN + head**。
conv 部分 23.51M → 只训 layer4 的 **14.96M（63.7%）**；
加上 FPN + head 约 **26.1M / 全模型 34.61M**。

</details>

<details>
<summary>Q5：论文 Eq.5 的 β 是多少？代码是多少？为什么重要？</summary>

**A**：论文 Eq.5 第二项系数 = **1**（严格尺度不变）；代码 `SIRloss.py:77` 写 **0.5**。
β=1 时全局尺度偏移被完全免疫；β=0.5 只消一半。
实测同一组预测两者算出的损失差 ~100 倍量级。
⚠️ 注意别和 Table 4 的 β=0.2（`loss_weight`）搞混。

</details>

<details>
<summary>Q6：官方仓库能直接跑出 PDFT 吗？</summary>

**A**：**不能**。全仓库零 PDFT 实现，`tools/` 无两阶段脚本。
Stage 1 恰好能用官方 config（`frozen_stages=1`），
Stage 2 得自己写（`frozen_stages=3` + `load_from` + `lr=0.002` + `auto_scale_lr` 关掉）。

</details>

<details>
<summary>Q7：SIRLoss 和 PDFT 是一回事吗？</summary>

**A**：**不是**。PDFT 是**跨域**的训练策略（冻结 + 降 lr，+10.0）；
SIRLoss 是**应对噪声伪深度**的损失函数（尺度不变 + 标签翻新，+0.1~0.2）。
§4.2 把它们放在同一节，只是因为共用同一个实验。

</details>

<details>
<summary>Q8：论文 Table 4 说真实域 38.0，Table 3 说 38.7，引用哪个？</summary>

**A**：**写 38.0（Table 4，与消融表自洽），并注明 Table 3 记为 38.7**。
论文自身不一致。顺带 Table 3 的 34.62M/225.37 GFLOPs 与 Table 4 的 34.61M/230.41 也对不上。

</details>

---

## 🔗 相关笔记

- [[05-DeCoDet原理精读]] —— MSDP / DCK 的原理（本讲的前一半）
- [[03-深度标注与被浪费的多模态线索]] —— 深度标注从哪来、SiLog 怎么算
- [[04-复现必查项与坑]] —— 本讲第 6 节 3 个坑的完整版 + 本地数据残缺清单
- [[公共基础知识/04-深度监督三件套与SiLog尺度性质]] —— β 的真相、`smooth` 的真相
- [[公共基础知识/05-ResNet50结构与分层冻结]] —— **$\theta^1..\theta^4$ 就是 ResNet 的四段**（§0.5 还讲了 ResNet 的历史作用）
- [[02-数据集构成与标注格式]] —— 合成雾怎么来的、真实雾数据集长什么样

## 🔗 本文（HazyDet）用在哪

| 本文内容 | 用在 HazyDet 的哪里 |
|---|---|
| 三域（$\mathcal{D}_s/\mathcal{D}_m/\mathcal{D}_t$） | §4.2 开头 + Algorithm 1 的 Require 行 |
| Algorithm 1 两阶段 | §4.2 Algorithm 1（19 行） |
| γ=0.1, k=3 | §5.1 Implementation Details |
| Real-world Train 400 张 | §5.1 / Table 2 |
| Table 4 消融 | §5.3 Ablation Study |
| 19 个检测器全用 PDFT | §5.2 Detector Benchmark |
| Fig. S5 三策略对比 | Appendix B.1 Effectiveness of PDFT |
| SIRLoss Eq.5 + α=0.7 | §4.2 第 3 段 |

---

**← 上一篇** → [[05-DeCoDet原理精读]] ｜ **下一篇 →** [[04-复现必查项与坑]] ｜ **索引 →** [[00-索引 MOC]]
