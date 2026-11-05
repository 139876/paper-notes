# 面向 IEEE TVT 的无人机跨场景泛化与感知友好去雾研究方案

> 整理日期：2026-10-29  
> 研究定位：面向低空无人机交通感知的跨场景泛化、感知友好去雾与可靠目标检测。  
> 说明：本文为前述讨论的研究规划汇总；论文元数据、代码可用性和数据集下载状态应在正式开题前逐项复核。

## 1. 期刊匹配与研究背景

IEEE Transactions on Vehicular Technology（TVT）并不要求所有论文都以地面汽车自动驾驶为背景。其研究范围包括无人机（UAV）等自主载具系统。因此，**以无人机为平台开展雾天视觉感知研究是可行的**。

但投稿时应突出无人机系统或交通应用价值，而非仅在通用图像去雾数据集上优化 PSNR、SSIM。建议采用**无人机辅助交通监测**作为首选场景：在雾天航拍图像中检测车辆，提升跨地区、跨天气和跨成像条件的检测可靠性。无人机自主避障也可作为备选，但对数据和安全验证的要求更高。

## 2. 推荐研究主线

**中文暂定题目：** 面向无人机交通感知的任务驱动域泛化去雾方法  
**英文暂定题目：** *Task-Oriented Domain-Generalized Dehazing for Robust UAV-Based Traffic Perception*

核心研究问题：在**不使用未见目标域进行训练或模型选择**的前提下，去雾模型能否在不同地点、飞行高度、摄像头和雾浓度条件下，稳定改善无人机车辆检测性能？

研究应围绕三个互相支撑的方面：

1. **图像复原：** 恢复雾天目标的结构和判别信息，减少伪纹理与过度增强。
2. **跨场景域泛化：** 利用多个可用源域或源域增强条件，学习跨雾浓度、成像条件和场景的稳定表征；严格区分域泛化（DG）与使用目标域数据的域适应（UDA）。
3. **感知友好优化：** 让目标检测任务反向指导去雾，并通过可靠性或置信度机制避免错误恢复损害检测。

可考虑附加轻量化目标，评估机载计算资源下的时延与吞吐量。

## 3. 与地面自动驾驶路线的比较

| 维度 | 地面自动驾驶去雾 | 无人机去雾 |
|---|---|---|
| TVT 范围 | 明确匹配 | 明确匹配 |
| 与遥感/跨场景技术积累衔接 | 中等 | 较强 |
| 去雾与检测协同 | 研究成熟、竞争激烈 | 已有直接竞争论文 |
| 数据和开源基础 | 较成熟 | 有专用航拍雾天检测数据 |
| 应用表述 | 车辆前视感知 | UAV 交通监测或自主感知 |
| 部署关注 | 车载实时性 | 机载算力、时延和能耗 |

**选择建议：** 优先考虑无人机交通监测，但不能仅将“自动驾驶”替换为“无人机”；应明确航拍小目标、跨域变化和检测可靠性这些独特问题。

## 4. 必读文献与用途

### 4.1 TVT 期刊对标论文

1. **Haze Visibility Enhancement for Promoting Traffic Situational Awareness in Vision-Enabled Intelligent Transportation**. IEEE TVT, 2023.  
   DOI：https://doi.org/10.1109/TVT.2023.3298041  
   **用途：** 理解交通场景去雾论文如何组织方法贡献、视觉恢复指标与下游感知实验；不宜默认其仓库具备完整训练代码。

2. **Cross-Modal Object Detection Via UAV**. IEEE TVT, 2023.  
   DOI：https://doi.org/10.1109/TVT.2023.3262129  
   **用途：** 证明 UAV 航拍目标检测可作为 TVT 论文的研究主体，学习跨模态感知与模型效率的应用论证。

3. **Offloading Deep Learning Powered Vision Tasks from UAV to 5G Edge Server with Denoising**. IEEE TVT, 2023.  
   DOI：https://doi.org/10.1109/TVT.2023.3243529  
   **用途：** 理解 UAV 图像恢复、感知任务与实际系统约束的结合方式。注意其主要处理通信噪声和边缘卸载，而非天气去雾。

### 4.2 核心方法与竞争论文

4. **HazyDet: Open-Source Benchmark for Drone-View Object Detection With Depth Cues in Hazy Scenes**. IEEE TGRS, 2026（具体出版信息待复核）。  
   DOI：https://doi.org/10.1109/TGRS.2026.3701819  
   代码及数据：https://github.com/GrokCV/HazyDet  
   **用途：** 首选 UAV 雾天目标检测数据与 DeCoDet 检测框架复现起点；应核验训练配置、权重和数据链接。

5. **CCFA-Net: Cross-domain collaborative and foreground-aware for UAV object detection in hazy scenes**. ISPRS Journal of Photogrammetry and Remote Sensing, 2026.  
   DOI：https://doi.org/10.1016/j.isprsjprs.2026.04.020  
   代码：https://github.com/XFCV26/CCFA-Net  
   **用途：** 直接竞争工作，研究去雾—检测协同、特征融合和小目标增强；重点区分其“跨域特征协同”与严格的未见域泛化。

