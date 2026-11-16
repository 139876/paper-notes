---
tags: [公共基础, 深度监督, max_depth, SiLog, 尺度不变, 相对深度, 损失函数, 监督信号]
aliases: [max_depth, max_depth.txt, 深度监督三件套, SiLog 尺度不变性, 深度损失, 深度靶子]
created: 2026-11-11
stage: 1 · 打地基
series: 基础 · 第 4 篇
related: "[[00-公共基础总览]]", "[[03-标注文件与真值gt]]", "[[02-数据集构成与标注格式]]", "[[03-深度标注与被浪费的多模态线索]]"
track: 公共基础
---

# 04 · 深度监督三件套 与 SiLog 的尺度性质

> [!note] 这是**公共基础知识**
> 任何"用深度图做监督"的多模态检测/分割都适用。

> [!tip] 一句话（先纠正一个常见误解）
> **`max_depth` 不是"深度答案"，它是每张图的一个标量刻度。**
> 损失函数真正比对的靶子是**逐像素的米制深度图**，
> 而那张图 = `PNG 相对深度 ÷ 65535 × max_depth`。
> **`max_depth` 从头到尾没有直接出现在损失函数里。**

---

## 4.1 深度监督的「三件套」

深度监督要凑齐三样东西，缺一样就训不了：

| # | 名字 | 是什么 | 形状 | 例子 |
|---|---|---|---|---|
| ① | `normalized_depth_maps/{id}.png` | **相对深度图**，uint16 像素 = 相对刻度 | `(H, W)` 整数 | `49257 ~ 65535` |
| ② | `max_depth.txt` 里的一行 | **每图一个标量**，单位「米」＝这张图的最大深度 | `()` 标量 | `12.97` |
| ③ | **GT 深度图（米）** | ①÷65535×② 的换算结果 | `(H, W)` 浮点，单位米 | `9.75 ~ 12.97` |

> 🎯 **类比 · 曝光**
>
> ① PNG 是**照片的亮度分布** —— 每张照片都各自用满 0~255，所以不同照片的"亮"不可比。
> ② `max_depth` 是**这张照片对应的实际光照范围**（EXIF 里的曝光参数）。
> ③ 是把亮度换算回真实亮度后的结果。
>
> 👉 **要做跨图比较，必须先换算（用②），不能直接比像素值。**

> 🎯 **类比 · 温度计**
> ① 是**刻度线**，② 是**"这根水银柱最高到多少度"**，
> ③ 是**每个刻度换算出的实际温度**。
> 损失比的是③（每个刻度的实际温度），不是②（最高温度）。

---

## 4.2 ❌ `max_depth` 不是损失靶子

**完整链路**（实测行号，来自 HazyDet 官方仓库）：

```
normalized_depth_maps/{id}.png  (uint16, 相对深度)
        │  ÷ 65535
        ▼
   相对深度 [0, 1]
        │  × max_depth[stem]          ← loading.py:230
        ▼
 ★ GT 深度图（米）──► results['gt_seg_map']
        │  resize / pad(填充值 255 = ignore_index)
        ▼
   gt_seg  (B, 1, H, W)
        │  F.interpolate(mode='nearest') → 每个 FPN level
        ▼
   silog_loss(pred_depth, target_depth)  ← SIRloss.py
        ▼
     loss_seg
```

**① 换算（数据加载层）**

```python
# Github/HazyDet-repo/HazyDet/datasets/transforms/loading.py:230
absolute_depth_map = depth_map / 65535.0 * max_depth
results['gt_seg_map'] = absolute_depth_map
```

**② 取监督目标（检测头）**

```python
# Github/HazyDet-repo/HazyDet/models/dense_heads/vfnet_DeCoDetHead.py:634
def get_seg_targets(self, seg_scores, batch_gt_sem_seg):
    for lvl in range(len(seg_scores)):
        lvl_seg_target.append(gt_sem_seg.sem_seg.data)
        lvl_seg_target = F.interpolate(lvl_seg_target, size=(h, w), mode='nearest')
```

**③ 算损失**

```python
# Github/HazyDet-repo/HazyDet/models/losses/SIRloss.py
depth_cost = (torch.sum(nvalid_pix * torch.sum(diff**2))
              - 0.5 * torch.sum(torch.sum(diff) ** 2)) \
             / torch.maximum(torch.sum(nvalid_pix**2), torch.tensor(1.0))
```

> [!important] 关键观察
> 看第③段代码 —— **找不到 `max_depth`**。
> 它在第①步就被"乘"进 GT 深度图里了，之后以**米**的形式藏在逐像素靶子里。
> 所以「拿 `max_depth` 这个数去和模型比」这个想法是**错的**：
> 模型预测的是**一张图**（H×W 个数），不是一个数。

### 🔬 本地实测（3 张图）

