# 复现路线图：Cross-Modal Object Detection via UAV

> 论文：Li et al., *Cross-Modal Object Detection via UAV*, IEEE T-VT, 2023, 72(8).
> **官方代码：无**（全文没有 GitHub 链接，也没有 Data Availability 声明，只写了 "The pytorch library is used for code implementation"）。
> 本文件回答那个最要命的问题：**没有代码，怎么复现？**

---

## 0. 一句话答案

> **复现 ≠ 拿到作者代码。**
> 复现 = 你自己把论文的公式翻译成代码 + 用论文给的超参训练 + 复现论文的数字。

这四篇论文（CCFA-Net、Cross-Modal UAV、HazyDet、HyperSpectral）**全部没有官方代码**，但它们都属于"信息足够"的类型——这才是判断一篇论文能不能复现的唯一标准，而不是"作者放没放 GitHub"。

---

## 1. 这篇论文为什么属于"好复现"

| 检查项 | 状态 | 说明 |
|---|---|---|
| 公式完整性 | ✅ | Eq.(1)–(14) 全部给出，没有"见附录/待补充" |
| 伪代码 | ✅ | Algorithm 1 完整（老师冻结、只更新学生） |
| 超参 | ✅ | `pi1=0.3`、`pi2=0.7`、`rho=0.7`、`lambda=0.5`、SGD、lr=1e-3、momentum=0.9、wd=5e-4、50 epochs、每 20 epoch ×0.1、batch=8、输入 840×712、hflip p=0.5 |
| 基线 | ✅ | Oriented R-CNN，**mmrotate 有现成 config** |
| 数据集 | ✅ | DroneVehicle 公开（需申请） |
| 需要自己写的量 | 小 | **只有 SFI + API 两个模块，约 300 行 PyTorch** |

**所以真实工作量不是"从零实现一篇论文"，而是"在现成检测器上挂两个蒸馏模块"。**

---

## 2. 分级复现：必须按顺序做

```
Level 0  基线 Oriented R-CNN 在 DroneVehicle 上             -> mAP 56.1   ← 90% 的人死在这
Level 1  基线 + SFI（特征蒸馏）                            -> mAP 59.2
Level 2  基线 + API（预测蒸馏）                            -> mAP 57.5
Level 3  基线 + SFI + API（完整模型）                       -> mAP 60.7
Level 4  消融：pi1 扫描 {0, 0.3, 1.0}、w_ciou 消融 {全用 / 全不用}
Level 5  对照组：IR+RGB 双检测器输出级融合                 -> mAP 63.2（推理成本翻倍）
```

**Level 0 是全部工作的门槛。** 如果基线本身没跑到 56.1，后面所有数字都没有意义。
很多"复现失败"的真实原因不是模块写错，而是**基线就没对齐**（旋转框评测口径、数据划分、anchor 设置、评测脚本不一致）。

### 为什么必须一级一级来

| 直接做 Level 3 会发生什么 |
|---|
| mAP 只有 58，比论文低 2.7 |
| 你不知道是 SFI 写错了、API 写错了，还是基线弱 |
| 三天改三个地方，最后不知道哪个改动有效 |

> 🎯 **类比**：像做菜复刻。第一步不是"同时炒三个菜"，而是先把**盐**的量做对——先炒一盘最简单的青菜，看看火候对不对。

---

## 3. 三条技术路线

| 路线 | 做法 | 工作量 | 风险 | 推荐度 |
|---|---|---|---|---|
| **A. mmrotate 魔改** | 用 mmrotate 现成的 Oriented R-CNN config，把 SFI / API 写成 `mmdet.models.BaseModule` + 自定义 pipeline | 小（~2 天） | 中（版本地狱：mmcv-full 要编译） | ✅ **首选** |
| **B. 纯 PyTorch 从零写** | 自己写 Rotated RPN / RoIAlign(rotated) / rotated NMS / 多边形 IoU | 数千行 | 极高 | ❌ 不要在第一篇做 |
| **C. 抄别人的 CKD 开源项目** | 找一个 cross-modal KD 的开源仓库当骨架，换成 Oriented R-CNN | 中 | 中（要读懂别人的代码） | 🟡 备选 |

> **为什么选 A**：论文的 baseline 就是 Oriented R-CNN，而 mmrotate 里有 `configs/oriented_rcnn/oriented_rcnn_r50_fpn_1x_dota_le90.py`。你只要：
> 1. 把 DroneVehicle 数据集注册成 `mmdet.Dataset`（官方仓库 `SunYM2020/UA-CMDet` 里**已经写好了** `mmdet/datasets/DroneVehicle.py`）
> 2. 加一个 `CrossModalDistill` 的 wrapper，把 SFI/API 接在 backbone 输出和 RPN/RoI head 输出上
> 3. 写 config，改 loss

### 关于 mmcv-full 在 Mac 上编译不了

这是**硬约束**：
- `mmcv-full` 只提供 Linux x86_64 的预编译轮子，**macOS / Apple Silicon 没有**；
- `mmrotate` 依赖的 `roi_align_rotated` / `psroi_align_rotated` / `poly_nms` 都是 **CUDA 扩展**，没有 CUDA 就编不过；
- 结论：**完整的 mmrotate 训练必须在 Linux GPU 机器上跑**。

