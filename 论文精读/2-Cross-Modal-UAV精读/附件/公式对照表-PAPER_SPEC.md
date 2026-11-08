# 公式 ↔ 代码 逐条对照表

> 论文：Li et al., *Cross-Modal Object Detection via UAV*, IEEE T-VT 2023, 72(8): 10898–10909.
> 每一行都注明了**代码在哪**、**论文哪里没说清楚**、**我们默认怎么做的**。

---

## 一、整体框架（Algorithm 1，p.7）

| 论文 | 代码 | 备注 |
|---|---|---|
| 老师 `theta_IR` 冻结 | `models/ckd.py::CKDFramework.__init__` 里 `requires_grad_(False)` + `teacher.eval()` | 论文："their parameters do not need to be further updated" |
| 只更新学生 `theta_RGB` | `models/ckd.py::build_optimizer` 只取 `framework.student.parameters()` | |
| `L = L_f + L_cls + L_loc`（Eq.14） | `models/ckd.py::CKDFramework.forward` 的 `total` | 论文里没有 `L_det` 这一项——我们额外保留了学生自己的检测损失（`det_weight`，默认 1.0），因为 Eq.(8) 的 `L_CE` 本质上就是检测器的分类损失 |
| 推理时删掉 IR 检测器 + SFI + API | 只部署 `student` | 论文 Section III-E |

---

## 二、SFI（Eq.2–5）

| 论文 | 公式 | 代码 | 未说明之处 |
|---|---|---|---|
| Eq.(2) | `M = (F_IR · F_RGB) / (‖F_IR‖₁ ‖F_RGB‖₁)` | `sfi.py::SFI._similarity` | 分母是**全局标量**还是**逐位置向量**？→ 默认 `l1_rowcol`；另备 `l2_cos` / `l1_global` |
| Eq.(3) | `M_bar = 1 - M` | `sfi.py::SFI.forward` | 是否需要 clamp → 默认 clamp 到 [0,1]（T(.) 有 ReU，特征非负，所以余弦天然 ∈[0,1]） |
| Eq.(4) | `F_com_IR = M·F_IR`，`F_com_RGB = F_RGB·M`，残差同理用 `M_bar` | `sfi.py::SFI.forward` | **公式本身不对称**（IR 用 `M`，RGB 也用 `M`，方向相反）→ 默认 `sim_mode='paper'` 字面实现；`sim_mode='sym'` 用 `0.5(M+Mᵀ)` 做对称版本 |
| Eq.(5) | `L_f = π₁‖F_com_IR − F_com_RGB‖² + π₂‖F_res_IR − F_res_RGB‖²` | `sfi.py::SFI._distance` | `‖·‖²` 是 Frobenius 范数还是逐元素 MSE？→ 默认 `frobenius`；`reduction='mse'` 可切 |
| T(·) | Conv3×3 → BN → ReLU | `sfi.py::TransformBlock` | Fig.3 里画的层序（Conv-BN-ReLU vs ReLU-BN-Conv）前后不一致，正文只列了三个组件 → 用正文顺序 |

### ⚠️ 显存红线：`M` 是 `(H·W)×(H·W)` 矩阵

输入 840×712，FPN 各层：

| 层 | stride | 特征图 | H·W | `M` 的大小 | fp32 显存 |
|---|---|---|---|---|---|
| P2 | 4 | 210×178 | 37 380 | 37 380² | **≈ 5.6 GB** ❌ |
| P3 | 8 | 105×89 | 9 345 | 9 345² | ≈ 350 MB 🟡 |
| P4 | 16 | 52×44 | 2 288 | 2 288² | ≈ 21 MB ✅ |
| P5 | 32 | 26×22 | 572 | 572² | ≈ 1.3 MB ✅ |

→ **SFI 只能接在 P4/P5**，或者先做空间池化。代码里 `max_hw=4096` 会在超限时直接报错并提示（`SFI refuses an oversized similarity map`）。

---

## 三、API（Eq.6–13）

