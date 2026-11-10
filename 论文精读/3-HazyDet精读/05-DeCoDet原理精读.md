---
tags: [HazyDet, DeCoDet, DCK, MSDP, SIRLoss, 消融实验, 动态卷积, 复现]
aliases: [DeCoDet 原理, HazyDet 模型, DCK 动态卷积核, DeCoDet 精读]
created: 2026-11-10
related: "[[00-索引 MOC]]", "[[03-深度标注与被浪费的多模态线索]]", "[[04-复现必查项与坑]]"
---

# 05 · DeCoDet 原理精读（论文视角）

> [!abstract] 本讲要回答
> 1. 论文为什么说深度是 **"内在模态（intrinsic modality）"** 而不是"辅助任务"？物理根据是什么？
> 2. DeCoDet 两个模块（MSDP / DCK）到底在算什么？Eq.2–4 逐条拆解。
> 3. SIRLoss（Eq.5）为什么必须尺度不变？标签翻新 $\alpha=0.7$ 又是干嘛的？
> 4. 消融表里哪些数字最有信息量？
> 5. **论文写的和官方代码做的，有五个地方对不上**——哪些？

> [!note] 和 03 讲的关系
> [[03-深度标注与被浪费的多模态线索]] 讲的是**数据侧**（深度怎么存、怎么还原、SiLog 怎么算）；
> 本讲讲**模型侧**（深度怎么进入网络、怎么影响检测）。
> 03 是"深度**是什么**"，本讲是"深度**怎么用**"。

---

## 1. 论文的出发点：为什么深度是"内在模态"

论文 Sec. 4.1 原话：

> haze-induced visual ambiguities in aerial imagery are fundamentally governed by scene depth, which modulates **both the severity of degradation and the apparent scale of objects**.

物理链条来自大气散射模型（Eq.1）：

$$
I(x,y) = J(x,y)\,t(x,y) + A\,\bigl(1-t(x,y)\bigr), \qquad t(x,y) = e^{-\beta\, d(x,y)}
$$

由此有两条推论：

| # | 链条 | 结果 |
|---|---|---|
| 1 | $d$ 大 $\Rightarrow$ $t$ 小 $\Rightarrow$ $I \to A$ | **对比度塌陷、纹理糊掉**（退化严重程度） |
| 2 | 无人机俯视透视 $\Rightarrow$ $d$ 大 $\Rightarrow$ 目标在画面上更小 | **表观尺度变小** |

👉 **"远"这一个变量，同时决定了"退化的严重程度"和"表观尺度"。** 这就是"内在模态"论断的根据。

论文因此明确写道：

> Rather than treating depth as an auxiliary prediction or an isolated task, we architect DeCoDet to treat depth as an **intrinsic modality**, seamlessly woven into the detection pipeline.

### 数据集层面的证据（Fig. S4）

论文指出：估计深度与 bbox 面积存在**强负相关**。

> [!tip] 为什么这条证据是**必要**的
> 如果深度只是尺度的单调函数，那深度就是**冗余**的，做深度条件化没有额外收益。
> Fig. S4 证明两者只是**相关**不是**等价**——远处的东西不一定都小（远处的大卡车 vs 近处的小轿车）。
> 👉 **深度携带了尺度之外的信息**，这才是"内在模态"的完整含义。

---

## 2. 数据侧的深度：来自单目估计，不是激光雷达

论文 Fig.3(a) 的 pipeline 是：
`Data Collection → Data Processing → **Depth Estimation** → ASM → Semi-automatic Annotation`

- ASM（Eq.1）里的 $d$ 由"先进深度估计模型"得到（论文未点名具体模型）
- 所以深度标签本身是 **pseudo-depth**，**带噪声**
- 👉 这正是 SIRLoss 要专门设计"标签翻新"策略的原因

存储形式（详见 [[03-深度标注与被浪费的多模态线索]]），这里只留结论：
16-bit PNG（0–65535）+ `Depth/max_depth.txt` 逐图记录 $d_{\max}$，还原式：

$$
d_{\text{abs}}(x) = \frac{d_{\text{rel}}(x)}{65535}\cdot d_{\max}
$$

本机实测样本（已下载的真实数据）：