| 图 | `d_max`（米） | PNG 像素范围 | 换算后深度（米） | 中位数 |
|---|---|---|---|---|
| `000081` | 32.995 | 43862 ~ 65535 | 22.08 ~ 33.00 | 26.61 |
| `000144` | 156.471 | 7568 ~ 65535 | 18.07 ~ 156.47 | 29.67 |
| `000162` | 221.667 | 5719 ~ 65535 | 19.34 ~ 221.67 | 45.87 |

> [!warning] 这三张图的最远点 PNG **都是 65535**，但物理距离差了 **7 倍**（33 m vs 222 m）。
> 👉 **跨图颜色不可比**，这是「每图独立归一化」的必然副作用。

---

## 4.3 🔥 SiLog 到底「不变」什么？（本次实测修正）

### 公式分解

记有效像素数 `n`、逐像素对数误差 `d_i = log(ŷ_i) − log(y_i)`、均值 `d̄ = Σd_i/n`：

$$
L = \frac{1}{n}\sum_i d_i^2 \;-\; \beta \frac{\left(\sum_i d_i\right)^2}{n^2}
= \underbrace{\frac{1}{n}\sum_i (d_i - \bar d)^2}_{\textbf{结构项（尺度完全无关）}} + \underbrace{(1-\beta)\,\bar d^2}_{\textbf{尺度项（全局偏移）}}
$$

| β | 含义 | 谁在用 |
|---|---|---|
| **1** | **严格尺度不变**（结构项而已，尺度项被完全消掉） | 理论值 |
| **0.5** | **半尺度不变** —— 尺度项只剩一半 | ⚠️ **HazyDet 官方代码就是 `- 0.5 * ...`，即 β=0.5** |
| 0 | 普通 log-MSE | — |
> [!danger] 🔴 论文与代码不一致（本次新核实）
> **论文 §4.2 Eq.5 写的第二项系数是 `1`（不是 0.5）**，也就是**严格尺度不变**：
>
> $$
> \mathcal{L}_{Dep}=\frac{1}{n}\sum_i(\Delta d_i)^2-\frac{1}{n^2}\Bigl(\sum_i\Delta d_i\Bigr)^2
> $$
>
> 而官方代码 `HazyDet/models/losses/SIRloss.py:76-78` 写的是：
>
> ```python
> depth_cost = (torch.sum(nvalid_pix * torch.sum(diff**2))
>               - 0.5 * torch.sum(torch.sum(diff)**2)) \
>              / torch.maximum(torch.sum(nvalid_pix**2), torch.tensor(1.0, device=label.device))
> ```
>
> ⇒ **论文 β=1（严格尺度不变），代码 β=0.5（半尺度不变）**。
>
> 📐 **本次数值实测**（64 像素，预测整体放大 1.5 倍 + 噪声）：
>
> | | 论文式 Δd | 代码式 Δd |
> |---|---|---|
> | **β=1（论文）** | 0.000347 | 0.000457 |
> | **β=0.5（代码）** | 0.035639 | 0.040763 |
>
> 同一组预测，两者算出的损失**差 ~100 倍量级**。
> 👉 **想严格复现论文 Eq.5，需把 `SIRloss.py:77` 的 `0.5` 改成 `1.0`。**
>
> ⚠️ **别把两个 β 搞混**：
> - **Table 4 的 β = 0.2** = SIRLoss 的 `loss_weight`（损失整体乘 0.2）
> - **Eq.5 内部的 1 vs 0.5** = 尺度项的消解比例
>
> 两个都叫 β，但**不是同一个东西**。详见 [[paper-notes/论文精读/3-HazyDet精读/06-PDFT渐进域微调精读|06-PDFT渐进域微调精读]] §5 出入①。

### 实测对照（本次真跑出来的）

| 预测缩放 `c` | β=0.5（官方） | β=1（严格不变） | L1 对照 |
|---|---|---|---|
| ×1 | 0.082440 | 0.053118 | 11.18 |
| ×2 | 0.154811 | **0.053118** | 32.83 |
| ×10 | 2.175786 | **0.053118** | 382.94 |
| ×0.1 | 3.290992 | **0.053117** | 50.45 |

> [!warning] 修正一个流传很广的说法
> **「SiLog 对全局尺度偏移不变」——只有在 β=1 时才严格成立。**
> HazyDet **论文**写 β=1（严格成立），但**官方代码**是 **β=0.5**，尺度项没有被消掉，只是**从线性惩罚变成了二次软惩罚**：
> 预测整体错 10 倍 → SiLog 只多 `0.5·(ln10)² ≈ 2.65`，而 L1 会爆炸 **34 倍**。
>
> 👉 正确的说法是：**SiLog「对尺度误差非常宽容」，不是「完全免疫」。**
>
> 📌 上表的「β=0.5（官方）」列 = **代码**行为；「β=1（严格不变）」列 = **论文**行为。

