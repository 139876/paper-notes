---
track: 公共基础
tags: [公共基础, FPN, 特征金字塔, neck, CV, 遥感, 多尺度]
aliases: [FPN, Feature Pyramid Network, 特征金字塔网络]
created: 2026-11-04
stage: 1 · 打地基
series: 基础 · 第 7 篇
related: "[[00-索引 MOC]]", "[[05-第4讲-架构张量尺寸逐层推导]]", "[[08-第7讲-MFAM多尺度前景感知]]", "[[09-第8讲-TOOD检测头精讲]]"
---

# 补充 7 · FPN 特征金字塔网络

> [!note] 这是**公共基础知识**
> 这篇笔记与 CCFA-Net **没有绑定关系** —— 换任何论文、任何项目都用得上。
> 读 CCFA-Net 时它是「地基」；不读这篇论文，它照样是一篇独立的基础课。

## 7.1 为什么非得有 FPN（问题从哪来）

检测头最终要在**某一张特征图**上回答："这里是不是一辆车？"

- **浅层特征**（ResNet 的 C2 / C3）：分辨率高（stride 4 / 8），边缘清楚、位置精确，但**不知道这是什么**（没有语义）。
- **深层特征**（C5）：分辨率低（stride 32），**知道这是什么**（语义强，能说"这是一辆车"），但**位置糊了**（原图 1 个像素对应特征图 1 个格子，而 1 个格子代表原图 32×32 的区域）。

> 🎯 **比喻**
> 浅层像**高清照片**——车漆上的划痕都看得见，但你不认识这辆车，分不清它是车还是坦克。
> 深层像**远处的一团影子**——你一眼认出"那是辆车"，但框不出它的四个轮子。

**在 UAV 图像里这件事被放大成灾难**：无人机高度可调，同一张图里近处的车占几千像素，远处的车只占 20×20 像素。

- 只用深层 → 大目标好，**小目标直接消失**（一个 20×20 的车在 stride 32 上根本不够 1 个格子）。
- 只用浅层 → 能定位，但**认不出类别**。

FPN 的思路一句话：**让深层的语义"流"回浅层**，造出一串"既有语义、又有分辨率"的特征图，每张负责一个尺度带。

---

## 7.2 FPN 到底在算什么（三个部件 + 一个公式）

**部件 1 · 自底向上（bottom-up）**：backbone 一路算下来，得到 C2 / C3 / C4 / C5，分辨率逐级减半、通道逐级翻倍。

**部件 2 · 横向连接（lateral）**：每个 C_k 先过一个 **1×1 卷积**，把通道统一成同一个数（本文是 256），否则没法相加。

$$
L_k = \operatorname{Conv}_{1 \times 1}(C_k)
$$

**部件 3 · 自顶向下（top-down）**：从最深的 P5 开始，把上一层**放大 2 倍**后加到当前层的横向连接结果上。

$$
P_k = \operatorname{Conv}_{1 \times 1}(C_k) + \operatorname{Up}_{2 \times}(P_{k+1})
$$

逐层展开就是：

$$
P_5 = \operatorname{Conv}_{1 \times 1}(C_5)
$$

$$
P_4 = \operatorname{Conv}_{1 \times 1}(C_4) + \operatorname{Up}_{2 \times}(P_5)
$$

$$
P_3 = \operatorname{Conv}_{1 \times 1}(C_3) + \operatorname{Up}_{2 \times}(P_4)
$$

最后每层再过一个 3×3 卷积做平滑：

$$
\hat{P}_k = \operatorname{Conv}_{3 \times 3}(P_k)
$$

> [!important] 这里最容易搞错的一点
> **上采样的是"已经混好语义"的 P_{k+1}，不是原始的 C_{k+1}。**
> 语义是**从上往下逐层传播**的：C5 的语义先到 P4，P4 把"自己的浅层细节 + C5 的语义"混在一起变成 P4，P3 再拿 P4 去混 …… 所以越往下（越浅）语义越"淡"，但细节越"浓"。
>
> 这也正是 **FPN 与 PANet 的区别**：PANet（Liu et al., 2018）在 FPN 之后**额外加了一条自底向上的路径**，让浅层信息也能往上走，两条路夹着走。

---

## 7.3 数字账 · 手算一遍（用本文的真实配置）

输入 1333×800，`pad_size_divisor=32` → 实际送进网络的是 **1336×800**（这个坑见 [[02-padding彻底理解]]）。

ResNet-50 四个 stage 的输出：

| 层 | stride | 尺寸 H×W | 通道 | 说明 |
|---|---|---|---|---|
| C2 | 4 | 200×334 | 256 | stage1，高分辨率纹理 |
| C3 | 8 | 100×167 | 512 | stage2 |
| C4 | 16 | 50×84 | 1024 | stage3 |
| C5 | 32 | 25×42 | 2048 | stage4，语义最强 |

