---
tags: [公共基础, ResNet, ResNet50, Backbone, 残差连接, Bottleneck, FPN, 冻结, 目标检测]
aliases: [ResNet50 结构, ResNet 结构详解, ResNet50 分层冻结]
created: 2026-11-12
stage: 1 · 打地基
series: 基础 · 第 05 篇
related: "[[00-公共基础总览]]", "[[04-深度监督三件套与SiLog尺度性质]]", "[[paper-notes/论文精读/3-HazyDet精读/06-PDFT渐进域微调精读]]"
track: 公共基础
---

# 05 · ResNet50 结构与分层冻结

> [!abstract] 本讲要回答
> 1. ResNet50 从头到尾长什么样？（每个 stage 多少层、通道怎么变、分辨率怎么变）
> 2. **残差连接**到底解决什么问题？为什么是 `y = F(x) + x`？
> 3. **Bottleneck**（瓶颈块）为什么长成 1×1 → 3×3 → 1×1 这个样子？
> 4. 「shortcut / downsample」那条旁路是干什么的？
> 5. 🔥 **和 HazyDet 的对接**：`frozen_stages=1` 和 `=3` 到底冻了哪些层？各占多少参数？

> [!note] 为什么这篇值得单独写
> 读 [[paper-notes/论文精读/3-HazyDet精读/06-PDFT渐进域微调精读|06-PDFT渐进域微调精读]]（PDFT）时，
> Algorithm 1 里的 $\theta^1 / \theta^{2:3}$ 一直很抽象。
> **搞懂 ResNet50 的四段划分，那些符号立刻就具体了。**

---

## 0. 结论先行

> [!tip] 一张表看懂 ResNet50
>
> | 阶段 | 名字 | 块数 | 通道 | 输出分辨率 | 参数量 | 占比 |
> |---|---|---|---|---|---|---|
> | stem | conv1+bn1+maxpool | — | 64 | **1/4** | 9,536 | 0.04% |
> | stage1 | layer1 | **3** | 64→**256** | 1/4 | 215,808 | 0.9% |
> | stage2 | layer2 | **4** | 256→**512** | 1/8 | 1,219,584 | 5.2% |
> | stage3 | layer3 | **6** | 512→**1024** | 1/16 | 7,098,368 | 30.2% |
> | stage4 | layer4 | **3** | 1024→**2048** | 1/32 | 14,964,736 | **63.7%** |
> | — | **conv+bn 合计** | — | — | — | **23,508,032** | 100% |
> | — | fc（分类头，检测里不用） | — | 2048→1000 | — | 2,049,000 | — |

**一句话**：ResNet50 = **1 个 stem + 4 个 stage（共 16 个 Bottleneck 块）**。
参数量**极度集中在 stage4**（63.7%）——这个数字直接决定了 PDFT 冻结策略的效果。

---

## 1. 完整结构图

### 1.1 整体流程

```
输入图像  3 × H × W
   │
   ├─► conv1: 7×7, stride=2, 3→64        ──► 64 × H/2 × W/2
   ├─► bn1 + ReLU
   ├─► maxpool: 3×3, stride=2            ──► 64 × H/4 × W/4      ← stem 结束
   │
   ├─► layer1  (stage1): 3 × Bottleneck  ──► 256  × H/4  × W/4    stride 4
   ├─► layer2  (stage2): 4 × Bottleneck  ──► 512  × H/8  × W/8    stride 8
   ├─► layer3  (stage3): 6 × Bottleneck  ──► 1024 × H/16 × W/16   stride 16
   ├─► layer4  (stage4): 3 × Bottleneck  ──► 2048 × H/32 × W/32   stride 32
   │
   └─► (分类任务) avgpool → fc(2048→1000)
        (检测任务) → 特征交给 FPN，fc 被丢弃
```

> [!important] 检测里 fc 会被丢掉
> torchvision 的 `resnet50` 参数 25,557,032 = conv+bn 23,508,032 + fc 2,049,000。
> 做检测时**只取 backbone**，fc 扔掉。
> 所以 HazyDet 里 VFNet 的 backbone 参数 = **23.5M**，
> 整个模型 32.71M（剩下的 9.2M 是 FPN + 检测头）。

