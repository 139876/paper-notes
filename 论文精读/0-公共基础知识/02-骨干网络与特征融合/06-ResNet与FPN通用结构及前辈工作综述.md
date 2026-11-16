---
tags: [公共基础, ResNet, FPN, 特征金字塔, 小目标, 域适应, 恶劣天气, 综述, 无人机检测, 选题]
aliases: [ResNet与FPN通用结构, FPN 改进综述, 前辈工作梳理]
created: 2026-11-12
stage: 3 · 综述
series: 基础 · 第 06 篇
related: "[[paper-notes/论文精读/0-公共基础知识/00-公共知识总览]]", "[[05-ResNet50结构与分层冻结]]", "[[paper-notes/论文精读/3-HazyDet精读/05-DeCoDet原理精读]]", "[[paper-notes/论文精读/3-HazyDet精读/06-PDFT渐进域微调精读]]"
track: 公共基础
---

# 06 · ResNet & FPN 的通用结构 + 前辈改进工作梳理

> [!abstract] 本讲要回答
> 1. **最初的** ResNet 是什么结构？（原始论文版本，不是 mmdet 改版）
> 2. **最初的** FPN 是什么结构？（原始论文 2017 版本）
> 3. 🔥 **你的方向上，前辈们做过哪些改进？** 是不是已经把路走完了？
> 4. 哪些坑已经被踩过（别重复劳动）？哪些还是空白（你的机会）？

> [!note] 你的方向定位（基于你在读的四篇）
> | 论文 | 在你的方向里的角色 |
> |---|---|
> | CCFA-Net | **目标论文**：去雾 + 跨域协同(CCDD) + 跨域特征融合(CFFM) + 多尺度前景感知(MFAM) |
> | Cross-Modal UAV | 跨模态：SFI 选择性特征模仿 + API 自适应预测模仿（蒸馏） |
> | HazyDet | **数据集地基**：合成雾 + 真实雾 + 深度标注；DeCoDet（MSDP+DCK）+ PDFT |
> | 跨域高光谱 | 域偏移三来源 + JVC 联合变量一致性 + ASI 锚点结构不变性 + DBFDF 双分支 |
>
> 👉 浓缩成一句话：**无人机视角 + 雾天（恶劣天气）+ 跨域 + 多尺度/前景 + 多模态融合**

---

## 第一部分 · 最初的 ResNet（He et al. 2015）

### 1.1 原始论文的通用结构

**基本单元 = Residual Block**（不是 Bottleneck，ResNet-18/34 用的是 BasicBlock）：

```
x ──────────────────────────┐
                            │  (identity 或 projection shortcut)
      conv3×3 → BN → ReLU    │
      conv3×3 → BN           │
                            │
      ▼                      ▼
   out = F(x) + shortcut(x)  ──► ReLU
```

**原始 ResNet-34 的层级表**（论文 Table 1 的通用形式）：

| 阶段 | 块类型 | 重复次数 | 输出通道 | 输出 stride |
|---|---|---|---|---|
| conv1 | 7×7, 64, stride 2 | 1 | 64 | 2 |
| conv2_x | 3×3 BasicBlock | **3** | 64 | 4 |
| conv3_x | 3×3 BasicBlock | **4** | 128 | 8 |
| conv4_x | 3×3 BasicBlock | **6** | 256 | 16 |
| conv5_x | 3×3 BasicBlock | **3** | 512 | 32 |

> [!important] 原始 ResNet 的两个"通用约定"
> ① **只在 stage 边界改变分辨率**（stride 2），stage 内部 stride 恒为 1
> ② **shortcut 分两种**：形状相同用 identity；通道数翻倍用 **1×1 projection shortcut**（参数化投影）
>
> ⚠️ 注意：ResNet-50/101 换成 Bottleneck 后，shortcut 的 projection **仍然是 1×1 conv**，
> 但 Bottleneck 内部多了一层 1×1 降维 —— **两者不要混淆**。

### 1.2 论文里最容易被忽略的两个"配套发明"

| 技术 | 做法 | 为什么重要 |
|---|---|---|
| **zero-init 残差分支** | 每个残差分支的**最后一个 BN 初始化为 0** | 训练一开始整个网络 = 恒等映射，再逐步学残差 |
| **He 初始化** | 按通道数缩放方差 | 与残差结构配套，缓解早期梯度问题 |