6. **Vision Transformers for Single Image Dehazing（DehazeFormer）**. IEEE TIP, 2023.  
   代码：https://github.com/IDKiro/DehazeFormer  
   **用途：** 去雾子网络主干基线；仓库提供训练、测试、权重和数据准备入口。注意数据通常需要另行下载。

7. **Rethinking Performance Gains in Image Dehazing Networks（gUNet）**.  
   代码：https://github.com/IDKiro/gUNet  
   **用途：** 轻量化去雾主干备选，适合算力有限或强调机载部署时使用。

8. **FriendNet: Detection-Friendly Dehazing Network**. 2024 预印本。  
   代码：https://github.com/yihua-fan/FriendNet  
   **用途：** 学习检测反馈引导去雾的设计。**注意：** 此前检查发现仓库训练说明与实际文件可能不一致，正式选为基线前必须验证可训练性。

9. **Detection-Friendly Dehazing: Object Detection in Real-World Hazy Scenes（BAD-Net）**.  
   **用途：** 学习雾图/去雾图双分支检测特征融合，以及如何降低错误恢复带来的检测损失；具体出版元数据和官方代码须复核。

10. **CoA: Towards Real Image Dehazing via Compression-and-Adaptation**. CVPR, 2025.  
    论文：https://openaccess.thecvf.com/content/CVPR2025/html/Ma_CoA_Towards_Real_Image_Dehazing_via_Compression-and-Adaptation_CVPR_2025_paper.html  
    代码：https://github.com/YanZhang-zy/CoA  
    **用途：** 学习合成到真实去雾的域适应和效率设计；注意不能将 UDA 直接称为 DG。

11. **PDDA: Prompt-Driven Domain Adaptation for Real-World Image Dehazing**. IEEE TIP, 2026.  
    DOI：https://doi.org/10.1109/TIP.2026.3684402  
    **用途：** 了解最新提示驱动域适应，避免泛泛地宣称首次进行跨域去雾。

12. **Disentanglement-wise Image Dehazing through Cross-Domain Manifold Consensus**. CVPR, 2026.  
    论文：https://openaccess.thecvf.com/content/CVPR2026/html/Lyu_Disentanglement-wise_Image_Dehazing_through_Cross-Domain_Manifold_Consensus_CVPR_2026_paper.html  
    **用途：** 对比跨域流形一致性、特征解耦和物理先验方法，界定创新边界。

13. **Driving-Video Dehazing with Non-Aligned Regularization for Safety Assistance（DVD）**. CVPR, 2024.  
    论文：https://openaccess.thecvf.com/content/CVPR2024/html/Fan_Driving-Video_Dehazing_with_Non-Aligned_Regularization_for_Safety_Assistance_CVPR_2024_paper.html  
    代码：https://github.com/IP-Dehaze/DVD  
    **用途：** 如扩展到无人机视频去雾，可学习真实场景非对齐训练和时序信息；第一篇稿件不必优先实现视频版本。

## 5. 核心基线怎么选？

**结论：应当选择公开训练/测试代码、权重、数据获取方式和评估协议的核心基线。**

- **UAV 检测主基线：** 优先 HazyDet / DeCoDet。它更直接对应航拍雾天车辆检测，适合建立完整任务协议。
- **去雾主干基线：** DehazeFormer；若强调轻量化或算力不足，则优先 gUNet。
- **最直接竞争方法：** CCFA-Net。若其完整代码可运行，应纳入对比；不能只与传统去雾网络比较。
- **方法参考：** FriendNet、BAD-Net、CoA、PDDA 等。它们不必全部作为可训练主干，但应在相关工作和创新分析中明确区分。

**开题前基线验收清单：**

- [ ] 仓库包含实际训练脚本和推理脚本（不仅有 README）。
- [ ] 权重文件能够下载、加载并完成推理。
- [ ] 数据集能下载，许可和使用范围明确。
- [ ] 数据标注、类别映射、训练/验证/测试划分清晰。
- [ ] 能在指定软硬件环境复现论文主要指标或解释偏差。
- [ ] 可以插入去雾、特征对齐和检测反馈模块。

## 6. 数据集与实验协议

| 数据集 | 作用 | 关键注意事项 |
|---|---|---|
| HazyDet | UAV 合成雾训练、验证和测试 | 核对 Car/Truck/Bus 类别、图像数量与官方划分 |
| RDDTS | 真实雾 UAV 目标检测 | 尽可能保留为严格未见目标域 |
| VisDrone | 多场景航拍目标检测 | 核对类别映射；若用于源域训练，不可再声称是未见测试域 |
| A2I2-Haze | 真实雾、可量化雾浓度及检测相关评估 | 核对无人机/地面视角子集、配对关系与标注可用性 |
| RESIDE | 通用去雾预训练 | 与 UAV 真实场景存在分布差异 |
| Foggy Cityscapes / ACDC | 地面驾驶场景的辅助对照 | 不宜直接替代 UAV 核心测试 |