### 1.2 为什么是这个"金字塔"形状

| | 通道数 | 分辨率 | 每层能"看到"多大范围 |
|---|---|---|---|
| stage1 | 64 | 1/4 | 小（细粒度纹理） |
| stage2 | 512 | 1/8 | 中 |
| stage3 | 1024 | 1/16 | 大 |
| stage4 | 2048 | 1/32 | 很大（高层语义） |

**分辨率每 stage 减半、通道数翻倍** —— 这是 CNN 的通用设计：
早期层保**空间细节**（但语义弱），深层提**语义**（但空间粗）。
目标检测恰恰**两个都要**（小目标要细节，大目标要语义），
所以要 **FPN 把四个 stage 融合起来**（见 §5）。

---

## 2. Bottleneck 块：ResNet50 的基本单元

### 2.1 结构（以 `layer2[0]` 为例，实测输出）

```
输入 256 × H × W
   │
   ├─────────────────────────┐  (identity 旁路 / 或 downsample)
   │                         │
   ▼                         │
conv1: 1×1, 256→128          │   ← 降维（bottleneck 就在这）
bn1 + ReLU                   │
conv2: 3×3, 128→128, stride=2│   ← 空间操作
bn2 + ReLU                   │
conv3: 1×1, 128→512          │   ← 升维
bn3                         │
   │                         │
   ▼                         ▼
  out = conv3_out + shortcut_out    ← 相加
   │
   ▼
输出 512 × H/2 × W/2
```

### 2.2 三个卷积各自的作用

| 卷积 | 核 | 通道 | 干什么 |
|---|---|---|---|
| conv1 | **1×1** | C → C/4 | **降维**，把计算量砍到 1/4 |
| conv2 | **3×3** | C/4 → C/4 | 唯一做**空间特征提取**的地方 |
| conv3 | **1×1** | C/4 → 4C | **升维**回输出通道数 |

### 2.3 为什么叫"瓶颈"？

> [!tip] 算一笔账
> 拿 `layer3` 的一个块举例：输入 512 通道。
>
> **如果直接 3×3 做 512→1024**：
> $$
> 3\times3\times512\times1024 = 4{,}718{,}592 \text{ 个参数/个位置}
> $$
>
> **用瓶颈 1×1→3×3→1×1**：
> $$
> 1\times1\times512\times256 + 3\times3\times256\times256 + 1\times1\times256\times1024
> = 131{,}072 + 589{,}824 + 262{,}144 = \mathbf{983{,}040}
> $$
>
> 👉 **参数少了约 4.8 倍**，而表达能力几乎不降。
>
> **这就是 Bottleneck 的全部动机**：先用 1×1 把通道"掐细"，
> 让昂贵的 3×3 卷积在窄通道上跑，最后再用 1×1 "撑"回来。

### 2.4 残差连接：`y = F(x) + x`

```python
out = self.conv3(self.bn3(self.relu(self.conv2(...))))  # F(x)
out += self.downsample(x)   # shortcut（如果需要）
out = self.relu(out)
```

> [!important] 残差连接解决的到底是什么问题
> **不是**"让网络更深"，而是**让深层可训练**。
>
> 设想一个 50 层的网络，梯度要反传 50 层。
> 没有残差时，梯度要**连乘** 50 个雅可比矩阵 —— 极易**梯度消失**（连乘后趋近 0）。
>
> 有了残差，每一层只需学一个"**残差量**" $\Delta x$：
> $$x_{l+1} = x_l + F(x_l)$$
> 反传时 $\frac{\partial x_{l+1}}{\partial x_l} = I + \frac{\partial F}{\partial x_l}$，
> 那个 $I$（单位矩阵）**保证了梯度至少有一条"直通车"**。
>
> 👉 通俗说：**每层只需要在"原样传过去"的基础上做一点点修正**，不用重新学一遍。

### 2.5 shortcut 旁路：identity vs downsample