（1336/16 = 83.5 → 84，1336/32 = 41.75 → 42，都是 **ceil 向上取整**。）

TOOD 配置里 `start_level=1`，意思是 **FPN 从 C3 开始，C2 根本不进 FPN**：

| FPN 输出 | 来源 | stride | 尺寸 H×W | 负责什么 |
|---|---|---|---|---|
| P3 | C3 | 8 | 100×167 | 小目标（远处的车） |
| P4 | C4 | 16 | 50×84 | 中目标 |
| P5 | C5 | 32 | 25×42 | 大目标（近处的车） |
| P6 | P5 上再堆一个 stride-2 的 3×3 卷积 | 64 | 13×21 | 超大目标 |
| P7 | P6 上再堆一个 stride-2 的 3×3 卷积 | 128 | 7×11 | 兜底 |

**交叉验证（很重要）**：配置里 `anchor_generator` 写的 `strides=[8, 16, 32, 64, 128]`，和上面这 5 层**一一对应** ✓

> [!tip] 这就是 neck 和 head 之间的"接口契约"
> **FPN 输出几层、每层 stride 多少，检测头的 anchor 分配就必须完全对上。**
> 少一层、多一层，训练直接报错或掉点。这也是为什么 `start_level` 不能随便改（见 7.7）。

---

## 7.4 在本文哪里用到了（三个位置，逐个查证）

### 位置一 · Sec. 2.1 相关工作：FPN 是 neck 演进谱系的起点

论文原文（Sec. 2.1）：

> "Early studies mainly focused on multi-scale feature learning, aiming to improve the perception of small objects through feature pyramid architectures. Specifically, FPN (Lin et al., 2017) effectively fused high-level semantics and low-level spatial details via a top-down pathway, PANet (Liu et al., 2018) further enhanced low-level semantic representation through an additional bottom-up path, and HR-FPN (Chen et al., 2024b) maintained high-resolution representations throughout the network. Subsequent works such as CFPT (Du et al., 2025) and ORFENet (D. Liu et al., 2024) optimized multi-scale feature interaction and receptive field diversity, thereby improving small object detection. **However, these approaches still suffered from limited feature fusion and inadequate spatial awareness.**"

翻译成一句话：

| 方法 | 在 neck 上做了什么 | 年份 |
|---|---|---|
| FPN | 自顶向下，把高层语义送回浅层 | 2017 (CVPR) |
| PANet | 再加一条自底向上路径 | 2018 (CVPR) |
| HR-FPN | 全程保持高分辨率 | 2024 |
| CFPT | 跨层特征金字塔 Transformer | 2025 |
| ORFENet | 优化多尺度交互与感受野多样性 | 2024 |
| **MFAM（本文）** | **多尺度 + 前景感知注意力** | 2026 |

**注意最后那句加粗**：论文说前人"**特征融合有限、空间感知不足**" —— 这正是 **MFAM 要接的茬**。MFAM 干的就是"融合 + 空间（前景）感知"，和 FPN 是同一条赛道上的**后继者**，不是替代者。

### 位置二 · 架构：TOOD 检测头要吃多尺度特征

本文的检测子网络用的就是 TOOD（[[09-第8讲-TOOD检测头精讲]]），TOOD 头的输入天然就是 FPN 的多层输出。

代码证据（官方仓库 `configs/tood/tood_r50_fpn_1x_hazydet.py`）：

```python
neck=dict(
    type='FPN',
    in_channels=[256, 512, 1024, 2048],   # C2 C3 C4 C5
    out_channels=256,                     # 统一成 256 通道
    start_level=1,                        # 从 C3 开始（跳过 C2）
    add_extra_convs='on_output',          # 在 P5 上补 extra conv
    num_outs=5),                          # 共输出 P3~P7 五层
```

### 位置三 · Table 12 消融：FPN 是基线 neck

| Model | Car | Truck | Bus | mAP |
|---|---|---|---|---|
| FPN | 60.9 | 35.5 | 62.4 | 52.9 |
| FPN-DSAM | 61.7 | 36.1 | 63.4 | 53.8 |
| FPN-DPIC | 61.8 | 36.6 | 63.7 | 54.0 |
| FPN-CFPT | 62.2 | 37.2 | 63.3 | 54.2 |
| **FPN-MFAM (Ours)** | **62.2** | **37.5** | **64.2** | **54.6** |

**论文的论证链**：在同一副 FPN 骨架上，把"多尺度融合"这一步换成不同方案 → FPN 52.9 → DSAM 53.8 → DPIC 54.0 → CFPT 54.2 → **本文 MFAM 54.6**。

