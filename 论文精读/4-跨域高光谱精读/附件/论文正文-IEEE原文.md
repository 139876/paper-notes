---
track: 论文精读
tags: [原文, 附件, JVC-ASI, IEEE, TGRS]
aliases: [论文正文原文, IEEE原文全文]
created: 2026-11-17
updated: 2026-11-17
source: "IEEE Xplore · https://ieeexplore.ieee.org/document/11595676"
doi: "10.1109/TGRS.2026.3710332"
license: CC-BY
status: 已抓取
---

# 📄 论文正文原文（IEEE Xplore 抓取）

> [!success] 抓取说明（2026-11-17）
> - 论文：*Cross-Domain Hyperspectral Image Generalization Based on Joint Variable Consistency and Anchor Structure Invariance*
> - 作者：Mengying Xie, Jingwen Han, Yantao Li, Shaojiang Deng（重庆大学）
> - IEEE TGRS, Vol. 64, Art. 5520916, 2026 · DOI `10.1109/TGRS.2026.3710332` · **CC-BY 开放获取**
> - 抓取入口：`https://ieeexplore.ieee.org/rest/document/11595676`（返回正文 HTML，含全部公式 MathML）
> - PDF 端点 `stamp/stampPDF` 在本机网络下返回 502，**表格数据（Table I–VI、Fig. 3–10 的曲线）未能取到**，本附件只含**正文散文与全部 12 个公式**。

> [!important] 怎么用这份原文
> 1. 本附件是**唯一权威的措辞来源**——笔记里凡是标 ✅ 的结论，都可以在这里找到对应段落。
> 2. 公式已转成 LaTeX，可直接抄进 [[10-附录A-公式速查手册]]。
> 3. 表格/曲线缺失的部分，笔记里标为 🖼️ 待补，不要瞎填数字。

---

SECTION I.


## Introduction
Hyperspectral images (HSIs) often contain massive spatial–spectral information across hundreds of narrow and continuous bands [1], [2], [3]. In the fields of agricultural monitoring [4], [5], [6], military reconnaissance [7], [8], [9], and urban governance [10], [11], [12], [13], they have shown great potential. Intelligent interpretation of HSIs serves as a fundamental pathway to fully exploit their practical value. However, the acquisition of annotated HSIs remains prohibitively expensive, which requires a large amount of expert knowledge [14]. Meanwhile, HSIs are highly sensitive to variations in sensors, imaging conditions, and land-cover classes, resulting in significant distribution discrepancies across different scenes [13], [15], [16]. Such high annotation costs and distribution discrepancies make it difficult for conventional classification models to generalize effectively to new domains, since they built upon the independent and identically distributed assumption [see Fig. 1(a)]. Therefore, it is of great importance to investigate cross-domain HSI classification, which leverages labeled source domain data to enhance recognition performance in target domains [17]. > 📷 Fig. 1. - Illustration for the limitations of the existing work and the challenges. (a) Independent and identically distributed-based models struggle with domain generalization under distribution shifts. (b) Existing MDG methods exhibit degraded target accuracy due to insufficient cross-domain consistency and structure invariance. 
Fig. 1. Illustration for the limitations of the existing work and the challenges. (a) Independent and identically distributed-based models struggle with domain generalization under distribution shifts. (b) Existing MDG methods exhibit degraded target accuracy due to insufficient cross-domain consistency and structure invariance.

Under the assumption that HSIs in target domain are accessible, HSI domain adaptation (HSI DA) has been extensively studied. Due to the scarcity of labeled target data and the failure of empirical risk minimization, a critical issue of HSI DA lies in how to align the distributions between source domains and target domain, so that the classification model effectively adapts to target domain [18], [19]. According to alignment strategies, the existing HSI DA methods are divided into four categories, i.e., adversarial learning-based, contrastive learning-based, subspace learning-based, and confidence learning-based. Specifically, the adversarial learning-based methods [15], [20], [21] employ a minimax optimization between feature extractor and domain discriminator. Contrastive learning-based methods [22], [23] pull features from the same class closer while pushing those from different classes apart. The subspace learning-based methods [24], [25] project source and target data into a shared subspace. The confidence learning-based methods [26] use confidence prediction to select target data for pseudo-labeling or self-training. Overall, HSI DA achieves substantial progress in HSI classification.
In real-world remote sensing scenes, continuous satellite observations make it often impractical to acquire data from new domains in advance. Consequently, compared with HSI DA, it is more desirable to achieve robust recognition on unseen domains without accessing any target domain data, i.e., cross-domain HSI generalization (HSI DG) [27], [28]. To address out-of-distribution generalization, a critical issue of HSI DG lies in learning domain-invariant features, which aim to preserve stable feature-label relationships across domains while eliminating spurious feature-domain correlations. Early studies in HSI DG primarily focus on single-source domain generalization (HSI SDG). According to invariant feature strategies, the existing HSI SDG methods are divided into three categories, i.e., data augmentation-based, prior knowledge-based, and structure constraint-based. Specifically, the data augmentation-based methods [29], [30], [31], [32], [33], [34] leverage generative adversarial learning or randomization to estimate extended domains for simulating underlying target domain distributions. The prior knowledge-based methods [35], [36] incorporate external prior knowledge, e.g., text information, to construct shared semantic spaces across domains. This encourages classification models to learn more inherent invariant features. The structure constraint-based methods [37] emphasize preserving semantic consistency and enforcing geometric constraints during domain extension. These HSI SDG methods have further promoted the development of HSI classification. However, since SDG relies on training over a single data distribution, it often struggles to accommodate the complex variability of real-world imaging conditions, such as distinct sensors, illumination changes, and spectral shifts. To alleviate these limitations, multisource domain generalization (MDG) [38], [39] has emerged as an effective solution in cross-domain HSI classification. By leveraging multiple source domains, HSI MDG introduces more diverse distributional priors into the training process, enabling the model to better distinguish between domain-variant and domain-invariant features. This significantly enhances its generalization capability on unseen domains. Specifically, MDGTnet [40] pioneered this direction by employing a dual-branch feature disentanglement and fusion (DBFDF) backbone to extract domain-variant and domain-invariant features. Upon this backbone, JPDA-SCL [41] strengthened the supervised contrastive learning module to enhance feature discriminability and prevent class feature collapse. SRDGNet [42] adopted a lightweight architecture to mitigate overfitting under limited samples. SSEDGnet [43] generated expanded domain samples via physically interpretable imaging simulation. The superior experimental results of these methods provide strong evidence for the importance of investigating HSI MDG.
Despite the effectiveness of these HSI MDG methods, they still encounter difficulty in generalization stability of domain-invariant features. Particularly, when facing significant domain shifts and complex data distributions, this difficulty often results in a notable degradation for classification accuracy on target domains. Fig. 1(b) has visually shown this difficulty. Ideally, following statistical theory, the well-generalized domain-invariant features should simultaneously satisfy stable cross-domain consistency and structure-invariance constraints. Cross-domain consistency implies the ability to resist domain discrepancies caused by imaging variations. Structure invariance indicates the capability to preserve class-discriminative semantics from both intraclass compactness and interclass separability perspectives. Regrettably, in practice, the domain-invariant features learned by the existing methods still lack rigorous guarantees in terms of both cross-domain consistency and structure invariance.
Lack of stable cross-domain consistency constraints. Existing methods rely on marginal or class-conditional distributions to measure domain discrepancies and employ outer-product-based linear modeling to mine interdomain correlations. However, such measure strategies fail to completely capture the joint information between features and labels,1 making them prone to a pseudo-invariant classification issue. In this issue, feature distributions appear aligned across domains while their category decision boundaries remain markedly distinct. Moreover, these modeling ways are not well-suited to the high-dimensional signature of HSIs, as they overlook high-order correlations across domains. Consequently, these relaxed distribution measures and correlation modeling render the learned domain-invariant features still sensitive to domain shifts, amplifying generalization errors.
Lack of stable structure invariance constraints. Existing approaches utilize contrastive learning to enhance feature discriminability. However, only using such a feature strategy not only heavily depends on the sampling strategies of positive and negative pairs but also struggles to exploit local and global topological structures per class that arise from the continuous spectral properties and low-dimensional manifold structure of HSIs. Therefore, these relaxed feature learning ways tend to produce domain-invariant features with ambiguous interclass boundaries and dispersed intraclass similarity, ultimately leading to degraded cross-domain classification accuracy.
To address the above limitations, we propose a novel cross-domain HSI generalization model JVC-ASI. In JVC-ASI, we present joint-variable consistency (JVC) and anchor-structure invariance (ASI) modules and introduce them into the classical DBFDF backbone. Specifically, to achieve stable cross-domain consistency tailored to HSIs, we exploit the JVC module by investigating mutual information (MI)-based joint distribution alignment, where a joint variable mechanism over features and labels is leveraged to mitigate spurious invariance, and MI-based domain correlation modeling is employed to better capture high-order correlations across domains. In addition, to satisfy stable structure invariance tailored to HSIs, we exploit the ASI module by exploring local–nonlocal anchor manifold structure, where the integration of dynamic local anchor selection and nonlocal graph Laplacian is designed to preserve class-discriminative semantics and circumvent class confusion. The learning algorithm of JVC-ASI is based on a minibatch stochastic gradient descent optimizer with numerical convergence behavior.
The main contributions are summarized as follows.
For cross-domain HSI generalization, we propose a novel MDG model JVC-ASI. By stable HSI cross-domain consistency and structure invariance, JVC-ASI has ability to effectively and efficiently overcome the generalization stability challenge for domain-invariant features. It prevents the amplification of generalization errors and the degradation of cross-domain classification accuracy.
In terms of stable HSI cross-domain consistency, we construct a joint variable constraint module JVC grounded in statistical theory. With MI-based joint distribution alignment, this module reveals complete and high-order joint correlations on features and labels across multiple source domains. This improves the ability of domain-invariant features to mitigate diverse domain shifts.
In terms of stable HSI structure invariance, we construct a multiregion geometric constraint module ASI grounded in topological theory. With local–nonlocal anchor manifold representation, this module maintains intraclass compactness and interclass separability for each domain throughout the distribution alignment process. This enhances the ability of domain-invariant features to avoid semantic mismatch and class confusion.
On several cross-domain HSI generalization tasks, JVC-ASI achieves an average overall accuracy (OA) of 79.16% and kappa coefficient of 70.27%, respectively, yielding a mean relative improvement of 1.74% and 2.73% over the competitive generalization baselines. This clearly validates the importance of JVC-ASI in promoting cross-domain HSI generalization performance.
The remainder of this study is organized as follows. Section II concisely introduces some preliminaries, including notations and related work. Section III detailly elaborates the proposed model JVC-ASI, including the overview, JVC and ASI modules, and loss function. Section IV conducts extensive generalization experiments and analyzes the empirical results. Section V briefly concludes this study and introduces future research directions.
 SECTION II.