| 情况 | shortcut 是什么 | 为什么 |
|---|---|---|
| 形状**相同**（C_in = C_out 且 stride=1） | **identity**（直接 `x`） | 维度一致，可以直接加 |
| 形状**不同** | **downsample**（1×1 conv + BN） | 通道或分辨率变了，加不起来，必须先对齐 |

实测各 stage 的 downsample 配置：

| stage | downsample conv | stride | 通道 |
|---|---|---|---|
| layer1 | 1×1 | 1 | 64→256 |
| layer2 | 1×1 | 2 | 256→512 |
| layer3 | 1×1 | 2 | 512→1024 |
| layer4 | 1×1 | 2 | 1024→2048 |

> [!note] 只有每个 stage 的**第 0 个块**有 downsample
> 因为 stride 只在 stage 边界处改变一次；
> stage 内部的所有块都保持形状，靠 identity 旁路。
> 实测确认：`layer2[0].conv2.stride=(2,2)`，而 `layer2[1].conv2.stride=(1,1)`。

---

## 3. 🔥 与 HazyDet 的对接：分层冻结

### 3.1 `frozen_stages` 到底冻了谁

mmdet 的 `ResNet` 有个参数 `frozen_stages`：

| 取值 | 冻结范围 | 可训参数（conv 部分） | 占比 |
|---|---|---|---|
| `-1`（默认） | 全不冻 | 23,508,032 | 100% |
| `0` | 冻 stem | 23,498,496 | 99.96% |
| **`1`** | 冻 stem + layer1 | **23,292,224** | **99.1%** |
| `2` | 冻 stem + layer1~2 | 22,072,640 | 93.9% |
| **`3`** | 冻 stem + layer1~3 | **14,964,736** | **63.7%** |
| `4` | 冻整个 backbone | 0 | 0% |

> [!danger] ⚠️ 冻结 ≠ 停止计算
> `frozen_stages=3` 时，**前向传播照走**（还要出特征给 FPN），
> 只是**不更新权重**（`requires_grad=False`）。
> 所以：
> - 参数量不变（还是 34.61M）✅
> - **FLOPs 也不变**（还是要算）✅
> - 省的是**显存中的梯度和优化器状态**，不是算力
>
> 👉 这也解释了为什么 Table 4 里 PDFT 的 GFLOPs 是 **184.32 → 184.32**，一点没变。

### 3.2 PDFT 两个阶段对应的冻结设置

回到 [[paper-notes/论文精读/3-HazyDet精读/06-PDFT渐进域微调精读|06-PDFT渐进域微调精读]]：

| PDFT 阶段 | 论文的 $\theta$ | mmdet 设置 | 训什么 |
|---|---|---|---|
| **Stage 1** | 冻 $\theta^1$ | `frozen_stages=1` | layer2+3+4 + FPN + head |
| **Stage 2** | 冻 $\{\theta^1, \theta^{2:k}\}$, k=3 | `frozen_stages=3` | **layer4 + FPN + head** |

> [!tip] 这就是为什么官方 config 的 `frozen_stages=1` 「恰好等于 PDFT Stage 1」
> 官方所有 config 都写了 `frozen_stages=1`，
> 但那是 mmdet 的**通用默认行为**（ImageNet 预训练微调的常规做法），**不是**论文的 PDFT。
> 巧合的是数值上正好一样 —— 所以 Stage 1 可以直接跑官方 config。

### 3.3 为什么冻 stage1-3 合理（物理直觉）

> [!important] 分层的"语义抽象程度"决定了它对雾的敏感度
>
> | 冻结的部分 | 学到的东西 | 雾会改变它吗？ |
> |---|---|---|
> | layer1 | 边缘、纹理、颜色梯度 | ❌ **不会** —— 雾是半透明罩子，边缘还在原地 |
> | layer2 | 局部形状、角点 | ❌ 基本不会 |
> | layer3 | 中层部件（车轮、车窗轮廓） | ⚠️ 部分会（对比度下降） |
> | **layer4** | **高层语义（"这是一辆车"）** | ✅ **会 —— 这正是雾要破坏的** |
>
> 👉 **要保护的是"跨域稳定"的低层，要适配的是"域相关"的高层。**
> 分层冻结刚好精确地对应这个物理划分。