> [!tip] 记住这两条，因为它们是"你改造 ResNet 时不能破坏的东西"
> 你的方向上如果想改 ResNet（比如加深度分支），**保留 identity shortcut 和 zero-init**，
> 否则深层的训练稳定性会立刻崩掉。

---

## 第二部分 · 最初的 FPN（Lin et al. CVPR 2017）

### 2.1 原始论文的通用结构

论文原名《Feature Pyramid Networks for Object Detection》。核心是**两条通路**：

```
              ┌─────────────────────────────────────────┐
  Backbone    │                                         │
  (ResNet)    │   C5 (stride 32) ──1×1──► C5lat ──┐    │  ← 自顶向下
              │                        ▲            │    │
              │   C4 (stride 16) ──1×1──► C4lat ──┴─► ⊕ ──3×3──► P4
              │                        ▲            │      ↑
              │   C3 (stride 8)  ──1×1──► C3lat ──┴─► ⊕ ──3×3──► P3
              │                        ▲                   ↑
              │   C2 (stride 4)  ──1×1──► C2lat ──┴─► ⊕ ──3×3──► P2
              │                                            │
              └────────────────────────────────────────────┘
                                                             
   P6 = conv3×3(stride 2) on P5     (仅用于检测，原文也提)
```

### 2.2 三个关键设计（这三点是 FPN 的"通用骨架"，所有改进都围绕它们）

| # | 设计 | 具体做法 | 为什么 |
|---|---|---|---|
| 1 | **Lateral connection** | 每个 C_i 用 **1×1 conv** 降到统一通道数（原论文 **256**） | 统一维度才能相加；1×1 不改空间分辨率 |
| 2 | **Top-down pathway** | 高层特征 **2× 最近邻上采样** 后与 lateral 相加 | 上采样必须用**最近邻**（反卷积会学出棋盘伪影） |
| 3 | **输出 smoothing** | 相加后再过 **3×3 conv** | 消除上采样的混叠（aliasing） |

> [!important] 原始 FPN 的输出层级是 **P2~P5**（stride 4~32）+ P6
> 而**检测领域后来普遍改成 P3~P7**（stride 8~128）：
> - 跳过 P2（stride 4 太贵、特征太碎）
> - 增加 P6/P7 覆盖超大目标
> 👉 HazyDet 用的是 **P3~P7**（`start_level=1`, `num_outs=5`）。

### 2.3 FPN 的两个"原始动机"（很多人不知道）

| 动机 | 说明 |
|---|---|
| **① 解决尺度不变性** | 单一尺度特征无法同时检测大/小目标 → 金字塔给出多个尺度 |
| **② 特征复用 + 额外训练数据** | FPN 在**多尺度特征上**都算 loss，**间接**让 backbone 学到更多有用特征（论文用 ImageNet 检测数据 + COCO 联合训练验证） |

> [!tip] 第 ② 点是你的方向上最值得记的
> **FPN 不只是"给检测头准备输入"，它本身就是一个强大的多尺度训练信号。**
> HazyDet 的 **MSDP**（多尺度深度先验）正是在 P3~P7 上并行生成分支 —— 属于"把 FPN 当成多尺度载体"的思路。

---

### 2.4 🔌 三段式接口契约：`in_channels` / `out_channels` 到底在说什么

> [!abstract] 一句话
> **`in_channels` = 我这个模块准备吃的那张输入特征图有几个通道。**
> 它是模块之间的「接口契约」：上游必须真的给我这么多通道，否则代码直接报错。

#### ① 通道（channel）是什么

一张特征图可以写成 `H × W × C`：

- `H × W` = 空间尺寸（特征图有多大）
- `C` = **通道数**（这张特征图有几"层"信息）

自然图像是 `H × W × 3`（R/G/B）；ResNet-50 的 C4 是 `H/16 × W/16 × 1024`。

> [!important] 通道不是"颜色"
> RGB 只是**输入图像**的 3 个通道。进入网络之后，通道变成**特征图的厚度**：
> 每一层放一种"检测线索"（"边缘在哪""这是车轮纹理""这里像车顶"）。
> `C` 越大 = 每层携带的信息越丰富。

#### ② 在检测器里，`in_channels` 出现在三处

| 位置 | 参数 | HazyDet 里的值 | 含义 |
|---|---|---|---|
| Backbone | `in_channels` | `3`（默认值，config 没写） | 输入是 RGB 图 |
| Neck (FPN) | `in_channels` | `[256, 512, 1024, 2048]` | 一次吃 4 个尺度的特征 |
| Neck (FPN) | `out_channels` | `256` | 输出统一成 256 通道 |
| Head | `in_channels` | `256` | 吃 Neck 交上来的 P3~P7 |
| Head | `feat_channels` | `256` | Head 内部中间卷积也保持 256 |