## Preliminaries


### A. NotationsFor the sake of clarity, we focus on a cross-domain HSI generalization scenario involving two source domains. Without loss of generality, this study can be naturally extended to generalization tasks with multiple source domains. Some important notations throughout this study are provided as follows.
Source Domain: Within original data, the labeled source domain datasets are denoted as $\mathbb {D}_{s_{1}}^{o}{\,}={\,}\{(\mathbf {x}_{i{s_{1}}}, y_{i{s_{1}}})\}_{i=1}^{n_{1}}$
 and $\mathbb {D}_{s_{2}}^{o}{\,}={\,}{\,}\{(\mathbf {x}_{i{s_{2}}}, y_{i{s_{2}}})\}_{i=1}^{n_{2}}$
. Within feature data, they are represented as $\mathbb {D}_{s_{1}}^{f} {\,}={\,}\{(\mathbf {f}_{i{s_{1}}}, y_{i{s_{1}}})\}_{i=1}^{n_{1}}$
 and $\mathbb {D}_{s_{2}}^{f}{\,}={\,}\{(\mathbf {f}_{i{s_{2}}}, y_{i{s_{2}}})\}_{i=1}^{n_{2}}$
. $\mathbf {x}_{i{s_{1}}}, \mathbf {x}_{i{s_{2}}}$
 are HSI patch samples. $\mathbf {f}_{i{s_{1}}}, \mathbf {f}_{i{s_{2}}}$
 and $y_{i{s_{1}}}, y_{i{s_{2}}}$
 are their corresponding features and labels. The numbers of samples in two source domains are $n_{1}$
 and $n_{2}$
, respectively.
Target Domain: Within original data, the unlabeled target domain dataset is denoted as $\mathbb {D}_{t}^{o} {\,}={\,}\{\mathbf {x}_{it}\}_{i=1}^{n_{3}}$
. Within feature data, it is represented as $\mathbb {D}_{t}^{f} {\,}={\,}\{\mathbf {f}_{it}\}_{i=1}^{n_{3}}$
. In general, the distributions of target data domain significantly differ from those of the source domains. $n_{3}$
 is the number of target samples.
Domain Label: The domain label is denoted as $l {\,}\in {\,}{L}$
. ${L}{\,}={\,}\{1, \ldots, n_{s}\}$
 is the domain label space. $n_{s}{\,}={\,}2$
 is the number of source domains. $l{\,}={\,}1$
 and $l{\,}={\,}2$
 correspond to the first and second source domains, respectively. Within feature data, the domain-conditional distributions are $p(\mathbf {f}, y \mid l{\,}={\,}1)$
 and $p(\mathbf {f}, y \mid l{\,}={\,}2)$
, respectively.


### B. MDG for HSIBy introducing diverse distributional priors into the training process, MDG can enable the classification model to better distinguish between domain-variant and domain-invariant features, especially for unseen scenes. Thus, it has become an indispensable solution in cross-domain HSI classification.
Most existing HSI MDG methods follow a unified DBFDF backbone, which is proposed by Qi et al. [40] for the first time. This backbone consists of two branches, which are the intradomain uniqueness extraction branch (Intra-DUEB) and the interdomain commonality extraction branch (Inter-DCEB). The Intra-DUEB uses an attribute extraction module (AEM) and four consecutive convolution blocks. AEM performs spectral segmentation and weight calculation for simultaneously obtaining fine-grained spectral feature representations and maintaining the original spectral consistency. Moreover, four consecutive convolution blocks, each consisting of two sets of $1{\,}\times {\,}1$
 convolutions with batch normalization, ReLU, channel attention, and residual connections, are used to extract multilevel domain features. In this way, this branch effectively captures the intrinsic attributes of each source domain, which reflect the domain-specific properties induced by the corresponding imaging environment. Different source domains are processed by separate Intra-DUEBs with shared network parameters. In parallel with the Intra-DUEB, the Inter-DCEB employs an integrated feature extraction head (IFEH) and an integrated feature extraction module (IFEM) with feature dimensions aligned to those of Intra-DUEB. IFEM progressively extracts common features across different source domains and integrates them with the corresponding outputs of Intra-DUEB through a subtraction-based fusion strategy. Moreover, $3{\,}\times {\,}3$
 convolutions, batch normalization, and SoftMax operations are applied at each level to enhance spectral feature representations for similarity learning. In this way, this branch effectively captures the interdomain common characteristics and facilitates the learning of discriminative class representations.
To constrain samples from the same class to be close to each other, while pushing samples from different classes apart, the loss ${\mathcal {L}}_{\text {COS}}$
 based on cosine similarity measure and contrastive learning is defined as\begin{equation*} {\mathcal {L}}_{\text {COS}}\left ({ \mathbf {f},y}\right)= -\sum _{d=1}^{D}\xi \left ({ \mathbf {f}_{s_{1}}^{d} \cdot \mathbf {f}_{s_{2}}^{d}}\right) \tag {1}\end{equation*}
 \begin{equation*} {\mathcal {L}}_{\text {COS}}\left ({ \mathbf {f},y}\right)= -\sum _{d=1}^{D}\xi \left ({ \mathbf {f}_{s_{1}}^{d} \cdot \mathbf {f}_{s_{2}}^{d}}\right) \tag {1}\end{equation*}
where $D{\,}={\,}4$
 is the network layers. $\mathbf {f}_{s_{1}}^{d}$
 and $\mathbf {f}_{s_{2}}^{d}$
 are the feature vectors at the $d$
th layer. $\xi $
 is an indicator operator. For positive pairs, i.e., $y_{s_{1}}{\,}={\,}y_{s_{2}}$
, $\xi {\,}={\,}1$
; otherwise, $\xi {\,}={\,}-1$
. $\mathbf {f}_{s_{1}}^{d}\cdot \mathbf {f}_{s_{2}}^{d}$
 approximates the cosine similarity.
To guide the network to progressively increase the similarity of same-class samples and the dissimilarity of different-class samples as network depth $d$
 increases, the loss ${\mathcal {L}}_{\text {SDP}}$
 based on similarity-value difference progressive strategy is defined as\begin{equation*} {\mathcal {L}}_{\text {SDP}}\left ({ \mathbf {f},y}\right)=\sum _{d=1}^{D-1}\left ({ s^{d}-s^{d+1}-\xi w^{d}}\right)^{2} \tag {2}\end{equation*}
 \begin{equation*} {\mathcal {L}}_{\text {SDP}}\left ({ \mathbf {f},y}\right)=\sum _{d=1}^{D-1}\left ({ s^{d}-s^{d+1}-\xi w^{d}}\right)^{2} \tag {2}\end{equation*}
where $s^{d}{\,}={\,}\mathbf {f}_{s_{1}}^{d}\cdot \mathbf {f}_{s_{2}}^{d}$
 denotes the cosine similarity at the $d$
th layer, and $w^{d}$
 is the target margin controlling the similarity difference between adjacent layers. Eventually, $\mathbf {f}_{s_{1}}{\,}={\,}\mathbf {f}_{s_{1}}^{D}$
.
To assess the classification accuracy, the loss ${\mathcal {L}}_{\text {BCE}}$
 based on binary cross-entropy is defined as\begin{equation*} {\mathcal {L}}_{\text {BCE}}\left ({ \mathbf {f},y}\right)=\frac {1}{C}\sum _{i=1}^{n}-w_{c}\left ({ y_{i}\log \hat {y}_{i}+\left ({ 1-y_{i}}\right)\log \left ({ 1-\hat {y}_{i}}\right)}\right) \tag {3}\end{equation*}
 \begin{equation*} {\mathcal {L}}_{\text {BCE}}\left ({ \mathbf {f},y}\right)=\frac {1}{C}\sum _{i=1}^{n}-w_{c}\left ({ y_{i}\log \hat {y}_{i}+\left ({ 1-y_{i}}\right)\log \left ({ 1-\hat {y}_{i}}\right)}\right) \tag {3}\end{equation*}
where $C$
 is the class number. $n{\,}={\,}n_{1}{\,}+{\,}n_{2}$
. $\mathbb {D}^{f}$
 is composed of samples $\{\mathbf {f}_{1{s_{1}}},\mathbf {f}_{2{s_{1}}},\ldots,\mathbf {f}_{{n_{1}}{s_{1}}},\mathbf {f}_{1{s_{2}}},\mathbf {f}_{2{s_{2}}},\ldots,\mathbf {f}_{{n_{2}}{s_{2}}}\}$
 and class labels $\{y_{1{s_{1}}},y_{2{s_{1}}},\ldots,y_{{n_{1}}{s_{1}}},y_{1{s_{2}}},y_{2{s_{2}}},\ldots,y_{{n_{2}}{s_{2}}}\}$
