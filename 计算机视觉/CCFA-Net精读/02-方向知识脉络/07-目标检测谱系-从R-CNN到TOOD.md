---
tags: [方向脉络, 目标检测, 检测谱系, anchor-free, DETR, TOOD, ATSS, FCOS, 知识地图, CV]
aliases: [目标检测谱系, 检测技术地图, 从R-CNN到TOOD, 检测算法脉络]
created: 2026-11-04
related: [13-两阶段检测与R-CNN家族, 12-目标检测基础与mAP, 09-第8讲-TOOD检测头精讲, 00-方向地图总览]
track: 方向脉络
status: 已完成
---

# 07 · 目标检测谱系：从 R-CNN 到 TOOD

## 0. 这篇笔记在整张地图里的位置

[[00-方向地图总览]] 把你的方向拆成了五条主线。**检测谱系是其中最"工程化"的一条**——它不像去雾那样有漂亮的物理模型，而是一条由**几十篇论文、一堆小改动**堆出来的技术路线。

它的价值在于：
1. 你以后读任何一篇检测论文，它的 Table 1 一定是一张谱系表——看不懂这张表就抓不住"这篇的贡献是补了哪一格"；
2. **CCFA-Net 的检测器选型，本质就是在谱系上选了一个坐标点**，这个选型是有代价的（见第 5 节）。

---

## 1. 五条分支：一张图看清整个领域

```
                        目标检测
                            │
    ┌───────────────────────┼───────────────────────┐
    │                       │                       │
【两阶段】               【单阶段】              【集合式 / DETR 线】
 先找后认                密集预测                 无 anchor + 无 NMS
    │                       │                       │
 R-CNN(14)                SSD(15)                 DETR(20)
   ↓ 共享卷积              ↓                      ↓
Fast R-CNN(15)           YOLO(16)                Deformable DETR(21)
   ↓ RoI Pooling          ↓ 锚框+多尺度           ↓ 可变形注意力
Faster R-CNN(15)        RetinaNet(17)          DINO(22)
   ↓ RPN + anchor        ↓ Focal Loss            ↓ 对比去噪 + 混合查询
Cascade R-CNN(17)       FCOS(19) ← 去 anchor
   ↓ 三阶段精修          ↓ 逐点预测
Mask R-CNN(17)          ATSS(20) ← 动态样本分配
   ↓ RoIAlign            ↓
                        TOOD(21) ← 任务对齐
                            ↑
                        ★ CCFA-Net 用的是这一格
```

**三条线的关系（一句话各一条）：**
- **两阶段**："候选框"是显式的一等公民；精度传统上更高，慢。
- **单阶段**：没有显式候选框，靠**密集点 + 样本分配规则**决定谁负责预测；这一支的**全部难点都压在"样本分配"四个字上**——ATSS、TOOD 都是攻这一关。
- **DETR 线**：把检测看成"集合预测"，用匈牙利匹配一对一分配正样本，从根上消掉了 anchor 和 NMS；但早期训练慢、小目标弱。

---

## 2. 关键节点表（记住"谁解决了什么"比记住年份重要）

| 年份 | 代表 | 核心贡献一句话 | anchor? | 两阶段? |
|---|---|---|---|---|
| 2014 | R-CNN | 深度特征 + 区域提议，证明这条路可行 | 否（Selective Search） | 是 |
| 2015 | Fast R-CNN | 共享卷积 + RoI Pooling + 端到端 | 否 | 是 |
| 2015 | Faster R-CNN | **RPN** 生成 proposals，与 backbone 共享特征 | **是（k=9）** | 是 |
| 2016 | SSD / YOLO | 单阶段密集预测，工业界转向速度 | 是 / 是 | 否 |
| 2017 | RetinaNet | **Focal Loss** 解决正负失衡 | 是 | 否 |
| 2017 | Mask R-CNN | RoI **Align** + 实例分割分支 | 是 | 是 |
| 2017 | Cascade R-CNN | 三阶段逐级精修，抑制 IoU 对定位质量的敏感性 | 是 | 是 |
| 2019 | FCOS | **彻底去掉 anchor**，逐点预测 + centerness | **否** | 否 |
| 2020 | ATSS | **自适应训练样本选择**（动态 top-k） | 否 | 否 |
| 2020 | DETR | 集合预测 + 匈牙利匹配，端到端去 NMS | 否 | 否（但有 query） |
| 2021 | **TOOD** | **任务对齐**：按分类×定位质量分配样本，分离分类/回归任务 | 否 | 否 |
| 2021 | Deformable DETR | 多尺度可变形注意力，修小目标与收敛速度 | 否 | 否 |

> [!tip] 看这张表的正确姿势
> **不要背年份，背"每个节点动了哪个零件"**：
> R-CNN 动"流程"→Fast 动"算得快"→Faster 动"候选框来源"→RetinaNet 动"损失函数"→FCOS 动"anchor"→ATSS 动"样本分配"→TOOD 动"样本分配 + 任务解耦"→DETR 动"匹配机制"。
> 这七个零件，基本就是检测领域的全部矛盾点。