| 文件 | shape | dtype | 像素 max | $d_{\max}$ |
|---|---|---|---|---|
| `000081.png` | 1080×1920 | uint16 | 65535 | 32.995 m |
| `000144.png` | 765×1360 | uint16 | 65535 | 156.471 m |
| `000162.png` | 540×960 | uint16 | 65535 | 221.667 m |

> [!warning] 逐图归一化 ⇒ **跨图不可比** ⇒ 它本质是"相对深度"
> 这条事实后面会**直接决定** SIRLoss 必须是尺度不变的。

---

## 3. 模块一：Depth Prior Generation（MSDP）

论文 Eq.2：

$$
D_n^m = \mathrm{ReLU}\Bigl(\mathrm{BN}\bigl(\mathrm{Conv}_{3\times3}^{m}(D_n^{m-1})\bigr)\Bigr), \qquad D_n^0 = P_n
$$

- 在 FPN 的每一级 $P_n$ 上，接 $M$ 个 3×3 卷积
  - ⚠️ **级别数有三层证据，且互不一致**（详见 §3.1）
- 最后的特征 $D_n^M$ 经 **1×1 卷积**得到该尺度的深度图 $\{D_3, D_4, D_5, D_6, D_7\}$
- 最优 $M = 3$（见消融）

论文卖点（原文）：

> Unlike conventional encoder-decoder architectures requiring dedicated upsampling branches, our DeCoDet directly operates on the backbone's pyramidal features

👉 **没有解码器、没有额外上采样分支**，这是它"轻量"的来源。
代价：GFLOPs 从 184.32 → 230.41，参数量 32.71M → 34.61M（Table 4）。

### 3.1 到底是几级？图 / 正文 / 代码三层对不上

| 来源 | 特征层级 | Head 数 |
|---|---|---|
| **论文 Fig.4 图** | P₃, P₄, P₅, **P₇**（**没有 P₆**） | 4 |
| **论文正文 §4.1** | $P = \{P_3, P_4, \dots, P_7\}$，$n \in \{3,4,\dots,7\}$，深度图 $\{D_3,\dots,D_7\}$ | 5 |
| **官方 config**（FCOS & VFNet 相同） | `num_outs=5`、`strides=[8,16,32,64,128]` → P₃,P₄,P₅,**P₆**,P₇ | 5 |

**代码里 P6 从哪来**：`start_level=1` 让 FPN 从 C₃ 起 → 先得到 P₃/P₄/P₅；
`num_outs=5` 比 3 多两级，于是**在 P₅ 的输出上再叠 2 个 extra conv**（`add_extra_convs='on_output'`）
→ 产出 P₆（stride 64）和 P₇（stride 128）。

**结论**：**正文和代码一致（5 级），Fig.4 是那个画漏了一级的**。
所以看图数金字塔时别被误导——**实际跑的是 P₃–P₇ 五级**。

> [!tip] 这类不一致该怎么处理
> 一般原则：**图是示意图，正文和代码才是实现依据**。
> 但反过来也成立——如果你要复现**官方权重**，代码优先级最高。
> 📌 遇到图 / 正文 / 代码打架，**三处都查一遍**，别只信一处。

---

> [!warning] 一个**极易被忽略**的点
> DCK 用的**不是**最终那张深度图，而是**中间层特征** $D_n^m$。
> 深度图只是**副产品**——它的真正作用是**监督**，保证中间特征确实编码了深度。
>
> 代码对应：`fcos_DeCoDetHead.py:66,72` 送进 DCK 的是 `seg_feats[i+1]`
> （第 $i{+}1$ 个 `seg_conv` 的输出），而不是 `conv_seg` 的输出。

---

## 4. 模块二：DCK —— 全文最核心

![[fig4_full.jpg]]

### 4.1 核的生成（Eq.3）

$$
K_{i,j} = W_2 \cdot \sigma\bigl(W_1 \cdot D[i,j]\bigr)
$$

| 符号 | 含义 | 代码对应（`DCKModule`） |
|---|---|---|
| $W_1 \in \mathbb{R}^{C/r \times C}$ | 降维 $r$ 倍（**瓶颈结构**） | `convs1`：1×1 Conv，C→C/r，BN+ReLU |
| $W_2 \in \mathbb{R}^{(K^2G) \times C/r}$ | 升维成 $G$ 个 $K\times K$ | `convs2`：1×1 Conv，C/r→G·K² |
| $\sigma$ | BN + 非线性激活 | `norm_cfg=dict(type='BN')`, `act_cfg=dict(type='ReLU')` |
| $K_{i,j} \in \mathbb{R}^{K\times K\times G}$ | 位置 $(i,j)$ 的**动态核** | `weight.view(b, G, K², h, w)` |