. $\hat {y}_{i}$
 and $y_{i}$
 are the predicted label and the ground-truth label of the $i$
th sample in $\mathbb {D}^{f}$
, respectively. When $y_{i}$
 belongs to the $c$
th class, $w_{c}$
 is the $c$
th class weight.
According to the above designs, the backbone DBFDF is characterized through the loss function formulated by the parameterized linear combination of ${\mathcal {L}}_{\text {COS}}$
, ${\mathcal {L}}_{\text {SDP}}$
, and ${\mathcal {L}}_{\text {BCE}}$
. More details about this backbone and its variants for learning discriminative domain-invariant features can be seen in [40], [42], and [43]. However, such discriminative ability improvement from this backbone may be not enough for exploiting stably generalized domain-invariant features. Due to the lack of complete exploitation on joint feature-label relationships, domain-invariant features learned under this backbone are prone to encountering residual domain-sensitive information, which weakens its robustness on unseen domains. Furthermore, Luo et al. [41] introduce a joint-product optimization loss of features and labels into the DBFDF backbone. It explicitly considers cross-domain discrepancy via joint-product distribution measure, enhancing its robustness to a certain extent. However, due to the failure of capturing high-order correlations across domains during alignment, as well as of preserving intraclass compactness and interclass separability, domain-invariant features learned by [41] are prone to semantic mismatch and class confusion. Fortunately, our proposed method JVC-ASI can circumvent the residual domain-sensitive information and spurious invariance trap by more stable constraints on cross-domain JVC. In addition, it can avoid the semantic mismatch and class confusion issue by more stable constraints on local–nonlocal anchor-structure invariance.
 SECTION III.


## Methodology


### A. OverviewFig. 2 exhibits the architecture of our proposed JVC-ASI for outputting stably generalizable domain-invariant features and showing superior cross-domain classification accuracy. > 📷 Fig. 2：JVC-ASI 架构图（SA module performs spectral alignment） 
Fig. 2. Architecture of JVC-ASI. SA module performs spectral alignment.

First, JVC-ASI employs the classical DBFDF backbone as the fundamental network architecture. The source-domain HSIs are simultaneously fed into both Intra-DUEB and Inter-DCEB branches to generate the preliminary domain-invariant features at the fourth layer, i.e., $\{\mathbf {f}_{is_{1}},y_{is_{1}},l_{s_{1}}\}_{i=1}^{n_{1}}$
 and $\{\mathbf {f}_{is_{2}},y_{is_{2}},l_{s_{2}}\}_{i=1}^{n_{2}}$
.
Next, different from all existing MDG methods, the preliminary domain-invariant features are fed into a shared multilayer perceptron (MLP) layer $g$
. This operation enables the preliminary features to undergo a nonlinear reorganization from local representations into a global semantic space, together with cross-channel information interaction. Thus, the intermediate domain-invariant features $\{g(\mathbf {f}_{is_{1}}),y_{is_{1}},l_{s_{1}}\}_{i=1}^{n_{1}}$
 and $\{g(\mathbf {f}_{is_{2}}),y_{is_{2}},l_{s_{2}}\}_{i=1}^{n_{2}}$
 are generated.
Then, the intermediate domain-invariant features are fed into both JVC and ASI modules for enabling stable cross-domain consistency and structure invariance, respectively. Specifically, JVC module models and minimizes the complex dependencies between the joint variable pair $(g(\mathbf {f}),y)$
 and the domain labels $l$
 in a high-order manner, expecting well-controlled joint distribution alignment of different source domains. This stable cross-domain consistency constraint helps to achieve stronger robustness against domain shift, spurious invariance. At the same time, ASI module introduces dynamic anchor graph learning to preserve the local–nonlocal expressive structures in each source domain, enhancing anti-outliers ability and preventing these structures from being disrupted during pursuing joint distribution alignment. This stable structure invariance facilitates obvious mitigation on semantic mismatch and class confusion. Thus, the refined domain-invariant features $\{\hat {g}(\mathbf {f}_{is_{1}}),y_{is_{1}},l_{s_{1}}\}_{i=1}^{n_{1}}$
 and $\{\hat {g}(\mathbf {f}_{is_{2}}),y_{is_{2}},l_{s_{2}}\}_{i=1}^{n_{2}}$
 are generated, which can be stably generalized on unseen target domains.
Finally, the refined domain-invariant features are utilized to train a binary cross-entropy classifier. Once the classifier is trained, it is directly used to predict the labels of target-domain samples without any fine-tuning.


### B. Joint-Variable Consistency ModuleThe JVC module is designed for stable cross-domain consistency tailored to HSIs, which stems from the completeness of measure and the flexibility of alignment across source-domain distributions. Ideally, stably generalized domain-invariant features should satisfy two criteria: 1) the mapping between features and labels, i.e., $g(\mathbf {f})\rightarrow y$
, is reliable, ensuring that each sample pair $(g(\mathbf {f}),y)$
 is correctly matched and 2) such a mapping remains consistent across multiple source domains, i.e., $(g(\mathbf {f}), y)$
 is independent of domain label $l$
.
The popular selection for distribution measure in HSI MDG is the marginal distributions $p(g(\mathbf {f}))$
 or class-conditional distributions $p(y\mid g(\mathbf {f}))$
. However, such measure struggles to consistently and completely exploit the underlying mapping information between features and labels. Fortunately, from a statistical perspective, joint variable $(g(\mathbf {f}),y)$
 provides a more comprehensive representation for modeling this mapping, improving the completeness of distribution measure. Meanwhile, mainstream HSI cross-domain distribution alignment utilizes chi-square divergence [44], Kullback–Leibler divergence [45], or domain adversarial scheme [17] to directly minimize domain discrepancies. However, their inherent mathematical formulations make it difficult to enforce the independence between the mapping embedded in $(g(\mathbf {f}),y)$
 and the domain labels $l$
 via a tractable manner. It is pleased that from an information-theoretic perspective, MI estimation, which exhibits strong capability for nonlinear dependency modeling, offers a feasible solution for this limitation, enhancing the flexibility of distribution alignment.
From the above analysis and the definitions of joint variable and MI, a JVC module for well-controlled joint distribution alignment is formulated as follows:\begin{equation*} \min _{g\left ({ \mathbf {f}}\right)}{\mathcal {D}}_{\mathrm {MI}}\left ({ g\left ({ \mathbf {f}}\right), y; l}\right) \tag {4}\end{equation*}
 \begin{equation*} \min _{g\left ({ \mathbf {f}}\right)}{\mathcal {D}}_{\mathrm {MI}}\left ({ g\left ({ \mathbf {f}}\right), y; l}\right) \tag {4}\end{equation*}
where\begin{align*} & {\mathcal {D}}_{\mathrm {MI}}\left ({ g\left ({ \mathbf {f}}\right),y;l}\right) \\ & \quad = \int p\left ({ g\left ({ \mathbf {f}}\right),y,l}\right)\log \left ({ \frac {p\left ({ g\left ({ \mathbf {f}}\right),y,l}\right)}{p\left ({ g\left ({ \mathbf {f}}\right),y}\right)p\left ({ l}\right)}}\right){\,}dg\left ({ \mathbf {f}}\right){\,}dy{\,}dl \tag {5}\end{align*}
 \begin{align*} & {\mathcal {D}}_{\mathrm {MI}}\left ({ g\left ({ \mathbf {f}}\right),y;l}\right) \\ & \quad = \int p\left ({ g\left ({ \mathbf {f}}\right),y,l}\right)\log \left ({ \frac {p\left ({ g\left ({ \mathbf {f}}\right),y,l}\right)}{p\left ({ g\left ({ \mathbf {f}}\right),y}\right)p\left ({ l}\right)}}\right){\,}dg\left ({ \mathbf {f}}\right){\,}dy{\,}dl \tag {5}\end{align*}
where $p(g(\mathbf {f}),y,l)$
, $p(g(\mathbf {f}),y)$
, and $p(l)$
 are the distributions of full variable, joint variable, and domain label, respectively. In general, a smaller MI value indicates weaker statistical dependence between variables. Thus, when ${\mathcal {D}}_{\mathrm {MI}}(g(\mathbf {f}),y;l){\,}\rightarrow {\,}0$
, the joint variable $(g(\mathbf {f}),y)$
 approaches independence from the domain label $l$
. This implies that the mapping $g(\mathbf {f}){\,}\rightarrow {\,}y$
 embedded in the sample pairs $(g(\mathbf {f}),y)$
 is likely to be invariant across diverse source domains, i.e., $p(g(\mathbf {f}),y\mid l{\,}={\,}1) {\,}\approx {\,}p(g(\mathbf {f}),y\mid l{\,}={\,}2)$
.
Rewrite $\mathbb {D}^{f}$
 consisting of samples $\{g(\mathbf {f}_{i})\}_{i=1}^{n}$
, class labels $\{y_{i}\}_{i=1}^{n}$
 and domain labels $\{1,1,\ldots,1,2,2,\ldots,2\}$
, where $\{g(\mathbf {f}_{i})\}_{i=1}^{n}=\{g(\mathbf {f}_{{1}{s_{1}}}),g(\mathbf {f}_{{2}{s_{1}}}),\ldots, g(\mathbf {f}_{{n_{1}}{s_{1}}}),g(\mathbf {f}_{1{s_{2}}}),g(\mathbf {f}_{2{s_{2}}}), \ldots,$
 $g(\mathbf {f}_{{n_{2}}{s_{2}}})\}$