对应代码（HazyDet 官方 config）：
`configs/vfnet/DeCoDet_vfnet_r50_fpn_1x_hazydet.py`

```python
backbone=dict(type='ResNet', depth=50, out_indices=(0,1,2,3), frozen_stages=1, ...),
neck=dict(type='FPN', in_channels=[256,512,1024,2048], out_channels=256,
          start_level=1, add_extra_convs='on_output', num_outs=5, ...),
bbox_head=dict(type='VFNetDeCoDetHead', in_channels=256, feat_channels=256,
               stacked_convs=3, strides=[8,16,32,64,128], ...),
```

#### ③ 数据在流水线里的形状变化

```
输入图像            3 × H × W
  ↓ stem (7×7 s2)  64 × H/2 × W/2
  ↓ layer1         256 × H/4 × W/4      ← C2   (out_indices=0)
  ↓ layer2         512 × H/8 × W/8      ← C3   (out_indices=1)
  ↓ layer3        1024 × H/16 × W/16    ← C4   (out_indices=2)
  ↓ layer4        2048 × H/32 × W/32    ← C5   (out_indices=3)
  ↓ FPN (in=256/512/1024/2048 → out=256)
  P3 256×H/8×W/8    P4 256×H/16×W/16    P5 256×H/32×W/32
  P6 256×H/64×W/64  P7 256×H/128×W/128
  ↓ VFNetDeCoDetHead (in=256, strides=[8,16,32,64,128])
类别 logits / 回归框 / 深度图
```

#### ④ 为什么必须对得上（机制层面）

卷积核的权重形状是 `[out_channels, in_channels, kH, kW]`：

- 3×3、256→256 的卷积 = `256 × 256 × 3 × 3` = **589,824** 个参数
- 那个 `in_channels=256` 的意思是"每个输出通道都要去看这 256 个输入通道"

维度对不上会**直接报错**，不会静默算错：

```
RuntimeError: Given groups=1, weight of size [256, 128, 3, 3],
expected input[1, 256, H, W] to have 128 channels
```

#### ⑤ 最常见的复现坑：换 backbone 忘了改 neck

把 ResNet-50 换成 Swin / ConvNeXt / EfficientNet 之后，各阶段通道数全变，
**Neck 的 `in_channels` 必须同步改**，否则 FPN 第一层就崩。

这是"改论文配置"时最常见的报错来源之一。

#### ⑥ 别把三个 3 搞混

| 数字 | 参数名 | 在哪 | 含义 |
|---|---|---|---|
| 3 | `backbone.in_channels` | Backbone | 图像的 RGB 通道 |
| 3 | `num_classes` | Head | 目标类别数（HazyDet：car / truck / bus） |
| 256 | `in_channels` / `out_channels` | Neck / Head | 特征图通道数 |

前两个 3 **毫无关系**，只是碰巧相等。

#### ⑦ 口诀

> 一个模块的 `in_channels` = 上一个模块的 `out_channels`。
> 通道数在 Neck 这一层被"统一"（FPN 的 `out_channels=256`），
> 正是为了让 **Head 能用同一套权重处理 P3~P7 五个尺度**。

---

## 第三部分 · 🔥 前辈们做过的改进（你的方向）

> [!note] 分类原则
> 我按**"改进的是哪一层"**来组织，而不是按时间流水账 ——
> 这样你能直接看出**哪个位置还有空间**。

### 3.1 改进 Backbone 的路线

| 年份 | 工作 | 核心改进 | 与你的关系 |
|---|---|---|---|
| 2015 | **ResNet** | 残差连接，让深网络可训 | 一切的地基 |
| 2017 | **ResNeXt** | 分组卷积（cardinality），**宽度换深度** | ⭐ **HazyDet 的 DCK 用的就是 grouped conv（group=16）**，思想同源 |
| 2017 | **DenseNet** | 特征复用（concat 而非 add） | 对比 FPN 的 add，可做"add vs concat"的消融 |
| 2018 | **SE-Net / CBAM** | 通道注意力 / 通道+空间注意力 | ⭐ **CCFA-Net 的 MFAM 就是"多尺度前景感知"的注意力变体** |
| 2017 | **Deformable Conv** | 可变形卷积，采样点自适应偏移 | ⭐ **HazyDet 的 DCK 是"用深度生成卷积核"**，与可变形卷积是同一族思想 |
| 2021/22 | **ConvNeXt / RepVGG** | 纯卷积现代化改造 | 说明"纯卷积还有空间" |