默认超参：$K=7$、$G=16$、$r=4$。通道数 $C=256$ 时 `groups = 256 // 16 = 16`，
即**每 16 个通道共享一个 7×7 核**。

### 4.2 特征的调制（Eq.4）

$$
Y'_{i,j,g} = \sum_{(u,v)\in\Delta K} K_{i,j,\;u+\lfloor K/2\rfloor,\;v+\lfloor K/2\rfloor,\;\lceil gG/C\rceil} \odot Y_{i+u,\,j+v,\,g}
$$

其中 $\Delta K = [-\lfloor K/2\rfloor, \dots, \lfloor K/2\rfloor]^2 \subset \mathbb{Z}^2$ 是以该位置为中心的邻域偏移集合。

> [!tip] **大白话拆解**
> **检测特征 $Y$ 提供"值"，深度特征 $D$ 提供"权重"。**
> 同一个 7×7 窗口，普通卷积用**一套固定权重**扫全图；
> DCK 让**每个位置用自己深度生成的那一套权重**。
>
> 论文原话：$K$ 表示"与空间调制范围相关的核大小"——
> 也就是说，**核的作用半径本身**由深度调制。

### 4.3 DCK 与其它动态卷积的区别（**本讲最关键的一张表**）

| 方法 | 核 / 偏移由谁生成 | 引入深度了吗 |
|---|---|---|
| 普通卷积 | 训练时固定 | ❌ |
| Deformable Conv (DCN) | **输入特征自己**学偏移 | ❌ |
| Dynamic Conv | **输入特征**生成核 | ❌ |
| **DCK（DeCoDet）** | **另一个模态：深度图** | ✅ |

👉 DCK 是**跨模态条件化**，不是自条件化。
这是 DeCoDet 真正的技术卖点，也是它和一堆"动态卷积增强"论文拉开差距的地方。

### 4.4 三条性质（论文原文）

1. **Geometric awareness** through explicit depth conditioning
2. **Spatial adaptivity** via position-specific kernels
3. **Scale consistency** through pyramidal feature alignment

### 4.5 ⚠️ 必须诚实说明的一点

论文**没有**写死"深度大 → 核更大 / 更平滑"。

$K_{i,j}$ 完全由 MLP 从深度学出来，其语义只能通过 **DET Loss + SIRLoss 间接塑造**。
所以"远处用更大聚合范围"是一个**合理直觉**，但**不是论文声明**。

> [!warning] 复现提醒
> 不要试图"手工实现"那个直觉（比如按深度线性放大核）。
> 那样你会偏离官方实现，而且无法解释为什么官方能work。

---

## 5. 深度怎么学进来：SIRLoss（Eq.5）

$$
L_{\text{Dep}} = \frac{1}{n}\sum_{i=1}^{n}(\Delta d_i)^2 \;-\; \frac{1}{n^2}\Bigl(\sum_{i=1}^{n}\Delta d_i\Bigr)^2
$$

$$
\Delta d_i = \log(y_i) - \log\bigl(\alpha\, y_i^{*} + (1-\alpha)\, y_i\bigr), \qquad \alpha = 0.7
$$

> [!note] 符号说明
> $y_i$ = 网络预测的深度；$y_i^{*}$ = pseudo 深度标签（真值）；
> $\alpha$ = **伪标签置信因子**。
> （代码里少了尺度项的 $\lambda=0.5$，见 §7）

三项设计各司其职：

| 项 | 作用 | 直觉 |
|---|---|---|
| `log` | 进入对数空间 | 深度是**乘性量**，对数后误差 = **相对误差** |
| $-\frac{1}{n^2}(\sum \Delta d_i)^2$ | 扣掉**整体偏移** | **尺度不变**：所有深度乘常数 $c$，损失不变 |
| $\alpha y^* + (1-\alpha)y$ | **标签翻新** | $\alpha=0.7$；伪标签错时不至于把网络带偏 |