### 一个更要紧的细节：尺度是 **batch 级**的

官方把**所有 FPN level × 整批图**的像素**拼成一个长向量**再算：

```python
flatten_seg_scores = torch.cat(flatten_seg_scores)   # (N_levels × B × H × W,)
flatten_seg_targets = torch.cat(flatten_seg_targets)
loss_seg = self.loss_seg(flatten_seg_scores, flatten_seg_targets)
```

⇒ 那一个 `d̄` 是**整批共享的**。
👉 模型必须输出**跨图一致的绝对尺度**；单张图偏个 2 倍不会被完全抵消掉。

---

## 4.4 🔥 `smooth` 的真相：它只是把损失乘了 0.81

官方 `SIRLOSS` 的执行顺序是 **先 log，再 smooth**：

```python
if self.log:
    pred  = torch.log(torch.clamp(pred,  min=1e-6))
    label = torch.log(torch.clamp(label, min=1e-6))
if self.smooth:
    label = (1 - self.epsilon) * label + self.epsilon * pred     # eps = 0.1
```

在**对数空间**做这个混合，代入 `d_i = log_pred − log_label`：

$$
d_i \;\longrightarrow\; \log\hat y_i - \big[(1-\epsilon)\log y_i + \epsilon\log\hat y_i\big] = (1-\epsilon)\, d_i
$$

⇒ `Σd²` 和 `(Σd)²` **同时**乘 `(1−ε)²` ⇒ **整个 loss 乘 `(1−ε)² = 0.81`**。

**实测比值 = 0.810000**，与 `(1−0.1)² = 0.81` **完全吻合**。

> [!danger] 这纠正了一个常见误读
> 很多资料说 `smooth` 是「标签平滑 / 抑制离群点 / 增强鲁棒性」。
> **在官方这个实现里，它没有这个效果** ——
> 它只是把深度损失整体乘 0.81，
> **等价于把 `loss_weight` 从 2.0 改成 1.62**，仅此而已。
>
> ⚠️ 结论**依赖实现**：如果某些代码是在**线性空间**混合，或**先 smooth 后 log**，结论会不同。
> HazyDet 官方是**先 log 后 smooth**。
### 🔴 补充（本次新核实）：论文和代码的「混合空间」不一样

上面分析的是**官方代码**的行为。但**论文 §4.2 Eq.5 写的是另一个式子**：

| | 混合发生在哪个空间 | 公式 |
|---|---|---|
| **论文 Eq.5** | **线性空间**（先混，再取 log） | $\Delta d_i = \log(y_i) - \log(\alpha\,y_i^{*} + (1-\alpha)\,y_i)$ |
| **官方代码** | **对数空间**（先 log，再混） | `label = (1-ε)·label + ε·pred`（在 log 之后执行） |

系数对应关系：代码的 `epsilon` ↔ 论文的 `1−α`（都乘在**预测**上），所以
`epsilon = 0.3` ⟺ `α = 0.7`。

| config | 写法 | epsilon | 对应 α | 与论文 α=0.7 一致？ |
|---|---|---|---|---|
| `configs/vfnet/DeCoDet_vfnet_r50_fpn_1x_hazydet.py` | `smooth=True, epsilon=0.3` | 0.3 | 0.7 | ✅ |
| `configs/DeCoDet/DeCoDet_r50_1x_hazydet.py` | `smooth=True`，**未设 epsilon** | **0.1**（`SIRloss.py:26` 默认值） | 0.9 | ❌ |

> [!danger] FCOS 版 DeCoDet config **漏设 `epsilon`**，实际跑的是 α=0.9 而不是论文的 0.7
> 复现 FCOS DeCoDet 时要手动补上 `epsilon=0.3`。

> [!tip] 为什么这个差别很重要
> 论文的**线性空间**混合（`log(0.7·GT + 0.3·pred)`）才有真正的「标签翻新」效果：
> 离群点被**算术平均**抹平。
> 代码的**对数空间**混合等价于 $\Delta d_i \to (1-\epsilon)\Delta d_i$（整体缩放），
> **并没有真的做翻新** —— 只是把 loss 乘了个 $(1-\epsilon)^2$。
> 📐 本次实测验证：代码 `d / (1−ε)` 与纯 log 差的最大偏差 = **3.87e-07**（数值精度内完全一致）。
>
> 👉 详见 [[paper-notes/论文精读/3-HazyDet精读/06-PDFT渐进域微调精读|06-PDFT渐进域微调精读]] §5 出入②。

---

## 4.5 💡 这对复现有什么用