---

## 3. 三次重大转折（理解检测史的骨架）

**转折一：从"手工提议"到"网络提议"（RPN, 2015）**
候选框从不可导的启发式算法 → 可导的 RPN。梯度第一次能穿过"提议"这一层回到 backbone。

**转折二：从"固定 IoU 阈值"到"动态样本分配"（ATSS / TOOD, 2020–2021）**
两阶段靠人工设定的 IoU 阈值（0.7/0.3）划正负；单阶段更惨，密集点上 99% 是背景。
- **ATSS**：对每个真值框，按**定位质量（centerness）**从附近选 top-k 个点当正样本 → "自适应地"确定正负。
- **TOOD**：进一步认为"分类好"和"定位好"**不一定是同一批点**（这就是 TOOD 论文里的 task misalignment 现象）。于是 TOOD 做两件事：
  1. **任务对齐的样本分配（TAL）**：用 `分类得分 × 定位质量` 的对齐度排序挑候选，让被挑中的点**分类和回归都得到高质量监督**；
  2. **分类/回归特征解耦**：分类分支和回归分支用不同的特征（回归分支多几层），减少任务间干扰。

> 🎯 比喻
> 老办法是"考试分数 + 体育成绩"两个指标**分开**录取，各取各的前几名，可能录进来一个考试好但体育差的人。
> TOOD 改成"找一个**两项都靠前**的人"（对齐），并且**分类用一套教材、回归用另一套教材**（解耦），互不干扰。

**转折三：从"密集预测"到"集合预测"（DETR, 2020）**
不再问"哪些点是目标"，而是直接把检测看成"输出 N 个元素的集合"，用**匈牙利匹配**一对一分配真值。
优点：彻底去掉 anchor 与 NMS；缺点：早期收敛慢、小目标弱（Deformable DETR、DINO 都在补这个短板）。

---

## 4. TOOD 在图上的精确坐标（读本文检测头的钥匙）

**仓库实测**（`configs/tood/tood_r50_fpn_1x_hazydet.py`）：

| 配置项 | 值 | 说明 |
|---|---|---|
| `bbox_head.type` | `TOODHead` | 6 层 stacked convs，`feat_channels=256` |
| `anchor_type` | **anchor_free** | 不用 anchor 框，走逐点预测 |
| `anchor_generator` | `ratios=[1.0]`, `octave_base_scale=8`, `scales_per_octave=1`, `strides=[8,16,32,64,128]` | **只为每个位置算一个"基准尺度"**，供 ATSS 分配器用 |
| `initial_assigner` | `ATSSAssigner(topk=9)` | 前 4 个 epoch 用 ATSS 的动态 top-k 分配 |
| `assigner` | `TaskAlignedAssigner(topk=13)`, `alpha=1`, `beta=6` | 之后切到任务对齐分配 |
| `initial_epoch` | **4** | 论文里说的"分阶段迭代训练"在这里落地 |
| `initial_loss_cls` | `FocalLoss(gamma=2.0, alpha=0.25)` | 前期用普通 focal |
| `loss_cls` | `QualityFocalLoss(beta=2.0)` | 后期换成**质量感知**的 focal（用定位质量加权分类） |
| `loss_bbox` | `GIoULoss(weight=2.0)` | 回归用 GIoU |
| `bbox_coder` | `DeltaXYWHBBoxCoder(target_stds=[0.1,0.1,0.2,0.2])` | 回归 4 个相对偏移 |

**一句话坐标：TOOD = FCOS 的 anchor-free 逐点预测 + ATSS 的动态样本分配 + 任务对齐（TAL）+ 分类/回归解耦。**

---

## 5. 官方仓库的 22 个 baseline 配置 = 论文对比表的"横截面"

仓库 `configs/` 目录里完整备了这些 baseline 配置，**它们几乎一一对应论文 Table 2 与 Table 7 的方法**：

| 配置目录 | 谱系位置 | 论文里对应 |
|---|---|---|
| `faster_rcnn` / `cascade_rcnn` / `dynamic_rcnn` / `libra_rcnn` | 两阶段 | Table 7 / 补充对比 |
| `atts` / `fcos` / `gfl` / `vfnet` | 单阶段 anchor-free | FCOS 在 Table 2；ATSS 是 TOOD 的前身 |
| `tood` | **本文采用** | 消融表的 baseline（mAP 50.8） |
| `yolov3` / `yolox` | 单阶段实时 | Table 7 的轻量参照 |
| `centernet` | 无 anchor 的关键点派 | Table 2（47.2） |
| `reppoints` | 无 anchor 的点集派 | — |
| `detr` / `deform_detr` / `conditional_detr` / `dab_detr` / `ddod` / `sparse_rcnn` | DETR 系 | Table 2 里的 Deformable DETR（51.5） |
| `deform_detr` | — | DeCoDet 底层组件 |

> [!tip] 怎么用这张"横截面"
> **把仓库当地图的横截面来读**：每个配置 30~80 行，改几个超参就是"在这个坐标点上换配置再测一次"。
> 想做实验的话，**换检测器 = 换一个配置目录**，这是最低成本的实验设计方式。