**为什么必须尺度不变**：§2 已证明深度是**逐图归一化**的，跨图尺度本就不可比。
如果不减掉整体偏移项，网络就会被迫去拟合一个它根本不知道的绝对尺度。

> [!warning] **关键认知**
> 深度**不直接监督检测框**。深度只是"**造核的原料**"，
> 它对检测的贡献**完全通过核的形状间接传导**。
>
> 👉 所以深度分支估错 → 核错 → 检测错，两个分支**强耦合**。
> 论文用图里的 `S`（Skip Connection，代码 `feature_map = out + feature_map`）来缓解。

---

## 6. 消融实验（Table 4）—— 哪些数字最有信息量

| 配置 | mAP–Test | mAP–Real | GFLOPs |
|---|---|---|---|
| VFNet baseline | 49.5 | 25.6 | 184.32 |
| + Progressive FT | 49.5 | **35.6** | 184.32 |
| + MSDP | 49.8 | 35.8 | 221.14 |
| + DCK | 50.6 | 36.9 | 230.41 |
| + SIRLoss（全上） | **52.0** | **38.0** | 230.41 |
| $M=1$ | 50.1 | 35.6 | 156.68 |
| $K=3$（太窄） | **42.9** | 31.2 | 224.26 |
| $K=9$（太宽） | 51.4 | 37.3 | 237.38 |
| $G=1$ | 49.2 | 34.3 | 224.46 |
| $G=64$ | 51.6 | 37.2 | 249.86 |

三个最有信息量的结论：

1. **Progressive FT 只涨真实域（+10.0），合成域纹丝不动（+0.0）**
   → 它解决的是**合成 → 真实的域差**，不是检测能力本身。
   👉 这两件事必须**分开评估**，混在一起看会误判。
2. **$K$ 从 7 降到 3，掉 9.1 个点**（52.0 → 42.9）
   → "**空间调制范围**"这个维度很关键，DCK 不是随便加个模块就有用。
3. **$G=1$ 比 $G=16$ 差 2.8 点**（49.2 vs 52.0），而参数量只从 34.61M 涨到 34.92M
   → **分组共享核**（而非每通道独立核）是必要设计，性价比很高。

---

## 7. ⚠️ 论文 vs 官方代码：**五个对不上的地方**

| # | 项 | 论文 | 官方代码 | 影响 |
|---|---|---|---|---|
| 1 | 标签翻新 $\alpha$ | 0.7 | `smooth=True, epsilon=0.1` → 等效 $\alpha=\mathbf{0.9}$ | 代码里伪标签权重更大 |
| 2 | SIRLoss 权重 $\beta$ | 0.2（消融最优） | `loss_weight=2.0` | **差 10 倍** |
| 3 | 尺度项系数 | Eq.5 无系数 | `- 0.5 * ...`（Eigen 的 $\lambda=0.5$） | 论文少写 |
| 4 | 基线 | **VFNet** | `configs/DeCoDet/` 是 **FCOS** | 论文 Table 4 的 baseline 是 VFNet |
| 5 | 深度卷积数 $M$ | 3（最优） | `stacked_convs=4` | 代码实际是 4 层 |
| 6 | **金字塔级别数** | 正文 5 级（P₃–P₇） | 代码 5 级（`num_outs=5`） | **但 Fig.4 图只画了 4 级（无 P₆）** |

**另一个代码级发现**（关于 §5 的 `smooth`）：

```python
label = (1 - epsilon) * label + epsilon * pred   # 0.9·GT + 0.1·pred
diff  = pred - label
      = pred - 0.9·GT - 0.1·pred
      = 0.9 · (pred - GT)
```

👉 `smooth=True` 在**这份实现里**等价于**把整个 SiLog 乘 0.81**，
它**并没有**真正实现论文所说的"标签翻新"（论文里预测要占 0.3，代码只占 0.1）。

> [!warning] 复现建议
> - 想**复现论文数字** → 按论文调：$\alpha=0.7$、$\beta=0.2$、$\lambda=0.5$、$M=3$
> - 想**复现官方 checkpoint 行为** → 用官方 config 原样，别动
>
> **两者别混**，否则你不知道自己在验证什么。

---

## 8. ❓ 自测