. Following [46], the MI formulation (5) can be discretized by utilizing the variational representation [47], replacing the distribution mathematical expectations with sample averages, and introducing a linear-in-parameter function $q(g(\mathbf {f}),y,l;\beta){\,}={\,}\sum _{i=1}^{n}\beta _{i}k(g(\mathbf {f}),g(\mathbf {f}_{i}))\delta (y,y_{i})\delta (l,l_{i})$
. The function parameters are defined as $\beta {\,}={\,}(\beta _{1},\beta _{2},\ldots,\beta _{n})$
. Both $\delta (y,y_{i})$
 and $\delta (l,l_{i})$
 are based on the delta kernel function $\delta (\cdot)$
. For example, when $y{\,}={\,}y_{i}$
, $\delta (y,y_{i}){\,}={\,}1$
; otherwise, $\delta (y,y_{i}){\,}={\,}0$
. $k(g(\mathbf {f}),g(\mathbf {f}_{i}))$
 is a simple Gaussian kernel function of $g(\mathbf {f})$
 and $g(\mathbf {f}_{i})$
, and is equal to ${\mathrm {exp}}(({\,}-{\,}{\|g(\mathbf {f}){\,}-{\,}g(\mathbf {f}_{i})\|}_{2}^{2})/(2\sigma _{f}^{2}))$
 with a positive kernel width $\sigma _{f}$
. This nonlinearity enables $q(g(\mathbf {f}),y,l;\beta)$
 to well approximate the optimality condition $1+\log (p(g(\mathbf {f}),y,l)/(p(g(\mathbf {f}),y)p(l)))$
 of optimization problem (4) under the variational representation, turning the formulation (5) into a tractable convex form. Thus, the optimization problem (4) of JVC module can be reformulated as follows:\begin{align*} \min _{g\left ({ \mathbf {f}}\right),\beta }& \frac {1}{n} \sum _{i=1}^{n}q\left ({ g\left ({ \mathbf {f}_{i}}\right),y_{i},l_{i};\beta }\right) \\ & -\frac {1}{n^{2}} \sum _{i,j=1}^{n}\exp \left ({ q\left ({ g\left ({ \mathbf {f}_{i}}\right),y_{i},l_{j};\beta }\right)-1}\right). \tag {6}\end{align*}
 \begin{align*} \min _{g\left ({ \mathbf {f}}\right),\beta }& \frac {1}{n} \sum _{i=1}^{n}q\left ({ g\left ({ \mathbf {f}_{i}}\right),y_{i},l_{i};\beta }\right) \\ & -\frac {1}{n^{2}} \sum _{i,j=1}^{n}\exp \left ({ q\left ({ g\left ({ \mathbf {f}_{i}}\right),y_{i},l_{j};\beta }\right)-1}\right). \tag {6}\end{align*}
This objective function is convex on $\beta $
, which implies that when $g(\mathbf {f})$
 is given, the global optimal estimation of $\beta $
, i.e., $\hat {\beta }$
, can be well generated through a limited-memory Broyden–Fletcher–Glodfarb–Shanno (L-BFGS) algorithm [48]. Once $\hat {\beta }$
 is determined, the function $q(g(\mathbf {f}_{i}),y_{i},l_{i};\hat {\beta })$
 serves as a credible empirical estimate of the statistical dependence between the joint variable $(g(\mathbf {f}),y)$
 and the domain label $l$
. This provides a favorable and easily-computational gradient signal to guide the update of domain-invariant features $g(\mathbf {f})$
.
Based on the optimization problem (6), JVC module minimizes the training loss defined as follows:\begin{align*} {\mathcal {L}}_{\mathrm {JVC}}\left ({ \mathbf {f},y,l}\right)& =\frac {1}{n} \sum _{i=1}^{n}q\left ({ g\left ({ \mathbf {f}_{i}}\right),y_{i},l_{i};\hat {\beta }}\right) \\ & \quad -\frac {1}{n^{2}} \sum _{i,j=1}^{n} \exp \left ({ q\left ({ g\left ({ \mathbf {f}_{i}}\right),y_{i},l_{j};\hat {\beta }}\right)-1}\right). \tag {7}\end{align*}
 \begin{align*} {\mathcal {L}}_{\mathrm {JVC}}\left ({ \mathbf {f},y,l}\right)& =\frac {1}{n} \sum _{i=1}^{n}q\left ({ g\left ({ \mathbf {f}_{i}}\right),y_{i},l_{i};\hat {\beta }}\right) \\ & \quad -\frac {1}{n^{2}} \sum _{i,j=1}^{n} \exp \left ({ q\left ({ g\left ({ \mathbf {f}_{i}}\right),y_{i},l_{j};\hat {\beta }}\right)-1}\right). \tag {7}\end{align*}


#### Remark 1:From the training loss (7), by explicitly enforcing the mathematical independence between joint variable pair $(g(\mathbf {f}),y)$
 and domain label $l$
, JVC module satisfies the essential criteria, i.e., ensuring the credibility of feature-label mapping, and preserving its consistency across different source domains, for learning domain-invariant features with stable generalization. In addition, an empirical comparison between the JVC module and conventional joint-product distribution alignment module [44] is illustrated in Fig. 3. JVC module exhibits an obvious numerical advantage. Both theoretical and empirical soundness enable the learned domain-invariant HSI features to be more robust to domain shifts and avoid spurious invariance.
 > 📷 Fig. 3. - 
 Performance comparison (%) on PU + PC $\rightarrow $
 H18 task for JVC.
  
Fig. 3. 
 Performance comparison (%) on PU + PC $\rightarrow $
 H18 task for JVC.



### C. Anchor-Structure Invariance ModuleThe ASI module is designed for stable structure invariance tailored to HSIs. Benefiting from the high-dimensional signature of HSIs, the samples from the same land-cover classes often form compact clusters lying on complex nonlinear manifolds [14]. However, in HSI MDG, the domain distribution alignment essential for learning domain-invariant features, while reducing domain discrepancy by matching global statistics, may damage this nonlinear geometric structure. Once such topological structures are distorted during the alignment process, class boundaries may be warped, which in turn causes both semantic mismatch and class confusion, ultimately hindering the stability of domain-invariant features in discriminative capability and generalization performance.
Existing HSI MDG methods leverage contrastive learning to enhance the discriminability of domain-invariant features, while neglecting the constraints on both the similarity and discriminability among different land-cover materials across local and nonlocal regions. As a result, the learned domain-invariant features remain susceptible to distortion of the underlying nonlinear cluster manifold structures. Fortunately, dynamic anchor graph learning provides a promising solution to this difficulty. By enabling dynamic selection of cluster anchors, it allows nonlinear manifold representations to achieve greater anti-outlier performance while preserving intraclass compactness. This can alleviate semantic mismatch. Furthermore, by treating cluster anchors as graph nodes, graph Laplacian regularization encourages the learned representations to maintain smoothness. This ensures that topologically similar anchors remain closely connected, preventing well-structured signals from undergoing distortion or collapse during alignment optimization, and reducing the risk of class confusion.
From the above analysis and the definitions of cluster anchor and graph, an ASI module involves the following two steps.
Dynamical Cluster Anchor Selection: Budling upon [49], K-Means clustering [50] is used to determine cluster anchors. This procedure is dynamically implemented after each feature space update. Specifically, rewrite $\mathbb {D}_{s_{j}}^{f}{\,}={\,}\{g(\mathbf {f}_{{i}{s_{j}}}),y_{{i}{s_{j}}}\}_{i=1}^{n_{j}}$
, where $j{\,}={\,}1,2$
. In $\mathbb {D}_{s_{j}}^{f}$
, cluster centers $\{{\boldsymbol {\mu }}_{m{s_{j}}}\}_{m=1}^{M_{j}}$
 are obtained by minimizing\begin{equation*} \min _{\left \{{ {\boldsymbol {\mu }}_{m{s_{j}}}}\right \}_{m=1}^{M_{j}}} \sum _{m=1}^{M_{j}}\sum _{g\left ({ \mathbf {f}_{{i}{s_{j}}}}\right)\in \mathbb {C}_{m}} \left \|{ g\left ({ \mathbf {f}_{{i}{s_{j}}}}\right)-{\boldsymbol {\mu }}_{m{s_{j}}}}\right \|_{2}^{2} \tag {8}\end{equation*}
 \begin{equation*} \min _{\left \{{ {\boldsymbol {\mu }}_{m{s_{j}}}}\right \}_{m=1}^{M_{j}}} \sum _{m=1}^{M_{j}}\sum _{g\left ({ \mathbf {f}_{{i}{s_{j}}}}\right)\in \mathbb {C}_{m}} \left \|{ g\left ({ \mathbf {f}_{{i}{s_{j}}}}\right)-{\boldsymbol {\mu }}_{m{s_{j}}}}\right \|_{2}^{2} \tag {8}\end{equation*}
where $M_{j}$
 is the parameter of cluster number to control the degree of local homogeneity for intraclass similarity. $\mathbb {C}_{m}$
 is the set of samples belonging to the $m$
th cluster. In each $\mathbb {C}_{m}$
, the sample closest to the cluster center ${\boldsymbol {\mu }}_{m{s_{j}}}$
 is selected as the anchor\begin{equation*} \mathbf {a}_{m{s_{j}}}=\mathop {\arg \min }_{g\left ({ \mathbf {f}_{{i}{s_{j}}}}\right)\in \mathbb {C}_{m}}\left \|{ g\left ({ \mathbf {f}_{{i}{s_{j}}}}\right)-{\boldsymbol {\mu }}_{m{s_{j}}}}\right \|_{2}^{2}. \tag {9}\end{equation*}
 \begin{equation*} \mathbf {a}_{m{s_{j}}}=\mathop {\arg \min }_{g\left ({ \mathbf {f}_{{i}{s_{j}}}}\right)\in \mathbb {C}_{m}}\left \|{ g\left ({ \mathbf {f}_{{i}{s_{j}}}}\right)-{\boldsymbol {\mu }}_{m{s_{j}}}}\right \|_{2}^{2}. \tag {9}\end{equation*}