| 结论 | 实际影响 |
|---|---|
| 结构项与尺度无关 | **`max_depth` 不够准也不会毁掉训练** —— 尺度项只是二次软惩罚 |
| 深度损失是**辅助**监督 | 深度权重（官方 2.0）不宜盖过检测主任务 |
| 尺度是 **batch 级**的 | 训练时若各图尺度打架，`loss_seg` 会莫名其妙变大 |
| `smooth` 只是常数系数 | 想调深度监督强弱，**改 `loss_weight` 即可**，别指望 `smooth` |

> [!tip] 落地建议
> 1. **不必等 6800 张深度图补齐才能开始复现** —— 批次里只要有深度图就能算 `loss_seg`。
>    （但深度分支是随机初始化的，深度图越少学到的越少。）
> 2. **诊断技巧**：结构项通常 < 0.1。若 `loss_seg` 长期 > 2.0，
>    基本可判定是**整体尺度偏了**（例如换算系数搞错、或者图和 `max_depth` 没对上号）。
> 3. **加一条 sanity check**：随机抽一张，打印 `gt_seg` 的 min/max/median，
>    和 `max_depth.txt` 里那一行对一下 —— **median 必须 ≤ d_max**。

---

## 4.6 ❓ 自测

<details>
<summary><b>1. <code>max_depth.txt</code> 里的 <code>152.0</code> 是什么意思？它是损失函数的靶子吗？</b></summary>

它是**这张图的最大深度（米）**，是一个**标量刻度**，不是靶子。
靶子是换算后的**逐像素米制深度图**（= PNG/65535 × 152.0）。
</details>

<details>
<summary><b>2. 模型输出的是一个数还是一张图？为什么不能拿 <code>max_depth</code> 去比？</b></summary>

输出一张 `(H, W)` 的深度图（每个像素一个米数）。
`max_depth` 只是**换算系数**，已经在数据加载阶段乘进靶子里了。
尺寸都不匹配（标量 vs H×W），没法比。
</details>

<details>
<summary><b>3. 某张图的 PNG 像素范围是 <code>60000~65535</code>，<code>d_max=30</code>。这说明什么？</b></summary>

这张图**很单调**：最远 30 米，最近 27.5 米（60000/65535×30），景深很浅。
也说明**光看颜色区分不出远近** —— 必须换算成米才知道差多少。
</details>

<details>
<summary><b>4. SiLog 里 <code>beta</code> 从 0.5 改成 1.0，损失函数会怎么变？</b></summary>

**尺度项消失**，只剩结构项 → 变成**严格尺度不变**。
预测整体乘 10 倍，loss **一字不变**（实测：0.053118 → 0.053118）。
代价是：模型再也没有任何信号去把深度**校准到真实米数**。
</details>

<details>
<summary><b>5. <code>smooth=True</code> 到底做了什么？</b></summary>

在**对数空间**把真值往预测方向拉 10%，等价于把逐像素误差乘 0.9，
最终**整个 loss 乘 0.81**（实测比值 0.810000）。
**不是**「抗离群点」，只是等价于把深度损失权重从 2.0 调到 1.62。
</details>

<details>
<summary><b>6. <code>loss_seg</code> 一直是 3.0，但结构项理论上应该 &lt; 0.1，最可能是什么问题？</b></summary>

**尺度项炸了** —— 即模型预测的深度整体尺度偏了（乘了个常数 c）。
先查：图和 `max_depth.txt` 是不是对上了号？换算公式是不是写成 `× 65535` 了？
</details>

---

## 🔗 相关笔记

- [[03-标注文件与真值gt]] — `gt` / `pred` 的命名约定；`gt_seg_map` 到底是什么
- [[01-bbox边界框标注]] — 另一种监督信号（框）的读法
- [[paper-notes/论文精读/1-CCFA-Net精读/01-公共基础知识/12-目标检测基础与mAP|12-目标检测基础与mAP]] — IoU / AP 的推导
- [[03-深度标注与被浪费的多模态线索]] — HazyDet 深度标注的完整故事（本文是它的"理论篇"）

---

## 🔗 本文（HazyDet）用在哪

- [[03-深度标注与被浪费的多模态线索]] §1.2 — `max_depth` 的反归一化公式出处
- [[03-深度标注与被浪费的多模态线索]] §1.4 — `max_depth.txt` 是哪来的、缺了会怎样
- [[03-深度标注与被浪费的多模态线索]] §2.4 — 官方 `SIRLOSS` 源码逐行讲解
- [[04-复现必查项与坑]] §1.1 — 数据集从哪下、目录名对不上的坑
- [[05-DeCoDet原理精读]] — 深度怎么反过来去调制检测特征（DCK）

---

**← 上一篇** → [[03-标注文件与真值gt]] ｜ **下一篇 →** 无 ｜ **索引 →** [[00-公共基础总览]] ｜ **返回 →** [[00-索引 MOC]]