此前讨论中 HazyDet 被描述为 8,000 张训练、1,000 张验证、2,000 张测试，以及 RDDTS 600 张真实雾数据；这些具体数字须以实际下载版本和论文附录为准。

**严格 DG 协议：** 在源域训练、在源域验证集选超参数、在未见真实雾域进行最终一次性评估。若使用目标域无标签图像参与训练，应将实验明确标记为 UDA 或测试时适应，而不是纯 DG。

**核心指标：** 目标检测 mAP、AP_small、分类别 AP/Recall、漏检率；去雾 PSNR/SSIM（仅在有配对真值时）、真实场景无参考指标；参数量、FLOPs、推理延迟、显存占用；不同雾浓度和场景下的性能方差。

## 7. 建议的方法框架

```text
源域 UAV 图像 / 合成多浓度雾
               │
       去雾主干（DehazeFormer / gUNet）
               │
     结构恢复与不确定性估计
               │
   类别条件特征—预测联合一致性
               │
     目标检测反馈与可靠性加权
               │
      未见真实雾域车辆检测评估
```

### 拟研究的三个贡献点

1. **面向 UAV 小目标的可靠性引导恢复：** 根据雾浓度、目标区域和恢复不确定性调整增强强度，减少小车辆边缘和纹理丢失。
2. **类别条件的跨源域一致性：** 联合建模目标区域特征与类别预测，使不同源域条件下的目标判别结构保持稳定；可将其作为待验证的创新假设，而不是预先认定有效。
3. **检测友好的端到端优化与效率评估：** 在恢复质量和检测性能之间进行可控权衡，报告机载推理代价。

形式化地，可以探索源域间的联合分布约束：

$$
P_s(z,\hat y)\approx P_{s'}(z,\hat y),
$$

其中 $z$ 表示目标区域特征，$\hat y$ 表示类别预测，$s,s'$ 表示不同可用源域或源域增强条件。该式只是研究思路，实际损失函数、伪标签可信度和优化稳定性需通过实验论证。

## 8. 必须做的对比与消融

**基本对比：**

1. 雾图直接检测；
2. DehazeFormer/gUNet 去雾后检测；
3. 仅增强检测器训练（不新增去雾模块）；
4. 去雾与检测简单联合训练；
5. DeCoDet 与 CCFA-Net（在统一协议下）；
6. 提出的方法。

**关键消融：** 去掉类别条件一致性、去掉可靠性估计、去掉检测反馈、替换为普通特征一致性、改变雾浓度与目标尺寸、评估未见域性能与计算成本。

应特别证明：提升并非仅来自更多训练数据、更强的数据增强、更大模型或检测器额外微调。

## 9. 建议的四阶段实施计划

| 阶段 | 任务 | 交付物 |
|---|---|---|
| 1. 文献与可复现性核验 | 精读 TVT 对标、HazyDet、CCFA-Net、DehazeFormer | 文献对比矩阵、仓库/数据核验报告 |
| 2. 基线复现 | 运行 HazyDet/DeCoDet 和至少一种去雾主干 | 指标复现表、训练环境、检测可视化 |
| 3. 跨场景诊断 | 源域训练，未见真实雾域测试 | 按雾浓度、场景、目标尺度划分的失效分析 |
| 4. 创新与消融 | 加入可靠性引导、类别条件一致性及任务反馈 | 完整消融、与最新方法对比、效率分析 |

## 10. 风险与投稿策略

- **新颖性风险：** CCFA-Net 已研究 UAV 去雾与检测协同；PDDA、CIM-D 已覆盖跨域去雾。不可将“去雾 + 检测 + 特征对齐”本身写成首创。
- **任务定义风险：** DG 与 UDA 不可混用；不能在未见目标域上调参后仍宣称零样本泛化。
- **数据风险：** 真实雾样本和小目标标注可能有限，应报告置信区间、多次运行结果和跨场景稳定性。
- **工程风险：** GitHub 开源不等于完整可复现，须优先验收训练脚本、数据下载、权重和指标。
- **TVT 匹配风险：** 需围绕 UAV 自主感知或 UAV 辅助交通监测提出清晰的车辆技术问题，并给出实时性、鲁棒性等系统层面的证据。

## 11. 最终决策

**推荐路线：** UAV 辅助交通监测 + 严格未见域泛化 + 检测可靠性引导去雾。  
**核心实验起点：** HazyDet / DeCoDet + DehazeFormer（或 gUNet）。  
**直接竞争论文：** CCFA-Net。  
**TVT 对标：** *Cross-Modal Object Detection Via UAV* 与 *Haze Visibility Enhancement...*。

**最先回答的实验问题：** 不接触真实目标域训练数据时，普通去雾是否真的稳定改善 UAV 车辆检测？如果答案是否定或提升很有限，就有明确的研究切入点：解决去雾与检测之间的负迁移，并改善跨场景泛化。