In this way, an anchor set for the $j$
th source domain $\mathbb {D}_{s_{j}}^{f}$
 is constructed as $\mathbb {A}_{s_{j}}{\,}={\,}\{\mathbf {a}_{m{s_{j}}}\mid m{\,}={\,}1,\ldots,M_{j}\}$
.
Compressive Anchor Graph Representation: Given the anchor set $\mathbb {A}_{s_{j}}$
, we adopt an $r$
-nearest neighbor graph for local and nonlocal topological structure mining per class, where $r$
 is the number of neighbors to control anchor graph sparsity. Each node in the graph corresponds to an anchor feature $\mathbf {a}_{u{s_{j}}}$
, enabling the propagation of correlations from local to nonlocal regions. According to graph theory and for $\mathbf {a}_{u{s_{j}}},\mathbf {a}_{z{s_{j}}}{\,}\in {\,}\mathbb {A}_{s_{j}}$
, if $\mathbf {a}_{u{s_{j}}}$
 belongs to the $r$
-nearest neighbors of $\mathbf {a}_{z{s_{j}}}$
, or $\mathbf {a}_{z{s_{j}}}$
 belongs to the $r$
-nearest neighbors of $\mathbf {a}_{u{s_{j}}}$
, an edge is established between $\mathbf {a}_{u{s_{j}}}$
 and $\mathbf {a}_{z{s_{j}}}$
. The weight of this edge is computed using the simple Gaussian kernel function\begin{equation*} {w}_{a_{u,z}}^{j} = \exp \left ({ -\frac {\left \|{ \mathbf {a}_{u{s_{j}}}-\mathbf {a}_{z{s_{j}}}}\right \|_{2}^{2}}{2\sigma _{w}^{2}}}\right). \tag {10}\end{equation*}
 \begin{equation*} {w}_{a_{u,z}}^{j} = \exp \left ({ -\frac {\left \|{ \mathbf {a}_{u{s_{j}}}-\mathbf {a}_{z{s_{j}}}}\right \|_{2}^{2}}{2\sigma _{w}^{2}}}\right). \tag {10}\end{equation*}
Inversely, if there is no edge between $\mathbf {a}_{u{s_{j}}}$
 and $\mathbf {a}_{z{s_{j}}}$
, ${w}_{a_{j,z}}^{j}{\,}={\,}0$
. The weight (10) controls the degree of global heterogeneity for interclass separability.
Based on the compressive anchor graph representation and introducing classical Laplacian regularization, ASI module minimizes the training loss defined as follows:\begin{equation*} {\mathcal {L}}_{\mathrm {ASI}}\left ({ \mathbf {f}}\right)=\frac {1}{2}\sum _{j=1}^{n_{s}} \sum _{u}\sum _{z}{w_{a_{u,z}}^{j}}\big \|\mathbf {a}_{u{s_{j}}}-\mathbf {a}_{z{s_{j}}}\big \|_{2}^{2}. \tag {11}\end{equation*}
 \begin{equation*} {\mathcal {L}}_{\mathrm {ASI}}\left ({ \mathbf {f}}\right)=\frac {1}{2}\sum _{j=1}^{n_{s}} \sum _{u}\sum _{z}{w_{a_{u,z}}^{j}}\big \|\mathbf {a}_{u{s_{j}}}-\mathbf {a}_{z{s_{j}}}\big \|_{2}^{2}. \tag {11}\end{equation*}


#### Remark 2:From the formulation (11), the designed weight matrix $\{{w_{a}}^{j}\}_{j=1}^{n_{s}}$
 has enabled the learned domain-invariant features $\{g(\mathbf {f}_{{i}{s_{j}}})\}_{j=1}^{n_{s}}$
 on an anchor manifold $\{\mathbf {a}_{m{s_{j}}}\}_{j=1}^{n_{s}}$
 to exhibit nondispersed intraclass similarity via cluster anchors, while maintaining clear interclass boundaries through the anchor graph across source domains. A visual comparison between the ASI module and conventional graph Laplacian regularization is presented in Fig. 4. Obviously, ASI provides better numerical performance. Meanwhile, the anchor-based approximation significantly reduces the computational complexity and enhances robustness to outliers, noise, and overfitting for stable feature structure learning. Thus, ASI module is particularly crucial for classification in unseen scenarios. In addition, the dynamic anchor graph scheme in the ASI module is novel. It is inspired by, yet fundamentally different from, the superpixel landmark graph proposed in related HSI clustering research [49]. The superpixel landmark graph computes local and nonlocal correlations only once on the original HSIs, whose performance is highly dependent on the quality and discriminability of the raw data. It is prone to highly unstable topological relationships and classification results. The proposed dynamic anchor graph effectively overcomes this limitation. It is constructed in the progressively optimized feature space and is recomputed after each round of feature update, better ensuring the integrity and invariance of source domain structures during the pursuit of rigorous joint distribution alignment. This advantage will be further validated through quantitative results in Section IV-C.
 > 📷 Fig. 4. - 
 Performance comparison (%) on PU + PC $\rightarrow $
 H18 task for ASI.
  
Fig. 4. 
 Performance comparison (%) on PU + PC $\rightarrow $
 H18 task for ASI.



### D. Loss FunctionAccording to the overview and incorporating the presented JVC and ASI modules into the DBFDF backbone, the overall loss function of our proposed JVC-ASI model can be formally written as follows:\begin{equation*} {\mathcal {L}}_{\text {JVC-ASI}} = \lambda _{1} {\mathcal {L}}_{\text {JVC}} + \lambda _{2} {\mathcal {L}}_{\text {ASI}} + \lambda _{3} {\mathcal {L}}_{\text {COS}} + \lambda _{4} {\mathcal {L}}_{\text {SDP}} + \lambda _{5} {\mathcal {L}}_{\text {BCE}} \tag {12}\end{equation*}
 \begin{equation*} {\mathcal {L}}_{\text {JVC-ASI}} = \lambda _{1} {\mathcal {L}}_{\text {JVC}} + \lambda _{2} {\mathcal {L}}_{\text {ASI}} + \lambda _{3} {\mathcal {L}}_{\text {COS}} + \lambda _{4} {\mathcal {L}}_{\text {SDP}} + \lambda _{5} {\mathcal {L}}_{\text {BCE}} \tag {12}\end{equation*}
where parameters $\{\lambda _{i}\}_{i=1}^{5}$
 balance the contributions of the cross-domain JVC loss ${\mathcal {L}}_{\text {JVC}}$
, the domain anchor structure invariance (ASI) loss ${\mathcal {L}}_{\text {ASI}}$
, the pair feature similarity measure loss ${\mathcal {L}}_{\text {COS}}$
, the progressive feature similarity control loss ${\mathcal {L}}_{\text {SDP}}$
, and the binary cross-entropy classification loss ${\mathcal {L}}_{\text {BCE}}$
 to the model generalization and stability, respectively. It is worth noting that ${\mathcal {L}}_{\text {COS}}$
, ${\mathcal {L}}_{\text {SDP}}$
 and ${\mathcal {L}}_{\text {BCE}}$
 are derived from the classical DBFDF backbone, as detailed in Section II-B. They facilitate the generation of the preliminary domain-invariant features at the fourth layer in the backbone architecture. In line with the loss definition in formulation (1), ${\mathcal {L}}_{\text {COS}}$
 yields larger feature similarities for positive pairs and smaller feature similarities for negative pairs. On the basis of ${\mathcal {L}}_{\text {COS}}$
, according to formulation (2), ${\mathcal {L}}_{\text {SDP}}$
 enforces a progressive similarity change constraint across feature layers, where the positive pair similarity increases and the negative pair similarity decreases as the network deepens. Both ${\mathcal {L}}_{\text {COS}}$
 and ${\mathcal {L}}_{\text {SDP}}$
 engage all four feature layers, rather than only the fourth layer, in discriminative learning, making the preliminary domain-invariant features less prone to collapse under distribution shifts on unseen target domains. After feeding the preliminary domain-invariant features into the shared MLP layer to generate the intermediate domain-invariant features and in agreement with the design in formulation (7), ${\mathcal {L}}_{\text {JVC}}$
 pursues more complete distribution measure between intermediate features and labels and more flexible distribution alignment across source domain distributions. During pursuing domain distribution alignment, following the loss definition in formulation (11), ${\mathcal {L}}_{\text {ASI}}$
 maintains the integrity and invariance of the local–nonlocal expressive structures in each source domain. Both ${\mathcal {L}}_{\text {JVC}}$
 and ${\mathcal {L}}_{\text {ASI}}$
 further consolidate rigorous cross-domain consistency and domain structure invariance, allowing the finally learned domain-invariant feature to better cope with the complex domain shifts, spurious invariance, semantic mismatch, and ambiguous decision boundaries. After using the classifier to obtain the predicted labels and consistent with the definitions in formulation (3), ${\mathcal {L}}_{\text {BCE}}$
 controls whether each sample belongs to one of the training classes and the overall misclassification probability.


### Algorithm 1 JVC-ASIInput: Labeled $\mathbb {D}_{s_{1}}^{o}$
 and $\mathbb {D}_{s_{2}}^{o}$