> [!tip] 再叠加一个小样本因素
> Stage 2 只有 **400 张**真实雾图。
> 如果放开 layer1~3 让它们跟着这 400 张走，
> BN 的 running stats 也会被带偏（→ 必须配 `norm_eval=True`），
> 底层特征会朝这 400 张特有的风格过拟合。
> **冻结 = 强制底层保持"通用视觉常识"。**

### 3.4 参数账（本次 torchvision 实测）

| 部分 | 参数量 | 占 conv 部分 |
|---|---|---|
| stem (conv1 + bn1) | 9,536 | 0.04% |
| layer1 | 215,808 | 0.9% |
| layer2 | 1,219,584 | 5.2% |
| layer3 | 7,098,368 | 30.2% |
| **layer4** | **14,964,736** | **63.7%** |
| **合计** | **23,508,032** | 100% |

> [!note] 这张表的用处
> Stage 2 只训 layer4（14.96M）+ FPN（3.93M）+ head（≈3.3M）≈ **26.1M / 全模型 34.61M**。
> 也就是说：**PDFT 第二阶段更新的是那 63.7% 的大头**，
> 而"最通用"的前 36.3% 全部保持不动。

---

## 4. 容易搞混的几个点

### 4.1 ResNet18/34 和 50/101 的区别

| | ResNet18/34 | ResNet50/101 |
|---|---|---|
| 基本块 | **BasicBlock**（2 个 3×3） | **Bottleneck**（1×1→3×3→1×1） |
| 每 stage 块数 | 2,2,2,2 | **3,4,6,3** |
| layer4 通道 | 512 | **2048** |
| 常用场景 | 轻量、快速 | **检测/分割主流** |

> [!tip] 记法
> **18/34 = 2+2+2+2；50/101 = 3+4+6+3**。
> 检测 backbone 几乎都用 50 或 101（通道多、语义强）。

### 4.2 `style='pytorch'` vs `'caffe'`

HazyDet 的 config 里写了 `style='pytorch'`（`configs/vfnet/DeCoDet_vfnet_r50_fpn_1x_hazydet.py:22`）。

| | caffe 风格 | **pytorch 风格**（HazyDet 用这个） |
|---|---|---|
| stride 放在哪 | 放在第一个 1×1 上 | **放在 3×3 上** |
| conv4x4 | 否 | 否 |

实测：`layer2[0].conv2`（3×3）的 stride = **(2,2)**，而 `conv1`（1×1）stride = (1,1) → 确认是 pytorch 风格。

> [!note] 为什么重要
> caffe 风格**不做 zero-init**（残差分支最后一层 BN 初始化为 0）；
> pytorch 风格 `zero_init_residual=False`（默认）。
> 复现时若加载 ImageNet 权重发现对不上，先查 `style`。

### 4.3 `norm_eval` 与 `requires_grad=True` 并不矛盾

HazyDet config（`configs/vfnet/DeCoDet_vfnet_r50_fpn_1x_hazydet.py:20-21`）：

```python
norm_cfg=dict(type='BN', requires_grad=True),
norm_eval=True,
```

| 参数 | 管什么 |
|---|---|
| `norm_eval=True` | BN 的 **running mean/var 冻结不更新**（但推理时用它们归一化） |
| `requires_grad=True` | BN 的 **affine 参数 γ、β 仍然训练** |

> [!tip] 为什么要这么配
> **running stats 是"数据的统计量"**，γ、β 是"可学习的缩放平移"。
> 小数据微调（400 张）时：
> - running stats 会剧烈偏移 → 必须冻（`norm_eval=True`）
> - γ、β 只是每个通道的两个数 → 不会过拟合，可以继续学（`requires_grad=True`）
>
> 这是**小样本微调的经典配置**，不是矛盾。

---

## 5. ResNet50 → FPN：HazyDet 里怎么接的

config（`configs/vfnet/DeCoDet_vfnet_r50_fpn_1x_hazydet.py:24-31`）：