1. 论文说深度是 "intrinsic modality"，它的物理根据是哪**两条**？用 Eq.1 推。
2. Fig. S4（深度-尺寸负相关）这个证据为什么是**必要**的？如果深度就是尺度的函数会怎样？
3. DCK 的核由**深度图**生成，而不是让检测特征自己学（像 DCN 那样）——两者的失败模式有什么不同？
4. Eq.5 里减掉 $-\frac{1}{n^2}(\sum\Delta d_i)^2$ 会发生什么？结合"逐图归一化导致跨图尺度不可比"回答。
5. 深度分支估错了，检测分支会怎样？论文用什么结构缓解（看 Fig.4 里的 `S`）？
6. 消融表里 Progressive FT 让 mAP–Real 涨 10 点、mAP–Test 涨 0 点，说明什么？如果你的方法在真实域上没涨，问题可能出在哪？
7. 代码里 `smooth=True` 等价于把 SiLog 乘 0.81 —— 它**并没有**实现论文说的"标签翻新"。这算 bug 还是设计？你会怎么处理？

<details>
<summary>👉 折叠答案</summary>

1. ① $d$ 大 → $t=e^{-\beta d}$ 小 → $I \to A$ → 退化严重（雾更浓、对比度更低）；② 俯视透视 → $d$ 大 → 目标表观尺寸更小。**"远"同时决定退化程度和表观尺度**，所以深度是贯穿成像与观测的内在变量。

2. 如果深度只是尺度的单调函数，它就是冗余的，条件化没有额外收益。Fig. S4 证明二者只是**相关**不是**等价**（远处的大卡车 vs 近处的小轿车），说明深度**携带了尺度之外的信息**。

3. DCN 的偏移由**同一个模态的特征**学出来，在雾天它没有任何"雾浓不浓"的先验，只能盲目地从被污染的纹理里猜；DCK 的核由**深度图**生成，深度直接携带"这个位置被雾削弱了多少"的信息，是**跨模态条件化**，因果通路更直接。

4. 去掉该项后，损失对"所有深度整体乘一个常数 $c$"**不再不变**（对数误差整体平移 $\log c$，而该项正是用来扣掉这个常数平移的）。由于深度是逐图归一化的、跨图绝对尺度本就未知，网络会被迫去拟合一个它无法确定的绝对尺度，训练信号被无谓的尺度自由度污染。

5. 核会错 → 检测特征聚合方式错 → 检测直接退化，两个分支**强耦合**。论文用 Fig.4 里的 `S`（Skip Connection，代码 `fcos_DeCoDetHead.py:154` 的 `feature_map = out + feature_map`）保留恒等映射，让深度分支即使学得不好，检测分支也能退回普通卷积的行为、不至于崩溃。

6. 说明 Progressive FT 解决的是**合成→真实的域差**（真实域 +10.0、合成域 +0.0），它不提升检测能力本身。真实域没涨，可能是：① 合成/真实的雾分布差异没被覆盖（$A$、$\beta$ 的分布假设不够）；② 微调时冻结层数选错（冻太多学不到、冻太少过拟合 400 张真实图）；③ 学习率衰减 $\gamma$ 太狠；④ 伪深度/检测在真实域上的噪声更大。

7. 严格说是**实现与论文描述不符**，但不是致命 bug——它退化成"带一个常数缩放的 SiLog"，仍然能训练。
   处理方式：① 若目标是复现论文结论，按论文参数重写这一项并重跑；② 若目标是复现官方权重，保持原样但在报告里**明确写出**；
   ③ 无论哪种，都在论文复现笔记里留一条"论文-代码差异"记录，避免后来者重复踩坑。

</details>

---

## 🔗 下一步

- 动手前必看 → [[04-复现必查项与坑]]
- 深度侧基础 → [[03-深度标注与被浪费的多模态线索]]
- 跨模态方法论对比 → [[paper-notes/论文精读/2-Cross-Modal-UAV精读/02-第1讲-知识蒸馏与模态鸿沟]]
- 可落地的选题方向 → 本讲 §5 提到的"深度作为免学费的前景/尺度先验"

---

**← 上一篇** → [[04-复现必查项与坑]] ｜ **下一篇 →** 无 ｜ **索引 →** [[00-索引 MOC]]