, unlabeled $\mathbb {D}_{t}^{o}$
.
Hyperparameters: $\{\lambda _{i}\}_{i=1}^{5}$
, batch_size, learning_rate.
Output: Trained MDG network.
1:while training does not end do
2:for batch_iter = 1: batch_num do
3:Sample two minibatches from $\mathbb {D}_{s_{1}}^{o}$
, $\mathbb {D}_{s_{2}}^{o}$
, respectively.
4:Compute loss function (12) using these minibatches.
5:Update network parameters by using a gradient step.
6:end for
7:end while
 SECTION IV.


## Experiment


### A. Experimental Setup


#### 1) Dataset and Preprocessing:Following [40], four public HSI datasets, Houston 2013 (H13) [51], Houston 2018 (H18) [52], Pavia University (PU) [53], and Pavia Center (PC) [54], are used as experimental data. The PU with a size of $610{\,}\times {\,}340{\,}\times {\,}103$
 and the PC with a size of $1096{\,}\times {\,}715{\,}\times {\,}102$
 are collected from Pavia using the ROSIS sensor whose spatial resolution is 1.3 m. The H13 with a size of $349{\,}\times {\,}1905{\,}\times {\,}144$
 and the H18 with a size of $601{\,}\times {\,}2384{\,}\times {\,}48$
 are collected from the University of Houston campus and surrounding areas using the ITRES CASI-1500 sensor whose spatial resolution is approximately 2.5 m. These four datasets offer diversity in spectral dimensions, spatial resolution, and scene complexity, providing a solid foundation for evaluating the model’s cross-domain classification capabilities.
Preprocessing on sample partition and band alignment is implemented as follows. The experiments are divided into two groups. In the first group, H13 and H18 serve as the source domains, while PU and PC are used as the target domain. To match the number of bands, we duplicate H18’s 48 bands to 144 bands to align with H13. According to the spectral range and resolution, the band numbers of PU and PC are aligned with H13 by filling missing bands with zeros. In the second group, PU and PC serve as source domains and H13 and H18 as the target domain. A similar approach is employed, aligning the bands of PU, H13, and H18 with PC and removing any redundant bands. In view of class imbalance, the model is trained on a balanced subset of the data, while the full dataset is reserved for target evaluation. The class distribution for each dataset in both experimental groups is shown in Table I.TABLE I Dataset Class Distribution and Sample Counts
 > 📷 Table I- Dataset Class Distribution and Sample Counts 


#### 2) Comparison Algorithms:For cross-domain HSI classification, we consider six competitive baselines from three closely related categories to evaluate the superiority of our proposed method JVC-ASI. Specifically, we evaluate the following baselines: 1) HSI DA: Supervised contrastive learning-based unsupervised network SCLUDA [23]. 2) HSI SDG: Single-source domain expansion network SDEnet [29], language-aware domain generalization network LDGnet [35], locally linear unbiased randomization network LLURnet [30], and frequency disentanglement and data geometry-guided DG network FDGnet [37]. 3) HSI MDG: Feature disentanglement and fusion-based dual-branch network MDGTnet [40]. For each method, we perform ten experiments with different random seeds and compute the mean and standard deviation of the results. All methods are trained and tested on the same datasets. The source codes of baseline methods come from their official publications.


#### 3) Experimental Environment:All experiments are conducted on a server running Ubuntu 22.04.5 LTS. The system is equipped with an Intel Core i9-10900X processor, 125 GB of RAM, and two NVIDIA GeForce RTX 3090 GPUs. Each GPU has 24-GB VRAM. For training and evaluation, we utilize only one of these GPUs. The software stack includes Python 3.10.18 and PyTorch 1.12.1 with CUDA enabled.


#### 4) Hyperparameter Setup:The hyperparameters of our proposed method JVC-ASI are determined via grid search. Specifically, the initial learning rate is searched within $\{0.002, 0.006, 0.01, 0.02, 0.04, 0.06, 0.08, 0.1\}$
, and the optimal values for the two experimental groups are set to 0.006 and 0.06, respectively. The loss weights $\lambda _{1}$
 and $\lambda _{2}$
 are tuned by exploring the candidate sets $\{0.1, 0.5, 1.0, 2.0\}$
 and $\{0.01, 0.05, 0.1, 0.2\}$
, respectively. $\lambda _{1} {\,}={\,}1$
 and $\lambda _{2}{\,}={\,}0.05$
 are eventually selected, as they are prone to yielding the impressing generalization performance. Following the DBFDF backbone [40], the values of $\lambda _{3}$
, $\lambda _{4}$
, and $\lambda _{5}$
 are set to 3, 10, and 2, respectively, with only minor fine-tuning applied. The batch size is set to 1024, the batch number is 160, and the input HSI patch size is $3{\,}\times {\,}3$
. Referring to the landmark graph research [49], $r$
 is empirically set to 10 for balancing local integrity and graph connectivity. In terms of the cluster number $\{M_{j}\}_{j=1}^{n_{s}}$
, we introduce a heuristic rule $M_{j} {\,}={\,}\min (\max (2, \lceil n_{j}/50\rceil),20)$
. This rule implicitly produces an average cluster size of approximately 50 samples, where this value is inspired by the experimental results in [49]. To a certain extent, this value helps to strike a balance between within-cluster density and the reasonableness of the cluster count. The bounds $M_{j}{\,}\in {\,}\{2,20\}$
 guarantee basic semantic interpretability of the clustering results. Too few clusters, such as $M_{j}{\,}={\,}1$
, defeat the purpose of clustering, while too many clusters may lead to overly fragmented results that are difficult to summarize. Thus, the rule is sample-size adaptive, automatically adjusting the number of clusters across datasets of different scales, thereby avoiding the applicability issues of a fixed cluster count. For all comparison baselines, we adopt the hyperparameter configurations reported in their publications to ensure a consistent evaluation. In cases where specific hyperparameters are not applicable or need to be adapted to our experimental data, we perform additional tuning following the grid search strategy described above.


#### 5) Metric:Following [23] and [40], we utilize the classification accuracy for each target class and two aggregate evaluation metrics OA and kappa coefficient to comprehensively assess the generalized classification performance of our proposed method JVC-ASI and all comparison baselines. OA represents the ratio of correctly classified samples to the total number of samples in the target domain test, providing a direct measure of the model’s overall classification precision. Its value ranges from $[{0, 1}]$
, and higher OA values indicate better overall performance. Kappa coefficient evaluates the consistency between the classification results and the true labels. In general, it exhibits lower sensitivity to class imbalance than OA measure because it can account for chance agreement. In classification tasks, its value typically falls within the range $[{0, 1}]$
. Higher kappa values indicate stronger consistency between the model’s results and the ground truth (GT), implying higher reliability in the classification.


### B. Results and Analysis


#### 1) Quantitative Comparison:Table II lists the results for all methods across both experimental groups, where “1,” “2,” “3,” and “4” correspond to the classification accuracy for the four target classes, while “OA” and “kappa” reflect the model’s classification performance at the global level. All values are presented as percentages, with the best results highlighted in bold and the second-best results being underlined. From Table II, we have the following observations.TABLE II Classification Comparison of Different Methods on Several Target Domains (%)
 > 📷 Table II- Classification Comparison of Different Methods on Several Target Domains (%) 


##### a) Overall performance improvement:For all datasets, JVC-ASI always achieves the highest OA and kappa scores, indicating the best overall classification performance. Meanwhile, the standard deviations of JVC-ASI tend to be small, potentially indicating greater robustness and stability. For example, in the “PU + PC $\rightarrow $
 H18” task, JVC-ASI shows a clear advantage by reaching an OA of 76.82%, which is 2.31% higher than the second-best method MDGTnet. Besides, JVC-ASI exhibits lower performance variability, with a standard deviation of 1.42 compared to that of 2.31 in MDGTnet. The kappa coefficient follows the same trend, demonstrating both higher accuracy and generalization performance of JVC-ASI. This is benefiting from that in JVC-ASI: 1) JVC module imposes more stable cross-domain consistency constraint to handle domain variation, enhancing the accuracy of feature-label mapping and its domain-invariant capability and 2) ASI module strengthens compact intraclass structures and clear interclass boundaries on discriminative manifold from both local and nonlocal regions, further improving the structure invariance of domain-invariant feature representations. Both lead to more reliable classification generalization on unseen target domains. In addition, both MDGTnet and JVC-ASI significantly outperform the other baseline methods on OA and kappa, further confirming the importance of leveraging multisource domain information to enhance model generalization. For example, in the “H13 + H18 $\rightarrow $
 PC” task, JVC-ASI and MDGTnet achieve the OA values of 88.73% and 87.49%, respectively, whereas the best performance among the remaining methods is only 70.27%, and the worst drops to 39.83%, highlighting a significant performance gap.


##### b) Classwise balance improvement:Most baselines exhibit pronounced classwise accuracy imbalance, achieving very high accuracy on certain classes while performing poorly on others. In the “PU + PC $\rightarrow $
 H13” task, for instance, SCLUDA attains 99.94% accuracy on Class 2 but only 6.84% on Class 4. Similarly, SDEnet reaches 100.00% on Class 2 but drops to 1.23% on Class 4. In contrast, JVC-ASI delivers more balanced recognition performance across classes, with accuracies ranging from 71.04% to 98.31%, without extreme fluctuations. This means better classification stability and consistency.
From the above analysis on multiple evaluation metrics and diverse transfer tasks, the proposed method JVC-ASI not only achieves superior overall performance but also demonstrates clear advantages in class balance and model robustness. These results indicate that our approach provides a stable, reliable, and well-generalized solution for MDG in HSI classification.