```python
neck=dict(
    type='FPN',
    in_channels=[256, 512, 1024, 2048],   # ← 正好是 layer1~4 的输出通道
    out_channels=256,                      # ← 统一成 256
    start_level=1,                         # ← 从 layer2 开始用
    add_extra_convs='on_output',           # ← P5 之后再加卷积
    num_outs=5,                            # ← P3~P7
    relu_before_extra_convs=True),
```

> [!important] `start_level=1` 是什么意思
> FPN 默认从**最高分辨率**的层开始（index 0 = layer1，stride 4）。
> `start_level=1` 表示**跳过 layer1，从 layer2（stride 8）开始**。
>
> 为什么跳过？
> - layer1 是 stride **4**，特征图太大（1333×800 输入 → 333×200），计算昂贵
> - 而且 stride 4 的特征**太细**，P3（stride 8）已经够用
> - **小目标信息在 P3 上仍保留**（FPN 会把高层语义**下采样**传下来）

### 5.1 FPN 输出的 5 级金字塔

| 层级 | 来源 | stride | 通道 | 对应 HazyDet 的检测尺度 |
|---|---|---|---|---|
| **P3** | layer2 | 8 | 256 | 小目标（无人机视角下车很远） |
| **P4** | layer3 | 16 | 256 | 中小目标 |
| **P5** | layer4 | 32 | 256 | 中大目标 |
| **P6** | P5 上加 3×3 conv (stride 2) | 64 | 256 | 大目标 |
| **P7** | P6 上加 3×3 conv (stride 2) | 128 | 256 | 极大目标 |

> [!tip] 和你之前问的那句对上
> 你之前提到「FPN 的每一级 $P_n \in \{P3,P4,P5,P6,P7\}$ 上接 M 个 3×3 卷积」
> —— **正是 MSDP 模块**（[[paper-notes/论文精读/3-HazyDet精读/05-DeCoDet原理精读|05-DeCoDet原理精读]] §MSDP）。
> MSDP 就是在 P3~P7 上并行生成**多尺度深度先验**，再送进 DCK 调制检测特征。

### 5.2 完整的数据流（HazyDet VFNet 版）

```
输入 3×800×1333
   │
   ▼  ResNet-50 backbone (frozen_stages=1)
  C2: 256 ×100×167   (stride 4)   ← 被 FPN 跳过（start_level=1）
  C3: 512 × 50×84    (stride 8)   ─┐
  C4: 1024× 25×42    (stride 16)  ─┼─► FPN ─► P3 P4 P5 (+P6 P7)  各 256 通道
  C5: 2048× 13×21    (stride 32)  ─┘
   │
   ▼  MSDP: 深度图 → M 层 3×3 conv → 多尺度深度先验 D^m
   │
   ▼  DCK: 用深度图生成卷积核 → 调制 P3~P7 的检测特征
   │
   ▼  VFNetDeCoDetHead: 3 个 3×3 conv (stacked_convs=3) → cls + reg
   │
   ▼  ATSS 分配正样本 → VFL(分类) + GIoU(回归) + SiLog(深度辅助)
```

> [!note] 注意 `out_indices=(0,1,2,3)`
> config 里 backbone 写 `out_indices=(0, 1, 2, 3)` —— 输出**全部 4 个 stage**，
> 由 FPN 的 `start_level=1` 来决定用哪几个。
> 这样 C2 虽然不用，但仍然会被算出来（因为 backbone 是顺序执行的）。

---

## 5.5 🔥 概念澄清：「输入 RGB，输出多尺度特征图」对吗？

> [!abstract] 一句话回答
> **方向对，但有三处需要精确化。**
> ① 它不是"只能输入 RGB"——ResNet 是**通道无关**的，换成红外/深度图也能用；
> ② "多尺度特征图"不是它的**设计目标**，而是**使用方式**（原始 ResNet50 的目标是分类）；
> ③ 更准确的说法：**它是一台"特征提取机"，本身不做任何决策。**

### 5.5.1 澄清①：ResNet 不认"RGB"，只认"3 个通道"