但**本仓库里 `models/rotated_iou.py` 用纯 PyTorch 重写了多边形 IoU**（Sutherland–Hodgman 裁剪 + 鞋带公式），已通过蒙特卡洛校验（误差 < 0.02），所以 **API 模块的几何部分在 Mac 上就能跑通、就能验证**。

---

## 4. 你必须自己决定的 6 个"自由度"

论文没写的地方 —— 这既是**风险**，也是**你未来发论文的选题空间**。

| # | 自由度 | 论文写了什么 | 你要定什么 | 本仓库的默认 |
|---|---|---|---|---|
| 1 | **SFI 接 FPN 哪几层？** | 没说 | P2/P3/P4/P5 选哪些 | `feat_levels=('P4',)`，因为 `M` 是 `(H·W)×(H·W)` 矩阵，P2 会爆显存 |
| 2 | **Eq.(2) 分母的 L1 归一化** | 只说 "L1 normalization" | 全局标量？还是逐位置向量归一？ | `norm='l1_rowcol'`（逐行/逐列），另提供 `l2_cos`、`l1_global` |
| 3 | **M 要不要 clamp / softmax？** | 没说 | 相似度是否截断到 [0,1] | `clamp_sim=True` |
| 4 | **Eq.(4) 的矩阵方向** | 公式本身是**不对称**的（IR 用 `M`、RGB 用 `M`） | 字面照抄？还是对称化？ | `sim_mode='paper'`，另提供 `sim_mode='sym'` |
| 5 | **`w_ciou` 的归约粒度** | Eq.(6) 是逐目标，Eq.(7) 外面却套 `1/N Σ` | 逐目标加权后求均值？还是先求和？ | 逐目标加权后 `mean` |
| 6 | **老师/学生检测框怎么配对？** | 没说 | 贪心 IoU 匹配？匈牙利匹配？阈值多少？ | `greedy_iou_match`，阈值 0.5（可调） |

> 🎯 **类比**：论文给的是**乐谱**，不是**录音**。音符（公式、超参）全都在，但**节拍（对齐方式）、力度（损失尺度）、配器（接哪一层）**要你来定。复现的本质就是**把这些自由度收敛到论文的数字上**。

---

## 5. 硬件现实与分工（重要）

| 任务 | 你的 Mac M5 (arm64, 无 CUDA) | 需要 GPU 的部分 |
|---|---|---|
| 读论文 / 推公式 | ✅ | |
| 写 SFI / API 模块 | ✅ | |
| 写单元测试 + 合成数据 smoke test | ✅ **本仓库已全部通过（11/11）** | |
| 训练 IR 教师（Oriented R-CNN on IR） | ❌ | ✅ 需要 |
| 训练 RGB 学生（+SFI+API） | ❌ | ✅ 需要 |
| 评测 mAP | ❌（太慢） | ✅ 建议 |

论文原始配置：`2× Xeon E5-2695 v4 + 8× Tesla P100`，50 epochs，batch 8。

**最省时间的路径**：
1. 今晚：把本仓库的 `models/` 读懂，跑通 `tests/test_synthetic.py`（2 秒）
2. 同时：在学校超算 / 租一台 2080Ti / A10 申请到机器
3. 上机后：Level 0 基线 → Level 1 → Level 2 → Level 3，每一级都存 checkpoint 和 mAP

---

## 6. 本仓库已经完成的部分（今天就能用）

```
work/crossmodal-uav-repro/
├── models/
│   ├── rotated_iou.py   # 纯 PyTorch 多边形 IoU（Sutherland–Hodgman + 鞋带公式）
│   │                   #   ✅ 已用蒙特卡洛交叉验证（误差 < 0.02）
│   ├── sfi.py          # SFI：Eq.(2)–(5)，含 3 种归一化 / 2 种矩阵方向
│   ├── api.py          # API：Eq.(6)–(13)，w_ciou 加权 KL + smooth-L1
│   └── ckd.py          # Algorithm 1 训练循环 + 冻结教师 + SGD/StepLR
├── tests/
│   └── test_synthetic.py   # 11 个合成数据测试，全部通过
└── docs/
    ├── REPRO_PLAN.md       # 本文件
    └── PAPER_SPEC.md       # 公式 ↔ 代码 逐条对照表
```

运行方式：

```bash
cd /Users/yoyo/Documents/Codex/2026-10-28/xxx/work/crossmodal-uav-repro
/Users/yoyo/Documents/Codex/2026-10-28/xxx/.venv-pip/bin/python tests/test_synthetic.py
```

环境：Python 3.9.6 + PyTorch 2.2.2 (CPU)，venv 在 `/Users/yoyo/Documents/Codex/2026-10-28/xxx/.venv-pip`。

---

## 7. 下一步的三件事（按优先级）

1. **确认硬件**：实验室/学校有可用 GPU 服务器吗？租/借一台大概什么价位？
2. **确认数据**：DroneVehicle 需要在官方页面申请，拿到之后确认目录结构（`train/ir`, `train/rgb`, `train/label`）。
3. **写 Level 0 的配置**：基于 `SunYM2020/UA-CMDet` 的 `configs/DroneVehicle/UACMDet.py` + mmrotate 的 Oriented R-CNN config 合并。