#### 2) Qualitative Comparison:Figs. 5–​8 present the visual comparison of our proposed method JVC-ASI and the competitive baselines. In these maps, red, purple, blue, and green denote the healthy grass, bare soil, tree, and road, respectively. Using the GT as a reference, it can be clearly observed that JVC-ASI produces more accurate and consistent classification results than the other methods across all datasets. > 📷 Fig. 5. - Visualization comparison of different methods on the PU dataset. (a) GT. (b) SCLUDA. (c) SDEnet. (d) LDGnet. (e) LLURnet. (f) FDGnet. (g) MDGTnet. (h) JVC-ASI. 
Fig. 5. Visualization comparison of different methods on the PU dataset. (a) GT. (b) SCLUDA. (c) SDEnet. (d) LDGnet. (e) LLURnet. (f) FDGnet. (g) MDGTnet. (h) JVC-ASI.

 > 📷 Fig. 6. - Visualization comparison of different methods on the PC dataset. (a) GT. (b) SCLUDA. (c) SDEnet. (d) LDGnet. (e) LLURnet. (f) FDGnet. (g) MDGTnet. (h) JVC-ASI. 
Fig. 6. Visualization comparison of different methods on the PC dataset. (a) GT. (b) SCLUDA. (c) SDEnet. (d) LDGnet. (e) LLURnet. (f) FDGnet. (g) MDGTnet. (h) JVC-ASI.

 > 📷 Fig. 7. - Visualization comparison of different methods on the H13 dataset. (a) GT. (b) SCLUDA. (c) SDEnet. (d) LDGnet. (e) LLURnet. (f) FDGnet. (g) MDGTnet. (h) JVC-ASI. 
Fig. 7. Visualization comparison of different methods on the H13 dataset. (a) GT. (b) SCLUDA. (c) SDEnet. (d) LDGnet. (e) LLURnet. (f) FDGnet. (g) MDGTnet. (h) JVC-ASI.

 > 📷 Fig. 8. - Visualization comparison of different methods on the H18 dataset. (a) GT. (b) SCLUDA. (c) SDEnet. (d) LDGnet. (e) LLURnet. (f) FDGnet. (g) MDGTnet. (h) JVC-ASI. 
Fig. 8. Visualization comparison of different methods on the H18 dataset. (a) GT. (b) SCLUDA. (c) SDEnet. (d) LDGnet. (e) LLURnet. (f) FDGnet. (g) MDGTnet. (h) JVC-ASI.

Taking the PU dataset as an example (see Fig. 5), several intuitive observations can be drawn.Some baseline methods exhibit pronounced misclassification among land-cover classes. LDGnet shows evident information loss in the bare soil (purple) and tree (blue) regions. LLURnet misclassifies most healthy grass (red) areas as bare soil (purple). FDGnet mainly confuses tree (blue) with healthy grass (red).
For categories with higher classification difficulty, such as the elongated healthy grass (red) region in the central part of the image, most competitive methods almost completely fail to recognize this area. Although JVC-ASI does not completely identify this part, it is the only method that correctly captures this region, demonstrating relatively stronger recognition ability in challenging scenes where other methods cannot work.
Compared with MDGTnet, which also belongs to the HSI MDG category, JVC-ASI shows clearer advantages in addressing similar misclassification cases. For example, in the “H”-shaped healthy grass (red) region at the top of the image, MDGTnet produces fragmented and discontinuous predictions, where red regions are broken into scattered patches. In contrast, JVC-ASI yields clearer class boundaries that better match the actual land-cover distribution, with improved intraclass integrity and reduced misclassification and mixing.
More obviously, as exhibited in Fig. 8, the DA method SCLUDA and the four SDG methods all suffer from severe misclassification in the road (green) category, whereas MDG methods exhibit relatively stronger robustness. This further confirms the effectiveness of multisource domain training.
Overall, MDG methods perform better than DA and SDG approaches. When comparing the two MDG methods, i.e., our proposed method JVC-ASI and the optimal baseline MDGTnet, JVC-ASI achieves higher classification accuracy without severe misclassification. This is attributed to our rigorously designed JVC and anchor graph structure invariance constraints, which effectively overcome diverse domain shifts and spurious invariance traps while mitigating semantic mismatch and class confusion. To this end, JVC-ASI can yield stable and reliable cross-domain generalization, particularly in handling hard-to-classify samples and complex decision boundaries. These observations further demonstrate the practical value of JVC-ASI for HSI classification transfer, which is consistent with the quantitative results.


#### 3) Statistical Test:For a rigorous statistical evaluation, we perform significance tests to explore whether the proposed method JVC-ASI consistently outperforms the baseline algorithms. Friedman test is employed to examine the null hypothesis that all cross-domain HSI classification methods exhibit equivalent performance. The intermediate and Friedman statistics, i.e., $\chi _{F}^{2}$
 and $F_{F}$
, are computed by\begin{align*} \chi _{F}^{2}& =\frac {12N}{k\left ({ k+1}\right)}\left [{ \sum _{i=1}^{k}R_{i}^{2}-\frac {{k\left ({ k+1}\right)}^{2}}{4}}\right] \tag {13}\\ F_{F}& =\frac {\left ({ N-1}\right)\chi _{F}^{2}}{N\left ({ k-1}\right)-\chi _{F}^{2}} \tag {14}\end{align*}
 \begin{align*} \chi _{F}^{2}& =\frac {12N}{k\left ({ k+1}\right)}\left [{ \sum _{i=1}^{k}R_{i}^{2}-\frac {{k\left ({ k+1}\right)}^{2}}{4}}\right] \tag {13}\\ F_{F}& =\frac {\left ({ N-1}\right)\chi _{F}^{2}}{N\left ({ k-1}\right)-\chi _{F}^{2}} \tag {14}\end{align*}
where $N$
 is the number of classification tasks and equal to $24.~k$
 is the number of classification methods and equal to 7. The average ranks of all algorithms are reported in Table III, and $R_{7} {\,}{\,}={\,}{\,}1.92$
. Through (13) and (14), $\chi _{F}^{2} {\,}{\,}={\,}{\,}22.50$
 and $F_{F} {\,}={\,}4.26.~F_{F}$
 should follow the $F$
 distribution with $k{\,}-{\,}1$
 and $(k{\,}-{\,}1)(N{\,}-{\,}1)$
 degrees of freedom, and it exceeds the critical value $F(6,6{\,}\times {\,}23) {\,}={\,}2.16$
 at $\alpha {\,}{\,}={\,}{\,}0.05$
. This indicates that the null hypothesis is rejected, confirming differences among these cross-domain HSI classification methods.TABLE III Friedman Test With Holm’s Step-Down Procedure for JVC-ASI
 > 📷 Table III- Friedman Test With Holm’s Step-Down Procedure for JVC-ASI 
JVC-ASI is utilized as the control. Holm’s step-down procedure is used as a post-hoc test to investigate the null hypothesis that each baseline algorithm does not differ significantly from the control. Hypotheses in Table III are ranked by average rank $R_{i}$
. For each baseline, the statistic $z_{i}{\,}={\,}(R_{i}{\,}-{\,}R_{7})/(k{\,}(k{\,}+{\,}1)/6N)^{1/2}$
 compares it with the control. $p_{z}$
 is obtained from the normal distribution table with $p{\,}={\,}2(1{\,}-{\,}p_{z})$
. In Table III, except MDGTnet, every $p$
-value is below its $\alpha /(k-i)$
. Therefore, the null hypotheses about the baselines SCLUDA, SDEnet, LDGnet, LLURnet, and FDGnet are rejected.
To facilitate a better comparison between our proposed method JVC-ASI and the optimal baseline MDGTnet, we perform a $t$
-test under the null hypothesis of no difference in their mean performance. The statistic $p_{t}$
 is 0.003 and less than significance level 0.05. Thus, the null hypothesis is rejected. The mean accuracy of JVC-ASI is 82.22% and that of MDGTnet is 80.37%. Based on the above analysis, JVC-ASI is statistically superior to the baseline algorithms in cross-domain HSI classification tasks.


### C. Empirical Analysis


#### 1) Ablation Study:To assess the necessity of our presented modules JVC and ASI, we construct some ablation baselines. In “no JVC,” we abandon the JVC module from JVC-ASI. Similarly, in “no ASI,” we remove the ASI module from JVC-ASI. In “no JVC&ASI,” we drop both the JVC and ASI modules from JVC-ASI. This helps to demonstrate the individual and joint contributions of JVC and ASI to the overall performance. From the results reported in Table IV, we can notice that: 1) the complete model JVC-ASI that incorporates both the JVC and ASI modules achieves the best performance, with an average OA of 79.16% and a kappa coefficient of 70.27%; 2) in contrast, abandoning the JVC module leads to decreases of 1.25% in OA and 1.58% in kappa; 3) when the ASI module is excluded, the performance drops are more pronounced, with OA and kappa reduced by 1.61% and 2.19%, respectively. Notably, in the “PU + PC $\rightarrow $
 H13” task, removing the ASI module results in an obvious degradation, where the OA decreases by 3.56% and the standard deviation increases by 2.29%; and 4) removing both the JVC and ASI modules leads to a clear drop in model performance, causing an average decrease of 1.36% in OA and 1.86% in kappa. Interestingly, on the H13 dataset, using either JVC module or ASI module alone may lead to a slight drop in classification accuracy compared to removing both JVC and ASI modules. This may be attributed to the fact that, on the H13 dataset, domain shifts are relatively small and interclass spectral differences are more subtle. In this situation, only exploiting the rigorous cross-domain consistency constraint derived from the JVC module may erase the domain decision boundaries, causing the degradation of discriminability. Only utilizing the rigorous domain structure invariance constraint derived from the ASI module may amplify domain discrepancies, leading to the degradation of generalization. Fortunately, when JVC and ASI modules work together, they counterbalance each other and form mutual encouragement. Therefore, even addressing small domain shifts and subtle interclass spectral differences, the collaboration of JVC and ASI modules is still more likely to achieve a better tradeoff between discriminability and generalization, retaining impressing classification accuracy. (e) Removing JVC module, ASI module, or both degrades the classwise accuracy balance performance. These results clearly demonstrate the individual effectiveness of two modules as well as their complementary and synergistic contributions to the overall performance.TABLE IV Ablation Results of Our Presented JVC and ASI Modules (%)
 > 📷 Table IV- Ablation Results of Our Presented JVC and ASI Modules (%) 


