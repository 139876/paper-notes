---
tags: [MOC, 论文精读, CV, 多模态, 知识蒸馏, UAV检测]
aliases: [Cross-Modal UAV 索引, CKD 索引]
created: 2026-11-01
status: 进行中
---

# 📑 Cross-Modal Object Detection via UAV · 总索引

> [!info] 这是 Obsidian Vault
> 用 Obsidian 打开本文件夹：**Open folder as vault**
> 数学公式用行内式与独立居中式两种写法，由 Obsidian 内置 MathJax 渲染。
> 配套汇报 PPT 见 [[paper-notes/论文精读/2-Cross-Modal-UAV精读/附件/Cross-Modal-UAV-论文汇报.pptx]]。

---

## 📌 论文信息

| 项 | 内容 |
|---|---|
| 标题 | Cross-Modal Object Detection via UAV |
| 作者 | Ang Li, Shouxiang Ni, Yanan Chen, Jianxin Chen, Xin Wei, Liang Zhou, Mohsen Guizani |
| 单位 | 南京邮电大学 · 宽带无线通信与传感器网络技术教育部重点实验室 / MBZUAI |
| 期刊 | IEEE Transactions on Vehicular Technology, **Vol. 72, No. 8**, pp. 10894–10905, **Aug. 2023** |
| DOI | [10.1109/TVT.2023.3262129](https://doi.org/10.1109/TVT.2023.3262129) |
| 数据集 | DroneVehicle（28,439 对 IR-RGB） |
| 在阅读清单中的位置 | [[paper-notes/论文精读/00-总索引-四篇论文]] 第 2 篇 · **方法** 篇（[[paper-notes/论文精读/1-CCFA-Net精读/00-索引 MOC]] 是背景篇） |

**一句话总结**

> 无人机想在黑夜里看清车，但装不起红外相机（论文 Fig.1：IR 相机 = RGB 相机的 **10 倍**），也带不动多模态推理（Jetson TX2 只有 1.33 TFLOPS）。
> 本文让**红外检测器当老师、彩色检测器当学生**：训练时用 IR 教 RGB，**推理时把红外相机和所有融合模块全删掉**，只留一颗普通彩色摄像头。
> 结果：mAP 56.1 → **60.7**（+4.6），参数量与推理开销**减半**，逼近真正双模态的 63.2。

---

## 🗺️ 阅读路线

```
 阶段零 · 建立直觉（30 min）
   └─► [[paper-notes/论文精读/2-Cross-Modal-UAV精读/01-论文速览]]                训练用 IR、部署用 RGB 到底怎么做
   ├─► [[paper-notes/论文精读/2-Cross-Modal-UAV精读/公共基础知识/01-模型压缩全景]]  ★ 剪枝/量化/KD 三流派，本文属于哪一派
   └─► [[paper-notes/论文精读/2-Cross-Modal-UAV精读/公共基础知识/02-知识蒸馏详解]]      ★★ 软标签/温度T/KL + 本文 SFI·API 全部公式

 阶段一 · 补齐领域知识（本文最大空白）
   ├─► [[paper-notes/论文精读/2-Cross-Modal-UAV精读/02-第1讲-知识蒸馏与模态鸿沟]]     ★ 必读 · KD 基础 + 核心洞察
   ├─► [[paper-notes/论文精读/2-Cross-Modal-UAV精读/03-第2讲-基线与旋转框检测]]      ★ 必读 · Oriented R-CNN 三部件
   ├─► [[paper-notes/论文精读/2-Cross-Modal-UAV精读/04-第3讲-SFI选择性特征模仿]]     ★ 论文创新点①
   └─► [[paper-notes/论文精读/2-Cross-Modal-UAV精读/05-第4讲-API自适应预测模仿]]     ★ 论文创新点②

 阶段二 · 工程落地
   ├─► [[paper-notes/论文精读/2-Cross-Modal-UAV精读/06-第5讲-总目标训练流程与部署]]  ★ Algorithm 1 + 部署时删什么
   └─► [[paper-notes/论文精读/2-Cross-Modal-UAV精读/07-第6讲-实验设置与主结果解读]]  ★ 数字怎么读

 阶段三 · 研究者视角
   ├─► [[paper-notes/论文精读/2-Cross-Modal-UAV精读/08-第7讲-消融与定性结果精读]]    ★ 三个消融 + 定性对比
   └─► [[paper-notes/论文精读/2-Cross-Modal-UAV精读/09-第8讲-批判性评价与可做选题]]  ★ 找选题从这里开始

 附录
   ├─► [[paper-notes/论文精读/2-Cross-Modal-UAV精读/10-附录-公式速查手册]]
   └─► [[paper-notes/论文精读/2-Cross-Modal-UAV精读/11-附录-术语表与自测题库]]
```

---

## 📊 核心数字速查

| 数据集 / 项目 | 数值 | 说明 |
|---|---|---|
| 主结果 mAP | **60.7** | RGB-only，vs 同结构基线 56.1（**+4.6**） |
| vs 真正多模态 | −2.5 | 多模态 63.2，但需双模态 + 双倍参数 |
| vs 最强 RGB-only 基线 ReDet | +5.1 | 55.6 → 60.7，全面超过 11 个 RGB-only 基线 |
| 参数量 | 40M | 与单模态相同，是多模态的 **1/2** |
| 分类别增益 | Van **+6.6** / Freight Car **+6.0** / Car +3.5 / Bus +2.0 / Truck **+0.5** | 增益集中在 **RGB 看不见的类别** |
| 消融 基线 → +SFI → +API → 全模型 | 56.1 → 59.2 → 57.5 → **60.7** | SFI +3.1 > API +1.4，两者**不冲突** |
| π₁ 权重扫描 | 0→58.54 · **0.3→59.21** · 1→58.29 | 残差更有价值，但共性也不能丢 |
| w_ciou 消融 | 全用 57.5 vs 全不用 56.9 | 增益偏小（+0.6），论文未夸大 |
| IR vs RGB 标注数（训练集） | 316,411 vs 286,793 | 差 **29,618** 个 —— API 的实证依据 |
| 硬件 | 2× Xeon E5-2695 v4 + 8× Tesla P100 | ⚠️ **不是** Jetson TX2，见 [[paper-notes/论文精读/2-Cross-Modal-UAV精读/09-第8讲-批判性评价与可做选题]] |

---

## ⚡ 三句话抓住全文

1. **跨模态蒸馏不能无差别地拉近特征。** 必须先拆成"共性"和"残差"，只对残差加大权重——否则是重复劳动 + 梯度冲突。
2. **老师也会错。** 夜间 RGB 看不见红外能看见的目标（训练集差 3 万个标注），硬学老师 = 学坏；所以要用**跨模态 IoU 当信任度旋钮**。
3. **本文是"部署时的模态裁剪"，不是传统意义的"模型压缩"。** 师生完全同构，知识来源是**模态差异**而非模型容量。
   （完整坐标系见 [[paper-notes/论文精读/2-Cross-Modal-UAV精读/公共基础知识/01-模型压缩全景]]：剪枝 / 量化 / KD 三流派，本文 ≈ 结构化剪枝的极端特例 + 跨模态变体的 KD）

---

## 🖼️ 附件

| 文件 | 内容 |
|---|---|
| ![[cover_cameras.png]] | RGB 相机与红外相机的光谱对比（论文 Fig. 1） |
| ![[fig1_deployment_issues.png]] | 无人机部署的两大现实障碍 |
| ![[fig2_three_schemes.png]] | Fig. 2 三种方案对比：单模态 / 多模态 / **本文 CKD** |
| ![[fig3_framework.png]] | Fig. 3 整体框架：SFI + API + Oriented R-CNN |
| ![[fig4_qualitative.png]] | Fig. 4 定性对比（夜景 / 黄昏 / 雾天） |
| ![[fig5_module_ablation.png]] | Fig. 5 模块消融 |
| ![[fig6_pi_weight.png]] | Fig. 6 共性/残差权重 π₁ 扫描 |
| ![[fig7_wciou_ablation.png]] | Fig. 7 `w_ciou` 消融 |
| ![[night_rgb.png]] / ![[night_ir.png]] | 同一夜场的彩色 vs 红外 |
| ![[rotated_boxes.png]] | 水平框 vs 旋转框 |

**非图片附件**

| 文件 | 内容 |
|---|---|
| [[paper-notes/论文精读/2-Cross-Modal-UAV精读/附件/Cross-Modal-UAV-论文汇报.pptx]] | 19 页 CCF-A 风格汇报 PPT（每页带演讲者备注） |
| [[paper-notes/论文精读/2-Cross-Modal-UAV精读/附件/Cross-Modal-UAV-完整讲解.md]] | 完整讲解稿（46 KB，五段式） |
| [[paper-notes/论文精读/2-Cross-Modal-UAV精读/附件/Cross-Modal-UAV-速查笔记.md]] | 一页速查卡 |

---

## ✅ 学习进度

- [ ] [[paper-notes/论文精读/2-Cross-Modal-UAV精读/01-论文速览]]
- [ ] [[paper-notes/论文精读/2-Cross-Modal-UAV精读/公共基础知识/01-模型压缩全景]]（公共基础）
- [ ] [[paper-notes/论文精读/2-Cross-Modal-UAV精读/公共基础知识/02-知识蒸馏详解]]（公共基础）
- [ ] [[paper-notes/论文精读/2-Cross-Modal-UAV精读/02-第1讲-知识蒸馏与模态鸿沟]]
- [ ] [[paper-notes/论文精读/2-Cross-Modal-UAV精读/03-第2讲-基线与旋转框检测]]
- [ ] [[paper-notes/论文精读/2-Cross-Modal-UAV精读/04-第3讲-SFI选择性特征模仿]]
- [ ] [[paper-notes/论文精读/2-Cross-Modal-UAV精读/05-第4讲-API自适应预测模仿]]
- [ ] [[paper-notes/论文精读/2-Cross-Modal-UAV精读/06-第5讲-总目标训练流程与部署]]
- [ ] [[paper-notes/论文精读/2-Cross-Modal-UAV精读/07-第6讲-实验设置与主结果解读]]
- [ ] [[paper-notes/论文精读/2-Cross-Modal-UAV精读/08-第7讲-消融与定性结果精读]]
- [ ] [[paper-notes/论文精读/2-Cross-Modal-UAV精读/09-第8讲-批判性评价与可做选题]]
- [ ] [[paper-notes/论文精读/2-Cross-Modal-UAV精读/11-附录-术语表与自测题库]]（全部答完）