> [!important] 你必须知道的三条"路线图"
> ```
> ResNet(2015) ──► 分组/多分支(ResNeXt) ──► 注意力(SE/CBAM) ──► 动态采样(DCN)
>                                    ↓
>                      HazyDet DCK 落在这里（深度生成卷积核）
>                      CCFA-Net MFAM 落在这里（多尺度前景注意力）
> ```

### 3.2 改进 Neck（FPN）的路线 —— **你最该重点看的**

| 年份 | 工作 | 核心改进 | 与你的关系 |
|---|---|---|---|
| 2017 | **FPN**（原始） | 单向自顶向下 | 基线 |
| 2019 | **PANet** | 加**自底向上**路径 → 双向信息流 | ⭐ **YOLOX 用的就是 PAN**（HazyDet Table 3 里有） |
| 2019 | **NAS-FPN** | 神经架构搜索自动设计连接拓扑 | 说明"融合路径本身可以搜" |
| 2019 | **ASFF** | **空间自适应**加权融合（解决层间冲突） | ⭐ 对"雾天不同层信息可靠性不同"很契合 |
| 2020 | **BiFPN** | 可学习**加权**双向融合 + 跨层连接 + 剪掉单输入节点 | 效率优先的代表 |
| 2020 | **DCNv2 / DCP** | 可变形金字塔 | 与 DCK 呼应 |

> [!tip] FPN 改进的四条主线（背下来）
> ```
> ① 加路径:   FPN(单向) → PANet(双向) → BiFPN(双向+加权)
> ② 加权重:   固定 add → ASFF(空间加权) / BiFPN(可学习加权)
> ③ 换搜索:   手工设计 → NAS-FPN(自动搜拓扑)
> ④ 换采样:   固定网格 → DCNv2(可变形采样)
> ```
> 👉 **CCFA-Net 的 CFFM（跨域特征融合）走的正是 ①+② 路线**。

### 3.3 改进"恶劣天气 / 雾天检测"的路线