| 常见误解 | 实际情况 |
|---|---|
| "ResNet50 是 RGB 图像模型" | ❌ 它只看到 `3 × H × W` 的**浮点张量**，不知道什么叫红/绿/蓝 |

**证据**：HazyDet 里所有检测器的 backbone 输入通道都是 3（`data_preprocessor` 的 `mean`/`std` 各 3 个数），
但**图像内容完全不限 RGB**：

| 换什么进去 | 通道数 | 可行？ | 本项目里的例子 |
|---|---|---|---|
| 彩色 RGB | 3 | ✅ | HazyDet 合成雾 / 真实雾图 |
| **热红外 IR** | 3 | ✅ | Cross-Modal UAV 那篇（RGB+IR 配对） |
| **归一化深度图** | 1 → 复制成 3 | ✅ | HazyDet 的深度先验（转成 3 通道喂给 MSDP） |
| 伪彩色 | 3 | ✅ | 任何单通道图的"三通道化" |

> [!tip] 所以"通用"的准确含义
> **ResNet50 是一个"3 通道图像 → 多层特征"的通用函数逼近器**，
> 它对图像的**语义**（是雾是晴、是车是树）一无所知，
> 只对**像素统计**（边缘、纹理、对比度）有反应。
> 👉 这也解释了为什么**换域**（雾/晴天、RGB/IR）时它依然能初始化得很好——
> 低层的边缘/纹理提取器是**跨域通用**的，这正是 PDFT 敢冻 layer1 的物理基础。

### 5.5.2 澄清②："多尺度输出"是**使用方式**，不是原始设计

| | 原始 ResNet50（2015） | 检测里的 ResNet50 |
|---|---|---|
| 任务 | ImageNet **分类** | 特征提取 |
| 取哪一层 | 最后 layer4 → **1 个 2048 维向量** | **layer1~4 全取** → 4 张特征图 |
| 实现方式 | `forward` 返回 `x` | `out_indices=(0,1,2,3)` **把中间层截出来** |
| 分类头 `fc` | ✅ 用 | ❌ **丢弃** |

> [!important] `out_indices` 就是"我要哪几层"的开关
> **0 = layer1 (C2)、1 = layer2 (C3)、2 = layer3 (C4)、3 = layer4 (C5)**
>
> 📐 **实测 HazyDet 仓库里三种不同的取法**：
>
> | config | `out_indices` | 取到几级 | 颈部（neck）怎么处理 |
> |---|---|---|---|
> | VFNet / DeCoDet / FCOS / Faster-RCNN 等 | `(0,1,2,3)` | **4 级**（C2~C5） | FPN 融合成 P3~P7 |
> | **YOLOX** | `(2,3,4)` | **3 级**（C3~C5） | 自带 **PAN**（不是 FPN） |
> | **DAB-DETR** | `(3,)` | **1 级**（只有 C5） | `ChannelMapper` 1×1 压到 256 通道 |
>
> 👉 **同一个 ResNet50，被"截"在不同位置、接不同的颈部，就成了不同的检测器。**
> 这说明：**backbone 只是零件，输出什么形状由 `out_indices` 决定，不是 ResNet 的固有属性。**

### 5.5.3 澄清③：多尺度 ≠ "同一张图的多个缩放版本"

这是最容易误解的地方。多尺度特征**不是**把原图缩放几次，而是：

> **同一张图，在不同深度上"看"出来的结果。**

| | 空间分辨率 | 通道数 | 语义抽象程度 | 擅长 |
|---|---|---|---|---|
| **C2** (layer1) | **高**（1/4） | 少（256） | 低（边缘、纹理） | **小目标、细节定位** |
| **C3** (layer2) | 中（1/8） | 512 | 中 | 中等目标 |
| **C4** (layer3) | 低（1/16） | 1024 | 高（部件） | 大目标 |
| **C5** (layer4) | **最低**（1/32） | 2048 | **最高**（"这是一辆车"） | 大目标、整体语义 |