---

## 6. 必须掌握到什么程度（分层清单）

| 层次 | 内容 | 判定标准 |
|---|---|---|
| ✅ 必会 · 概念层 | 两阶段 vs 单阶段；RPN 干什么；anchor 是什么；ATSS/TOOD 在解决"样本分配" | 能一句话说清 TOOD 相对 ATSS 多了什么 |
| ✅ 必会 · 机制层 | RoI Pooling/RoIAlign；IoU 阈值定正负；Focal Loss 解决什么；TAL 的对齐度 | 能解释 TOOD 配置里每一项超参存在的理由 |
| ⭕ 选会 · 谱系层 | DETR 系、匈牙利匹配、query 的含义 | 读懂 Table 2 里 Deformable DETR 那一行 |
| ❌ 不用会 | R-CNN 的 Selective Search 实现、SVM 细节、各论文的 VOC 数字 | 知道存在即可 |

---

## 7. 批判视角：本文的检测器选型其实是可以质疑的

把谱系摊开看，CCFA-Net 的检测器选型有三个值得追问的地方：

**追问一：为什么用 TOOD，而不是 Table 2 里更强的那几个？**
Table 2 里 Deformable DETR = **51.5**、DiffusionDet = 51.0、DeCoDet = 51.5，而消融表里的 TOOD baseline = **50.8**。
同一张表里换检测器反而更高。论文没有解释选型理由。

**追问二：TOOD 的 `initial_epoch=4` 是本文设置的还是 TOOD 原版？**
仓库配置里 `initial_epoch=4` 写在 TOOD 配置里。但论文的实验设置只说"SGD、24 epoch、lr 0.01"，**没说这 4 个 epoch 的分阶段策略**。这属于复现时容易漏掉的隐藏细节（详见 [[11-第10讲-评价指标与复现必查项]]）。

**追问三：baseline 配置本身就带着 bug。**
仓库里 `configs/atts/...` 的 `ATSSHead` 写的是 `num_classes=80`，而 HazyDet 只有 3 个类（Car/Truck/Bus）——**这是从 COCO 配置复制过来忘了改**。
→ **如果谁直接跑这份 ATSS baseline，得到的数字是错的。** 这是你以后复现任何 baseline 前都要做的第一件事：检查 `num_classes`。

> [!danger] 这三条的共同教训
> **读论文的 Table 2 时，一定要问"baseline 的超参和训练设置公平吗"。**
> 检测器的选择往往会带来 ±1~2 mAP 的差异，而本文的三个模块合计带来 50.8 → 54.6（+3.8）——**检测器选型的影响和模块贡献是同一个量级**，论文却把讨论全给了模块。这是你做汇报时的一个高质量提问点。

---

## 8. 与方向地图上其他笔记的关系

| 邻居笔记 | 关系 |
|---|---|
| [[01-图像复原谱系-从DCP到DehazeFormer]] | 上游的"看"：复原谱系 |
| [[02-恶劣天气视觉与数据集]] | 数据从哪来（退化如何影响检测） |
| [[03-域适应域泛化与测试时适应]] | 换数据集测 = 泛化性测试，本文跨了 4 个数据集 |
| [[04-多任务学习与梯度冲突]] | 检测器与去雾分支的梯度关系 |
| [[05-注意力机制谱系]] | MFAM 的血缘（CA、Strip Pooling） |
| [[06-遥感UAV检测的特有问题]] | 本篇的"遥感特殊性"：小目标、尺度剧变、密集遮挡 |

---

## 9. 自测题

> [!question]- Q1 · 一句话说清：TOOD 相对 ATSS 多了什么？
> **答：** ATSS 按定位质量动态选 top-k 个正样本；TOOD 改用**任务对齐度**（分类得分 × 定位质量）选候选，并让分类分支与回归分支**用不同特征**，减少任务间相互干扰。

> [!question]- Q2 · 检测史上的"三次转折"分别是什么？
> **答：** ① 手工提议 → RPN 网络提议；② 固定 IoU 阈值 → 动态样本分配（ATSS/TAL）；③ 密集预测 + NMS → 集合预测（DETR，匈牙利匹配）。

> [!question]- Q3 · 为什么说"CCFA-Net 的检测器选型有争议"？
> **答：** 同表里 Deformable DETR / DeCoDet 都是 51.5，高于 TOOD baseline 的 50.8；论文未解释为何仍选 TOOD；且 baseline 配置里 ATSS 还留着 `num_classes=80` 的 bug。

> [!question]- Q4 · 本文的"级联不稳定"和 Cascade R-CNN 是一回事吗？
> **答：** 不是。前者指去雾→检测的模型串联流水线；后者是一个检测器内部的三个 head 级联精修。

> [!question]- Q5 · 仓库里 22 个 baseline 配置对你意味着什么？
> **答：** 它们是这张谱系图的"可执行横截面"——换检测器 = 换配置目录，是最低成本的对比实验设计方式；但跑之前必须先查 `num_classes` 这类硬伤。