（DSAM = Song et al., 2025，Boundary-aware feature fusion with dual-stream attention；DPIC = Zhang et al., 2025；CFPT = Du et al., 2025，Cross-layer feature pyramid transformer。逐表精读见 [[12-第11讲-消融实验逐表精读]]。）

---

## 7.5 ⚠️ 一处关键内部不一致：MFAM 到底接在 FPN 的哪一侧？

**这是复现时必须做的决策。** 三条线索互相打架：

| 线索 | 出处 | 它在说什么 |
|---|---|---|
| **A** | 论文 Algorithm 1 第 14–16 行 | `for k∈{3,4,5}: P_k ← MFAM(S_k)`，注释写着 "Generate Pyramid Feat from S_k" → **MFAM 直接从 backbone 的 S_k 生成金字塔特征，算法里根本没出现 FPN** |
| **B** | 论文 Table 12 的行名 | "FPN" / "FPN-DSAM" / "FPN-DPIC" / "FPN-CFPT" / "FPN-MFAM" → **FPN 被保留，模块叠在它上面** |
| **C** | Table 11 × Table 12 交叉 | Table 11 的 "WO_MFAM" = 60.9 / 35.5 / 62.4 / **52.9**，和 Table 12 的 "FPN" 行**逐个数字完全相同** → "去掉 MFAM 的模型" ＝ "只有 FPN 的模型" → **FPN 一定还在** |

**结论**：线索 C 是最硬的交叉验证 —— Table 11 和 Table 12 里同一组数字同时出现，说明"没有 MFAM"和"只留 FPN"指的是同一个配置。所以真实结构几乎肯定是 **FPN 在前、MFAM 在后**：

$$
P_k = \operatorname{FPN}_k(C_k)
$$

$$
\hat{P}_k = \operatorname{MFAM}(P_k)
$$

Algorithm 1 那一行属于**简化写法**（把 FPN 隐含在 "Generate Pyramid Feat" 这句话里），不是结构定义。

> [!warning] 复现决策点（记下来，别到时候抓瞎）
> - **方式 1（推荐，贴合 Table 11 / 12）**：ResNet → **FPN**（出 P3/P4/P5）→ **MFAM** → TOOD
> - **方式 2（贴合 Algorithm 1 字面）**：ResNet → MFAM（逐层）→ 直接当金字塔用 → TOOD
> - **方式 2 等于没有 FPN**，那 Table 12 里 "FPN" 这个基线行就没法解释了。
> - 建议：先用**方式 1** 把 54.6 复现出来，再把方式 2 当成一条消融去跑 —— 这本身就是可以写进你自己论文的一个点。

---

## 7.6 FPN 在本文到底解决了什么？（回到"UAV 特性"那张表）

| UAV 特性 | FPN 帮上忙的地方 | 真正负责解决它的模块 |
|---|---|---|
| 尺度剧烈变化 | P3/P4/P5 各管一个尺度带，把"近大远小"摊平 | **MFAM**（3/5/7 多尺度 + 前景感知） |
| 小目标 | P3 分辨率高，不像 P5 那样把小车抹成一个点 | **TOOD 的 TAL 跨层样本分配** + FPN 多尺度 |
| 雾 / 低对比度 | **FPN 完全帮不上** | **CCDD**（复原）+ **CFFM**（跨域融合） |

> [!important] 定位提醒
> **FPN 在本文里是"背景板"，不是创新点。**
> 论文的三个创新（CCDD / CFFM / MFAM）**没有一个动 FPN**。
> 论文之所以要在 Table 12 里专门做 FPN 的消融，是为了证明一件事：
> **"多尺度融合这条路线我们认真比过了，本文的方法最好"** —— 把 FPN 摆出来当陪衬。

---

## 7.7 批判 · 围绕 FPN 这条线索的 3 个问题

### ① 官方仓库**没有** CCFA-Net 的模型代码

`CCFANet/` 目录里只有 4 类东西：HazyDet 数据集、`fcos_DeCoNetHead.py`、`fcos_MDDH.py`（FCOSDepthHead）、`SIRloss.py`。
全仓库 `grep -rn "CCDD\|CFFM\|MFAM"` **零命中**（我实测过）。

→ **FPN 之后到底接了什么，官方没开源，只能从论文反推**。这就是 7.5 那个决策点存在的原因。

### ② 层数对不上

Algorithm 1 只用了 {P3, P4, P5} **三层**；而 TOOD 的官方配置是 **5 层**（strides [8,16,32,64,128]）。论文没解释 P6/P7 去哪了。