| 论文 | 公式 | 代码 | 未说明之处 |
|---|---|---|---|
| Eq.(6) | `w_ciou = Area(D_RGB ∩ D_IR) / Area(D_RGB ∪ D_IR)` | `models/rotated_iou.py::rotated_iou_pairwise` + `api.py::API._match` | 老师/学生的框怎么配对？→ 贪心 IoU 匹配，阈值 `match_iou_thr=0.5` |
| Eq.(7) | `L_KL = w_ciou · (1/N) Σ_i Σ_k p_IR,k log(p_IR,k / p_RGB,k)` | `api.py::API.forward` | `1/N` 的 N 是 batch size 还是目标数？→ 逐目标加权后取 **matched objects 的均值** |
| Eq.(8) | `L_CE = (1/N) Σ_i Σ_k y_k log p_RGB,k` | `api.py::API._gt_terms` | 学生检测框 ↔ GT 的对应关系没说 → 用 IoU>0.5 挂载；未挂上的检测框当**背景**处理（`-log(1-p_max)`） |
| Eq.(9) | `L_cls = ρ·L_KL + (1−ρ)·L_CE`，`ρ=0.7` | `api.py::API.forward` | ✅ 论文给了 |
| Eq.(10) | `L_ts_loc = w_ciou · ‖R_IR − R_RGB‖²₂` | `api.py::API.forward` | R 是 4 个顶点 → 8 个数；‖·‖² 取 Frobenius |
| Eq.(11)(12) | `L_sl_loc = (1/4)Σ_j z_j`，`z_j` 为 smooth-L1 | `api.py::smooth_l1_pointwise` | `z_j` 是对**顶点距离**还是对**8 个坐标**做 smooth-L1？→ 默认 `sl1_mode='vector'`（对顶点距离，忠实于 Eq.11-12）；`elementwise` 可切 |
| Eq.(13) | `L_loc = λ·L_ts_loc + (1−λ)·L_sl_loc`，`λ=0.5` | `api.py::API.forward` | ✅ 论文给了 |

### 论文**没有**的东西（复现时必须自己加）

- **temperature**：全文 0 次。KL 用**原始 softmax** 概率。作者引用的 [32] 是带 T 的，但本文没写 → 复现时先用 T=1，并把它列为消融项。
- **老师的检测结果怎么来的**：老师是一个**已经在 IR 图像上训练好的 Oriented R-CNN**（论文 Section III-A），IR 图像的标注来自 DroneVehicle 的 IR 标注文件。

---

## 四、实验设置（p.7, Section IV-A）

| 项 | 值 |
|---|---|
| Backbone | ResNet-50 + FPN |
| 检测器 | Oriented R-CNN |
| 输入尺寸 | 840 × 712 |
| 数据增强 | 随机水平翻转 p=0.5 |
| 优化器 | SGD，lr=0.001，momentum=0.9，weight_decay=0.0005 |
| 调度 | 每 20 epoch lr × 0.1 |
| Epochs | 50 |
| Batch size | 8 |
| `π₁` / `π₂` | 0.3 / 0.7 |
| `ρ` / `λ` | 0.7 / 0.5 |
| 硬件 | 2× Xeon E5-2695 v4 + 8× Tesla P100 |

代码对应：`models/ckd.py::build_optimizer`（SGD 超参）、`build_lr_scheduler`（StepLR 20 / γ=0.1）。

---

## 五、数据集与评测

- **DroneVehicle**：28 439 对 IR-RGB，训练 17 990 / 测试 10 449（原验证集并入测试集），5 类（car, truck, bus, van, freight car），**旋转框**标注（4 顶点）。
- 官方代码仓库（数据集论文 T-CSVT 2022）：`https://github.com/SunYM2020/UA-CMDet`
  - 已包含 `mmdet/datasets/DroneVehicle.py`、`two_stream_DroneVehicle.py`、`rotate_aug.py`、`anchor_target_rbbox.py`、`rbbox_nms.py`、`eval/DroneVehicleEval.py`
  - ⚠️ 里面的 `roi_align_rotated` / `psroi_align_rotated` / `poly_nms` 是 **CUDA 扩展**，Mac 上编译不过
- **评测**：mAP，IoU > 0.5 记为 TP；多边形 IoU 的实现见 `models/rotated_iou.py`（可与官方 `eval/polyiou.py` 对拍验证）。

---

## 六、主结果与消融（论文数字，供对表）

| 配置 | mAP |
|---|---|
| RGB Oriented R-CNN（单模态基线） | 56.1 |
| 本文完整模型（推理只用 RGB） | **60.7** |
| IR+RGB 双检测器输出级融合（推理成本翻倍） | 63.2 |

| 消融 | mAP |
|---|---|
| +SFI only | 59.2 |
| +API only | 57.5 |
| +SFI +API | 60.7 |
| `π₁` = 0 / 0.3 / 1.0 | 58.54 / **59.21** / 58.29 |
| `w_ciou` 全用 / 全不用 | 57.5 / 56.9 |

> `π₁` 扫描那组数字比"完整模型 60.7"低，说明该消融是在**只加 SFI**的配置下做的 —— 复现时要对齐消融的基线，否则数字对不上。