| 年份 | 工作 | 核心思路 |
|---|---|---|
| 2009 | **DCP**（暗通道先验） | 去雾的物理起点；**CCFA-Net 第 1 讲**讲的就是它 |
| 2016/19 | **D-HAZE / Dense-HAZE** | 去雾数据集 |
| 2019 | **GridDehazeNet** (ICCV'19) | 注意力多尺度去雾 |
| 2020 | **FFA-Net** (AAAI'20) | 特征融合注意力去雾 |
| 2020 | **Seeing Through Fog** (CVPR'20) | **不看雾看雾** —— 多模态(相机+LiDAR+radar)在雾中做检测；**同时提供了 12000 真实样本 + 1500 雾室样本** |
| 2020 | **DSNet** (TPAMI) | 恶劣天气下的联合语义学习（**HazyDet 引用**） |
| 2022 | **IA-YOLO** (AAAI'22) | **图像自适应** YOLO（**HazyDet 引用**，Table 3 有） |
| 2021 | **MS-DAYOLO** (ICIP'21) | **多尺度域自适应 YOLO**（**HazyDet 引用**，Table 3 有） |

> [!important] 这条线的历史包袱
> **「先去雾，再检测」**是早期主流（HazyDet Table 7 就在做这个对比），
> 但它有**根本缺陷**：
> ① 去雾会**丢纹理**，小目标本来就没几个像素，经过去雾网络更糊
> ② 去雾是**有损**的、不可逆的
> ③ 误差会**级联**传给检测器
>
> 👉 **HazyDet 的 DeCoDet 明确"不做显式去雾"（eschewing explicit dehazing）**，
> 直接让网络在雾里学 —— 这是它与前辈的分水岭。
> **CCFA-Net 反而走的是"去雾 + 跨域协同"路线**，你需要想清楚它为什么敢这么做。

### 3.4 改进"跨域 / 域适应"的路线 —— **PDFT 所在的赛道**

| 年份 | 工作 | 核心思路 |
|---|---|---|
| 2015 | **DANN** | 对抗域适应（特征对齐） |
| 2018 | **Domain Adaptive Faster R-CNN** | 检测器的域适应标准范式（图像级+实例级对齐） |
| 2018 | **AdaBN / DSBN** | **按域切分 BN 统计量**（域特定 BN） |
| 2020 | **Adaptive Teacher** (ECCV'20) | 半监督域适应 |
| 2022 | **Unbiased Teacher** (CVPR'22) | 半自监督域适应 |
| — | **HazyDet 的 PDFT** | **两阶段渐进微调**（合成→真实），零参数，+10.0 mAP |

> [!danger] 你必须知道的一个关键事实
> **PDFT 本质上是"域特定 BN + 冻结 + 降 lr"的组合**，而 **AdaBN (2018) 早就在做"域特定 BN"**了。
> HazyDet 的贡献点在于：**把它和"分层冻结"绑定成一套训练范式，并证明它零参数**。
>
> 👉 这意味着：**"域适应"这个大方向，你如果只是"再做一个 PDFT 变体"，创新性有限。**

### 3.5 改进"深度作为辅助线索"的路线

| 年份 | 工作 | 核心思路 |
|---|---|---|
| 2014 | **Eigen et al.** | 单目深度估计（**HazyDet 引用的 SiLog 出处**） |
| 2022 | **ZoeDepth** | 相对+度量深度零样本迁移（**HazyDet 引用**） |
| 2023 | **Metric3D v2** | **度量深度基础模型**（**HazyDet 引用**，实测最优） |
| 2024 | **UniDepth / VA-DepthNet / IEBins** | 通用深度估计器（**HazyDet 全部引用**） |
| 2017 | **DCK / Deformable DETR** | **动态卷积核**（HazyDet DCK 的直系来源） |

> [!tip] HazyDet 的深度路线其实很"保守"
> 它**没有自己训深度模型**，而是**拿现成的 Metric3D 生成的伪深度**当先验，
> 再用 SIRLoss 处理噪声。Table S2 对比了 5 个深度估计器（VA-DepthNet / ZoeDepth / IEBins / UniDepth / Metric3D）。

### 3.6 改进"多尺度 + 小目标 + 前景感知"的路线

| 年份 | 工作 | 核心思路 | 与你的关系 |
|---|---|---|---|
| 2018 | **DARKNET** (ICCV'18) | **无人机检测基准**（**HazyDet 引用**） | 数据集地基 |
| 2019 | **Clustered Object Detection** | 聚类先验用于航拍检测（**HazyDet 引用**） | |
| 2020 | **QueryDet** | 级联稀疏查询加速高分辨率小目标（**HazyDet 引用**） | |
| 2021 | **Global-Local Self-Adaptive** (TIP'21) | 全局-局部自适应（**HazyDet 引用**） | |
| 2022 | **UFPMP-Det** (AAAI'22) | 无人机小目标（**HazyDet 引用**） | |
| 2024 | **MFSSD** (TGRS'24) | 多尺度特征融合小目标（**HazyDet 引用**） | ⭐ **和 CCFA-Net 的 MFAM 直接撞名同方向** |
| 2018 | **FAM / 前景感知** | 前景-背景分离 | ⭐ **CCFA-Net 的 MFAM** |

---

## 第四部分 · 空白在哪里（你的机会）

> [!danger] 别踩的坑（前人已做，别重复）
> - ❌ 单纯"加一个注意力模块" —— SE/CBAM/ASFF/MFAM 都被做烂了
> - ❌ 单纯"把 FPN 换成 BiFPN/PANet" —— 这是配置改动，不是研究贡献
> - ❌ 单纯"用更好的深度估计器" —— HazyDet Table S2 已经全试过
> - ❌ 单纯"再做一个 PDFT 变体" —— AdaBN 早就做过度特定 BN

> [!important] 可能还有空间的方向（结合四篇论文的交叉空白）
>
> | # | 方向 | 为什么可能是空白 | 对应你的哪篇论文 |
> |---|---|---|---|
> | 1 | **雾的"深度分层"建模** | 大多数去雾/域适应方法把雾当**全局**变量；但 HazyDet 的深度数据证明**雾的退化是按深度分层的**。现有工作几乎没人显式按深度分层做去雾/对齐 | HazyDet 深度标注 × CCFA-Net 去雾 |
> | 2 | **"不用深度图也能用深度知识"** | HazyDet 证明深度有用，但**真实雾没有深度标注**（PDFT 的痛点）。做**单目深度估计 + 自训练**闭环 | HazyDet §4.2 PDFT |
> | 3 | **合成雾的"物理真实性"评估** | 合成雾都是大气散射模型合成的，**真实雾有湍流、局部不均**。做"合成→真实"的**雾属性迁移** | HazyDet 数据构造 |
> | 4 | **跨域的"尺度-退化"联合建模** | 深度同时决定**退化程度**和**表观尺度**（HazyDet Fig. S4 证明）。现有跨域方法把这两件事分开做 | HazyDet §4.1 → CCFA-Net MFAM |
> | 5 | **多模态（RGB+IR）在雾天** | Seeing Through Fog 证明了多模态在雾里有用，但那是**自驾场景**；**无人机 + 雾 + IR** 没人系统做过 | Cross-Modal UAV × HazyDet |
> | 6 | **不做去雾的雾天检测** | DeCoDet 明确"eschew explicit dehazing"，但**系统对比"显式去雾 vs 隐式"**只有 HazyDet Table 7 一张表，还可以做深 | CCFA-Net（它走的是显式路线）|

> [!tip] 最推荐的组合（给新入学研究生的现实建议）
> **方向 2 + 方向 4**：
> "**深度作为桥梁的合成→真实域适应**，且**按深度分层地**做特征对齐"
> - 理由 1：HazyDet 已经把**数据和深度标注**给你了，起点比从零做高
> - 理由 2：CCFA-Net 的 CCDD/CFFM 已经在做跨域融合，你可以在**它的框架上**替换/升级对齐机制
> - 理由 3：PDFT 的"深度只在训练期用"这个设定，**天然引出"推理期怎么用深度"**这个问题 —— 而 HazyDet 说"真实雾没深度"，这正是空白
> - 理由 4：实现成本低 —— PDFT 官方零实现，但 Stage 1 直接能跑官方 config

---

## 第五部分 · 一张总表：你读的四篇论文 vs 前辈工作

| 你的论文 | 它站在哪条前辈线上 | 它的"新"在哪 |
|---|---|---|
| **CCFA-Net** | 去雾(DCP→FFA/GridDehaze) + 跨域融合(ASFF/BiFPN 线) + 前景感知(FAM) | 三者**耦合**成一套端到端框架（CCDD/CFFM/MFAM） |
| **Cross-Modal UAV** | 知识蒸馏(Hinton→CRD) + 跨模态对齐 | **选择性**特征模仿（SFI）+ **自适应**预测模仿（API） |
| **HazyDet** | 域适应(AdaBN→PDFT) + 深度先验(ZoeDepth→Metric3D) + DCK(Deformable Conv) | ①**首个**无人机雾天大规模基准 ②深度做成**内在模态** ③零参数 PDFT |
| **跨域高光谱** | 域偏移(JVC/ASI) + 双分支 | 光谱**分辨率**作为域偏移第三来源 |

---

## 🔗 相关笔记

- [[05-ResNet50结构与分层冻结]] —— ResNet 的历史贡献 + 四段结构 + 冻结参数账
- [[paper-notes/论文精读/3-HazyDet精读/05-DeCoDet原理精读|05-DeCoDet原理精读]] —— MSDP/DCK 怎么改造 FPN 的 P3~P7
- [[paper-notes/论文精读/3-HazyDet精读/06-PDFT渐进域微调精读|06-PDFT渐进域微调精读]] —— PDFT 在哪条赛道上
- [[paper-notes/论文精读/1-CCFA-Net精读/01-论文精读/08-第7讲-MFAM多尺度前景感知|第7讲 MFAM]] —— 前景感知这条线
- [[paper-notes/论文精读/1-CCFA-Net精读/01-论文精读/07-第6讲-CFFM跨域特征融合|第6讲 CFFM]] —— 跨域特征融合这条线

## 🔗 本文（HazyDet）用在哪

| 本文内容 | 用在 HazyDet 的哪里 |
|---|---|
| FPN 原始结构与 P3~P7 演变 | VFNet config 的 `start_level=1` / `num_outs=5` |
| MSDP 挂在 P3~P7 | §4.1 多尺度深度先验 |
| DCK ↔ Deformable Conv 同源 | §4.1 动态卷积核 |
| PDFT ↔ AdaBN 谱系 | §4.2 |
| 前辈工作表（63 条引用） | §5.2 Benchmark、Related Work |

---

**← 上一篇** → [[05-ResNet50结构与分层冻结]] ｜ **下一篇 →** 无 ｜ **索引 →** [[paper-notes/论文精读/0-公共基础知识/00-公共知识总览]] ｜ **返回 →** [[paper-notes/论文精读/3-HazyDet精读/00-索引 MOC|HazyDet 索引]]