#### 2) Superiority Analysis:In this part, we construct two sets of experiments to evaluate the advantages of the JVC module and the ASI module over their respective relevant strategies.


##### a) Superiority of JVC module:We evaluate the superiority of JVC module for stable cross-domain consistency. In “EMMD” and “RCS,” we, respectively, employ the popular extended maximum mean discrepancy [55] and relative chi-square [44] strategies to control source-domain distribution alignment. From Table V, JVC module consistently outperforms the EMMD and RCS, achieving the best overall performance with an average OA of 80.82% and an average kappa of 72.37%. Interestingly, in the “PU+PC$\rightarrow $
H13” task, although the JVC module does not achieve the highest accuracy for each individual land-cover class, it still attains an OA of 84.81% (±1.44%) and a kappa of 79.74% (±1.91%), both of which are clearly superior to those of the competitive alignment strategies. Meanwhile, this result highlights the advantage of JVC module in terms of classwise balance and result stability.TABLE V Quantitative Analysis of Different Domain Alignment Strategies (%)
 > 📷 Table V- Quantitative Analysis of Different Domain Alignment Strategies (%) 
These quantitative findings are also supported by the trend of alignment errors during training. Considering the inconsistency in error scales, we normalize them to the range [0,1]. Fig. 9 shows the normalized alignment error curves of the aforementioned alignment strategies. Compared with EMMD, both JVC and RCS can exhibit faster convergence. Moreover, JVC achieves the lowest steady-state error, which is markedly smaller than those of RCS and EMMD, demonstrating its superior domain alignment efficiency and training stability. > 📷 Fig. 9. - Comparison of domain alignment error curves. 
Fig. 9. Comparison of domain alignment error curves.



##### b) Superiority of ASI module:We explore the superiority of ASI module for stable structure invariance. In “GLR,” we replace ASI module with conventional graph Laplacian regularization. The results shown in Table VI clearly demonstrate that compared to GLR strategy, ASI module yields a significant performance improvement. Specifically, in the “PU + PC $\rightarrow $
 H13” task, the classification accuracy of each category is enhanced to varying degrees, with the performance of the more challenging category (class 1) improving by 1.68%, and the simpler category (class 4) improving by 0.21%. Furthermore, the OA improves from 82.59% (±4.00%) to 84.81% (±1.44%). In the “PU + PC $\rightarrow $
 H18” task, the ASI module results in even more substantial improvements, with OA increasing by 7.99% and the kappa rising by 9.49%. Notably, the classification accuracy of the fourth category experiences a significant jump of over 11%. These results mean that dynamic cluster anchor selection and compressive anchor graph representation effectively and robustly preserves compact intraclass and separate interclass structures of source domain, preventing the strict alignment process from compromising the expressiveness of features, especially for challenging categories that are more susceptible to domain shift and feature collapse.TABLE VI Superiority Validation of ASI Module (%)
 > 📷 Table VI- Superiority Validation of ASI Module (%) 


#### 3) Feature Visualization Analysis:Through T-SNE [56], the feature space evolution of JVC-ASI at different training stages is visualized in Fig. 10. PU and PC are used as two source domains. From Fig. 10, we have the following observations. > 📷 Fig. 10. - T-SNE visualization of feature space evolution across training batches. 
Fig. 10. T-SNE visualization of feature space evolution across training batches.



##### a) Category separability improvement:From the first line, as the number of training batches increases from 20 to 160, the aggregation of features for each category improves significantly. At 20 batches, the features of different categories (e.g., healthy grass versus bare soil) overlap considerably, with fuzzy class boundaries. By batch 80, the compactness of features from the same category increases, and the separation between categories is also enhanced. By batch 160, each category forms an independent and clear feature cluster, with only a few outliers, indicating that the model continuously refines its learning of expressive features throughout training and stabilizes in the later stages.


##### b) Domain generalization enhancement:From the second line, the yellow and blue features from the two training source domains are highly mixed across all batches. Even at batch 160, the features from both domains do not form distinct domain boundaries. This indicates that the model does not overfit to the unique distribution of any single training domain and learns more generalizable features that are inherently tied to the categories themselves. This phenomenon of feature overlap within domains and the indistinct separation across domains demonstrates that the model’s learned features can consistently distinguish categories across different domains, reducing the impact of domain shift on model performance.
Taken together, the two types of visualizations suggest that JVC-ASI effectively balances cross-domain consistency and category structure invariance during training.


#### 4) Hyperparameter Sensitivity Analysis:We investigate the sensitivity of hyperparameters $\lambda _{1}$
, $\lambda _{2}$
, batch size, and learning rate. On “H13 + H18 $\rightarrow $
 PU/PC” and “PU + PC $\rightarrow $
 H13/H18” tasks, we vary each hyperparameter individually while keeping the others fixed. The results are shown in Fig. 11, from which we have the following observations.
Within the range of 0.1–2.0, the loss weight $\lambda _{1}$
 has a minimal impact on performance across all tasks. Specifically, for the PU and PC tasks, performance is optimal when $\lambda _{1}$
 is set to 0.1 or 1.0. For H13, the values of 0.1, 0.5, and 1.0 maintain good performance, while for H18, the values of 0.5 and 1.0 yield the best performance. Considering the robustness across tasks, $\lambda _{1}$
 is set to 1.0 for this study.
$\lambda _{2}$
 shows a more pronounced, task-dependent impact on performance. The PU and PC tasks are relatively robust to $\lambda _{2}$
 variation, with only minor fluctuations, whereas H13 achieves optimal performance at $\lambda _{2} {\,}= {\,}0.05$
 and 0.2. In contrast, H18 is highly sensitive, exhibiting a clear peak at $\lambda _{2}{\,}={\,}0.05$
. Based on these results, $\lambda _{2}$
 is set to 0.05.
Performance is relatively robust to the batch size, but we observe that performance on H13 is lowest when the batch size is set to 256, while H18 performs worst with a batch size of 512. Both batch sizes of 128 and 1024 yielded better performance. Considering both training efficiency and model performance, a batch size of 1024 is chosen for the experiments.
The learning rate is an important factor affecting the performance of JVC-ASI. In the “H13 + H18 $\rightarrow $
 PU/PC” setup, the OA first increases and then decreases as the learning rate increases, peaking at 0.006. In the “PU + PC $\rightarrow $
 H13/H18” setup, the OA steadily increases as the learning rate varies from 0.002 to 0.06, remains stable between 0.06 and 0.1, and shows no further improvement at higher learning rates. Thus, the learning rates are set to 0.006 and 0.06 for the first and second groups of tasks, respectively.
 > 📷 Fig. 11. - Hyperparameter sensitivity of JVC-ASI on OA values (%). 
Fig. 11. Hyperparameter sensitivity of JVC-ASI on OA values (%).



#### 5) Convergence Analysis:We investigate the convergence behavior of our proposed method JVC-ASI. The ${\mathcal {L}}_{\text {JVC-ASI}}$
 loss curves on two experiments are shown in Fig. 12. Obviously, the loss decreases rapidly during the initial stages of training, and eventually converges to a stable plateau. Specifically, for the “H13 + H18 $\rightarrow $
 PU/PC” task, the standard deviation of the final loss is 0.75, while for the “PU + PC $\rightarrow $
 H13/H18” task, the standard deviation is 0.47. This consistent decreasing trend indicates that our optimization objective (12) is well-defined. Meanwhile, the gradient-based optimization effectively integrates domain-invariant feature extraction, domain distribution alignment, and feature structure preservation, without introducing significant instability. > 📷 Fig. 12. - Convergence behavior of JVC-ASI. (a) H13H$18\rightarrow $
PU/PC task. (b) PU+PC$\rightarrow $
H13/H18 task. 
Fig. 12. Convergence behavior of JVC-ASI. (a) H13H$18\rightarrow $
PU/PC task. (b) PU+PC$\rightarrow $
H13/H18 task.

 SECTION V.


## Conclusion
In this study, we propose a novel HSI MDG method JVC-ASI. In JVC-ASI, the presented JVC module achieves stable cross-domain consistency constraints on domain-invariant features and thus has ability to well handle the issues of domain shift and spurious invariance. On this basis, the designed ASI module realizes stable ASI constrains and thus is capable of well mitigating the issues of ambiguous decision boundaries and semantic mismatch. The results of extensive experiments demonstrate the superiority and stability of JVC-ASI and its promising practical potential in HSI cross-domain generalization.
This work assumes that all samples in the target domain belong to known classes. However, in practical applications, scenarios involving unknown categories in the target domain are prevalent. In future work, we will further explore novel and credible open-set discrepancy modeling and incorporate it into JVC-ASI. By minimizing the risk discrepancy between the source and target domains regarding samples labeled as “unknown,” the extended method will be better applied for cross-domain generalization tasks in open-world HSI imaging.

---

**← 上一篇** → [[paper-notes/论文精读/4-跨域高光谱精读/14-第9讲-架构图逐块解析]] ｜ **下一篇 →** [[paper-notes/论文精读/4-跨域高光谱精读/00-索引 MOC]] ｜ **索引 →** [[paper-notes/论文精读/4-跨域高光谱精读/00-索引 MOC]]