→ 复现时这会直接影响 mAP：TAL 的"跨 FPN 层统一选 top-13"正样本，候选层数变了，分配结果就变了。这是个值得验证的细节。

### ③ `start_level=1` 是个**论文没说、但对读者有利**的隐藏细节

`start_level=1` ⇒ FPN 从 C3 开始 ⇒ **C2（stride 4）根本不进 FPN**，它只喂给 CCDD 做去雾。

→ 这和论文"**浅层归复原、深层归识别**"的设计在代码层面**完全自洽** ✓

论文正文从来没点明这一点。**你可以把这个当成自己的读码发现，在组会上讲出来 —— 老师会记住这种细节。**

---

## 7.8 自测题

**Q1.** FPN 里的 lateral 1×1 卷积和 top-down 上采样，各自解决什么问题？为什么两个都不能省？

**Q2.** backbone 只有 4 个 stage，为什么 FPN 却输出 5 层？

**Q3.** Table 11 的 "WO_MFAM" 和 Table 12 的 "FPN" 两行数字完全相同，这说明什么？

**Q4.** 如果你把配置里的 `start_level` 从 1 改成 0，会发生什么？

**Q5.** FPN 能解决"雾"吗？为什么？

<details><summary>点击展开答案</summary>

**A1.** 1×1 lateral 把不同 stage 的通道数（512 / 1024 / 2048）**统一成 256**，否则不同通道的特征图没法逐元素相加；top-down 上采样把深层语义**送回浅层**，让浅层那张图也知道"这看起来是什么"。少了 lateral 没法加，少了上采样就只剩"每层各管各的"，多尺度融合名存实亡。

**A2.** backbone 4 个 stage 只覆盖 stride 4~32，而 TOOD 需要覆盖到 stride 128（P7）。所以 FPN 用 `add_extra_convs='on_output'` 在 P5 上再堆两个 stride=2 的 3×3 卷积，补出 P6（stride 64）和 P7（stride 128），凑够 `num_outs=5`。

**A3.** 说明"**没有 MFAM 的模型**"和"**只有 FPN 的模型**"是同一个东西 → FPN 被保留，MFAM 是叠在 FPN 之上的。这是三条线索里最硬的一条，也是判断 Algorithm 1 属于简化写法的关键证据。

**A4.** FPN 会多出一层 P2（stride 4，通道来自 C2 的 256），输出变成 6 层。但 `anchor_generator` 只声明了 5 个 stride，多出来那层**没有对应的 anchor 分配规则** → 训练会直接报错（或者那层白算、纯浪费算力）。**这就是 `start_level` 必须和 `strides` 列表严格对齐的原因**，两者是耦合的，不能只改一个。

**A5.** 不能。FPN 只做**尺度融合**（不同深度之间），它完全不知道"雾"这个概念，既不建模大气散射、也不做域对齐。**跨域（雾域 ↔ 净域）融合是 CFFM 干的，出雾是 CCDD 干的。** 记住这个分工，你就知道论文为什么必须设计两个模块而不是一个。

</details>

---

## 🔗 相关笔记

- [[05-第4讲-架构张量尺寸逐层推导]] — 1333×800 一路走到检测头的完整张量账（本篇的数字账是它的浓缩版）
- [[08-第7讲-MFAM多尺度前景感知]] — MFAM 内部：3/5/7 深度卷积 + 前景感知注意力（Eq.8–13）
- [[09-第8讲-TOOD检测头精讲]] — TOOD 头如何消费 FPN 的 5 层输出（TAL 跨层分配）
- [[02-padding彻底理解]] — 为什么 1333 会变成 1336（本章尺寸账的前提）
- [[04-感受野深度理解]] — 多尺度与感受野的关系
- [[12-第11讲-消融实验逐表精读]] — Table 12 的逐行精读
- [[14-附录A-公式速查手册]] — 公式速查

---

---

---

---

## 🔗 本文（CCFA-Net）用在哪

> 这一节告诉你：**这篇公共知识，在 CCFA-Net 的哪个模块里被真正用到了**。
> 读论文时卡住，回来看对应模块；也可以从这里反查。

- [[05-第4讲-架构张量尺寸逐层推导]] — FPN 各层 stride
- [[08-第7讲-MFAM多尺度前景感知]] — MFAM 叠在 FPN 之后
- [[09-第8讲-TOOD检测头精讲]] — TOOD 的 TAL 跨层选样本
- [[10-第9讲-数据集与实验设置]] — start_level=1 ⇒ C2 不进 FPN


---

**← 上一篇** → [[06-空间注意力图]] ｜ **下一篇 →** [[08-激活函数]] ｜ **索引 →** [[00-索引 MOC]]