> [!tip] 为什么检测**必须**要多尺度
> 无人机俯视画面里，同样是"车"：
> - 远处一辆车可能只有 **20×12 像素**（要靠 C2 的高分辨率才看得见）
> - 近处一辆卡车可能有 **300×150 像素**（要靠 C5 的大感受野才认得出）
>
> **单一尺度必然顾此失彼**。
> 👉 而 FPN 的作用就是把 C5 的**语义**（强）**上采样**传给 C2（细），
> 让每一级都同时拥有"细定位 + 强语义"——**这才是 P3~P7 存在的意义**。

### 5.5.4 那"输出多尺度特征图"到底哪里对、哪里不精确？

| 你的表述 | 评价 |
|---|---|
| "输入 RGB 彩色" | ⚠️ **"RGB"是数据集属性，不是网络要求** → 改成"输入 3 通道图像张量" |
| "输出多尺度特征图" | ✅ **对**，但要补一句：**这是 `out_indices` 截出来的中间层，不是分类输出** |
| "通用的模型" | ✅ **对**，但通用性指的是**跨任务/跨域可复用**，且**它本身不做任务决策** |

> [!important] 完整的三段式心智模型（背下来）
>
> ```
> ┌─────────────┐   ┌──────────┐   ┌─────────────┐
> │   Backbone  │   │   Neck   │   │     Head    │
> │  (ResNet50) │──►│  (FPN)   │──►│  (VFNet头)  │
> └─────────────┘   └──────────┘   └─────────────┘
>   通用零件           尺度融合         任务决策
>   "看图"            "整理"          "下结论"
>   零任务知识         零任务知识      强任务知识
> ```
>
> | 部件 | HazyDet 里的具体配置 | 输出 |
> |---|---|---|
> | **Backbone** | ResNet-50, `out_indices=(0,1,2,3)`, `frozen_stages=1` | C2(256) C3(512) C4(1024) C5(2048) |
> | **Neck** | FPN, `out_channels=256`, `start_level=1`, `num_outs=5` | **P3~P7**，各 256 通道 |
> | **Head** | VFNetDeCoDetHead, `stacked_convs=3`, `num_classes=3` | 类别 + 框 + **深度图** |
>
> 👉 **换任务只换 Head，跨域只调 Backbone 的冻结/学习率**（这就是 PDFT 的位置）。
> 你在论文里看到的 `+10.0 mAP`，动的是**最上面那张表的第 3 段**。

### 5.5.5 自测

> [!tip] 思考题
> 1. 把 HazyDet 的图像换成**单通道深度图**直接喂给 ResNet50（不复制成 3 通道），会怎样？
>    → `conv1` 的输入通道是 3，**维度不匹配会直接报错**。所以要么复制成 3 通道，要么改 `conv1` 为 `Conv2d(1,64,...)`（此时该层权重需重新初始化）。
> 2. YOLOX 也用 `out_indices=(2,3,4)`，为什么它的 neck 不是 FPN 而是 PAN？
>    → PAN 是**自底向上**（把 C3 的细节往下传），FPN 是**自顶向下**（把 C5 的语义往下传）。
>    两种设计目的相同（多尺度融合），路径相反。
> 3. 如果只用 C5 一级（像 DAB-DETR），小目标会怎样？
>    → C5 是 stride 32，一张 20×12 的小车在 C5 上只剩 **不到 1 个像素**，几乎必然漏检。
>    DAB-DETR 靠 Transformer 的**全局注意力**跨层聚合来补救，这正是它比 CNN 检测器慢的原因。

---

## 6. 自测题

<details>
<summary>Q1：ResNet50 有几个 stage？每个 stage 几个块？</summary>

**A**：4 个 stage（layer1~4），块数分别是 **3、4、6、3**（共 16 个 Bottleneck）。
另外前面还有个 stem（conv1 7×7 + bn1 + maxpool）。

</details>

<details>
<summary>Q2：Bottleneck 为什么是 1×1 → 3×3 → 1×1？</summary>

**A**：为了**降计算量**。先 1×1 把通道掐到 1/4，让昂贵的 3×3 在窄通道上跑，
最后 1×1 撑回去。实测 layer3 一个块：直接 3×3 需 4.72M 参数，瓶颈只要 0.98M，**省 4.8 倍**。

</details>

<details>
<summary>Q3：残差连接解决的是"梯度消失"还是"过拟合"？</summary>

**A**：**梯度消失**（更准确说是"深层可训练性"）。
$y = F(x)+x$ 让每层只学残差量，反传时梯度有一条 $I$（单位矩阵）的"直通车"，不必连乘几十个雅可比。
过拟合是**另一个问题**，要靠数据增强/正则/冻结来解决。

</details>

<details>
<summary>Q4：哪个 stage 的哪个块有 downsample？为什么？</summary>

**A**：每个 stage 的**第 0 个块**有（1×1 conv + BN）。
因为 stride 只在 stage 边界改变一次，stage 内部形状不变，用 identity 旁路即可。

</details>

<details>
<summary>Q5：`frozen_stages=3` 冻了哪些层？还剩多少参数能训？</summary>

**A**：冻 stem + layer1 + layer2 + layer3。
conv 部分从 23,508,032 降到 **14,964,736（63.7%）**，只训 layer4。
加上 FPN + head ≈ **26.1M / 全模型 34.61M**。

</details>

<details>
<summary>Q6：`frozen_stages=3` 会减少 GFLOPs 吗？</summary>

**A**：**不会**。冻结只是不更新权重（`requires_grad=False`），
**前向传播照走**，FLOPs 完全不变。
这正是 PDFT 在 Table 4 里 GFLOPs 保持 184.32 的原因。

</details>

<details>
<summary>Q7：`norm_eval=True` 和 `requires_grad=True` 冲突吗？</summary>

**A**：**不冲突**。前者管 BN 的 running mean/var（冻结），后者管 BN 的 affine γ/β（继续训练）。
小样本微调（400 张真实雾）时的标准配置。

</details>

<details>
<summary>Q8：FPN 的 `start_level=1` 跳过了什么？为什么？</summary>

**A**：跳过 **layer1（stride 4）**，从 layer2（stride 8）开始。
原因：stride 4 特征图太大、计算贵；且 stride 4 太细，P3 已足够承载小目标信息。

</details>

---

## 🔗 相关笔记

- [[paper-notes/论文精读/3-HazyDet精读/06-PDFT渐进域微调精读|06-PDFT渐进域微调精读]] —— 本篇的直接下游（$\theta^1..\theta^4$ 就是这四段）
- [[paper-notes/论文精读/3-HazyDet精读/05-DeCoDet原理精读|05-DeCoDet原理精读]] —— MSDP / DCK 怎么用 FPN 的 P3~P7
- [[paper-notes/论文精读/1-CCFA-Net精读/01-公共基础知识/12-目标检测基础与mAP|12-目标检测基础与mAP]] —— FPN 与 mAP 的关系
- [[04-深度监督三件套与SiLog尺度性质]] —— 深度监督怎么挂在检测头上

## 🔗 本文（HazyDet）用在哪

| 本文内容 | 用在 HazyDet 的哪里 |
|---|---|
| ResNet50 四段划分 | PDFT Algorithm 1 的 $\theta^1 / \theta^{2:k}$ |
| 分层冻结参数账 | PDFT §2.3、§6.3 的 `frozen_stages` 设置 |
| `norm_eval=True` | VFNet config 第 21 行 |
| `style='pytorch'` | VFNet config 第 22 行 |
| FPN `start_level=1` / `num_outs=5` | VFNet config 第 24-31 行 → P3~P7 |
| MSDP 挂在 P3~P7 | [[paper-notes/论文精读/3-HazyDet精读/05-DeCoDet原理精读|05-DeCoDet原理精读]] §3 |

---

**← 上一篇** → [[04-深度监督三件套与SiLog尺度性质]] ｜ **下一篇 →** 无 ｜ **索引 →** [[00-公共基础总览]] ｜ **返回 →** [[paper-notes/论文精读/3-HazyDet精读/00-索引 MOC|HazyDet 索引]]
