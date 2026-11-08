"""
Adaptive Prediction Imitation (API)  --  Li et al., "Cross-Modal Object
Detection via UAV", IEEE T-VT 2023,  Section III-C, Eq. (6) ~ (13).

API transfers *prediction* knowledge (classification + localisation) from the
frozen IR detector to the RGB detector.  The novel part is the cross-modal IoU
weight w_ciou, which automatically *switches off* the distillation for the
objects the two modalities disagree about (e.g. an object that is only visible
in IR at night and is therefore not annotated in RGB).

Paper equations reproduced here
------------------------------
Eq.(6)   w_ciou = Area(D_RGB & D_IR) / Area(D_RGB | D_IR)
Eq.(7)   L_KL   = w_ciou * 1/N sum_i sum_k p_IR,k log(p_IR,k / p_RGB,k)
Eq.(8)   L_CE   = 1/N sum_i sum_k y_k log p_RGB,k
Eq.(9)   L_cls  = rho * L_KL + (1 - rho) * L_CE          (rho  = 0.7)
Eq.(10)  L_ts_loc  = w_ciou * ||R_IR - R_RGB||^2_2
Eq.(11)  L_sl_loc  = 1/4 sum_j z_j,  z_j = smoothL1(r_j^RGB - r_j)
Eq.(13)  L_loc  = lambda * L_ts_loc + (1 - lambda) * L_sl_loc   (lambda = 0.5)

Under-specified points of the paper, handled here as explicit options:
  * how teacher detections are paired with student detections   ('match')
  * how the per-object quantities are reduced to a scalar        ('reduce')
  * whether the smooth-L1 is applied to the vertex *distance* or to the
    8 raw coordinates                                           ('sl1_mode')
  * the IoU threshold used to attach a student detection to a GT ('gt_iou_thr')
"""
from typing import Dict, List, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

from .rotated_iou import rotated_iou_pairwise


# --------------------------------------------------------------------------- #
#  helpers
# --------------------------------------------------------------------------- #
def greedy_iou_match(ious: torch.Tensor, iou_thr: float = 0.5) -> Tuple[torch.Tensor, torch.Tensor]:
    """Greedy one-to-one matching by descending IoU.

    Args:
        ious: (N_teacher, N_student)
        iou_thr: minimum IoU to accept a pair
    Returns:
        idx_t: (M,) indices into the teacher array
        idx_s: (M,) indices into the student array
    """
    n_t, n_s = ious.shape
    if n_t == 0 or n_s == 0:
        empty = torch.zeros(0, dtype=torch.long, device=ious.device)
        return empty, empty.clone()

    order = torch.argsort(ious.reshape(-1), descending=True)
    taken_t = torch.zeros(n_t, dtype=torch.bool, device=ious.device)
    taken_s = torch.zeros(n_s, dtype=torch.bool, device=ious.device)
    idx_t: List[int] = []
    idx_s: List[int] = []
    for flat in order.tolist():
        i, j = flat // n_s, flat % n_s
        if taken_t[i] or taken_s[j]:
            continue
        if ious[i, j] < iou_thr:
            break
        taken_t[i] = True
        taken_s[j] = True
        idx_t.append(i)
        idx_s.append(j)
    if not idx_t:
        empty = torch.zeros(0, dtype=torch.long, device=ious.device)
        return empty, empty.clone()
    return (torch.tensor(idx_t, dtype=torch.long, device=ious.device),
            torch.tensor(idx_s, dtype=torch.long, device=ious.device))


def smooth_l1_pointwise(pred: torch.Tensor, target: torch.Tensor,
                        beta: float = 1.0) -> torch.Tensor:
    """z_j of Eq.(12) computed on the *distance* of each vertex.

    Args:
        pred:   (M, 4, 2) predicted vertices
        target: (M, 4, 2) ground-truth vertices
    Returns:
        (M,) per-object loss
    """
    diff = (pred - target).norm(dim=-1)          # (M,4) distance of each vertex
    absd = diff.abs()
    z = torch.where(absd < beta, 0.5 * diff.pow(2) / beta, absd - 0.5 * beta)
    return z.mean(dim=-1)                        # 1/4 sum_j z_j


def smooth_l1_elementwise(pred: torch.Tensor, target: torch.Tensor,
                          beta: float = 1.0) -> torch.Tensor:
    """Same but on the 8 raw coordinates instead of the 4 vertex distances."""
    diff = pred - target
    absd = diff.abs()
    z = torch.where(absd < beta, 0.5 * diff.pow(2) / beta, absd - 0.5 * beta)
    return z.mean(dim=(-2, -1))


# --------------------------------------------------------------------------- #
#  the module
# --------------------------------------------------------------------------- #
class API(nn.Module):
    """Adaptive Prediction Imitation.

    Args:
        num_classes: number of foreground categories K
        rho:         classification distillation rate (paper: 0.7)
        lam:         localisation distillation rate (paper: 0.5)
        match_iou_thr: IoU threshold used to pair teacher/student detections
                       (the paper does not state it -- freedom #6)
        gt_iou_thr:  IoU threshold used to attach a student detection to a
                     ground-truth box (0.5, the standard detection convention)
        match:       'greedy' (default) | 'none' (assume the two arrays are
                     already aligned)
        reduce:      'mean' (default) | 'sum'
        sl1_mode:    'vector' (default, faithful to Eq.11-12) | 'elementwise'
    """

    def __init__(self,
                 num_classes: int,
                 rho: float = 0.7,
                 lam: float = 0.5,
                 match_iou_thr: float = 0.5,
                 gt_iou_thr: float = 0.5,
                 match: str = 'greedy',
                 reduce: str = 'mean',
                 sl1_mode: str = 'vector'):
        super().__init__()
        assert match in ('greedy', 'none')
        assert reduce in ('mean', 'sum')
        assert sl1_mode in ('vector', 'elementwise')
        self.num_classes = num_classes
        self.rho = rho
        self.lam = lam
        self.match_iou_thr = match_iou_thr
        self.gt_iou_thr = gt_iou_thr
        self.match = match
        self.reduce = reduce
        self.sl1_mode = sl1_mode

    # ------------------------------------------------------------------ match
    def _match(self, d_ir: torch.Tensor, d_rgb: torch.Tensor):
        """Pair the teacher and the student detections.

        Args:
            d_ir:  (N,4,2) teacher vertices
            d_rgb: (M,4,2) student vertices
        Returns:
            (idx_t, idx_s, w_ciou)
        """
        if self.match == 'none':
            n = min(len(d_ir), len(d_rgb))
            if n == 0:
                empty = torch.zeros(0, dtype=torch.long, device=d_ir.device)
                return empty, empty.clone(), torch.zeros(0, device=d_ir.device)
            ious = rotated_iou_pairwise(d_ir[:n], d_rgb[:n])
            w = torch.diagonal(ious)
            idx = torch.arange(n, device=d_ir.device)
            return idx, idx.clone(), w
        ious = rotated_iou_pairwise(d_ir, d_rgb)
        idx_t, idx_s = greedy_iou_match(ious, self.match_iou_thr)
        if len(idx_t) == 0:
            return idx_t, idx_s, torch.zeros(0, device=d_ir.device)
        w = ious[idx_t, idx_s]                                     # Eq.(6)
        return idx_t, idx_s, w

    # ---------------------------------------------------------------- forward
    def forward(self,
                pred_ir: Dict[str, torch.Tensor],
                pred_rgb: Dict[str, torch.Tensor],
                gt_rgb: Dict[str, torch.Tensor]) -> Tuple[torch.Tensor, torch.Tensor, Dict[str, torch.Tensor]]:
        """Compute the API loss.

        Args:
            pred_ir:  teacher output, dict with
                        'dets'   (N,4,2) oriented-box vertices
                        'scores' (N,K)  class probabilities (softmaxed)
            pred_rgb: student output, same structure
            gt_rgb:   ground truth for the RGB image, dict with
                        'dets'   (M,4,2) vertices
                        'labels' (M,)   class ids
        Returns:
            loss_cls, loss_loc, aux
        """
        d_ir = pred_ir['dets'].detach()
        p_ir = pred_ir['scores'].detach()
        d_rgb = pred_rgb['dets']
        p_rgb = pred_rgb['scores']

        device = p_rgb.device
        zero = torch.zeros((), device=device, dtype=p_rgb.dtype)

        # ---- teacher <-> student matching --------------------------------- #
        idx_t, idx_s, w = self._match(d_ir, d_rgb)

        if len(idx_t) == 0:
            l_kl = zero
        else:
            p_t = p_ir[idx_t]                                   # (M,K)
            p_s = p_rgb[idx_s]                                  # (M,K)
            eps = 1e-8
            # Eq.(7): KL( p_IR || p_RGB ), weighted by w_ciou
            kl_elem = (p_t * (torch.log(p_t + eps) - torch.log(p_s + eps))).sum(dim=-1)
            l_kl = (w * kl_elem).mean() if self.reduce == 'mean' else (w * kl_elem).sum()

        # ---- student <-> ground truth assignment ------------------------- #
        l_ce, l_sl, assign = self._gt_terms(d_rgb, p_rgb, gt_rgb)

        # ---- localisation distillation ------------------------------------ #
        if len(idx_t) == 0:
            l_ts = zero
        else:
            r_ir = d_ir[idx_t]                                  # (M,4,2)
            r_rgb = d_rgb[idx_s]                                # (M,4,2)
            dist = (r_ir - r_rgb).pow(2).sum(dim=(-2, -1))      # ||.||^2_2
            l_ts = (w * dist).mean() if self.reduce == 'mean' else (w * dist).sum()

        # Eq.(9)
        loss_cls = self.rho * l_kl + (1.0 - self.rho) * l_ce
        # Eq.(13)
        loss_loc = self.lam * l_ts + (1.0 - self.lam) * l_sl

        aux = {
            'w_ciou_mean': w.mean() if len(w) else zero.detach(),
            'num_matched': torch.tensor(float(len(idx_t)), device=device),
            'l_kl': l_kl, 'l_ce': l_ce, 'l_ts': l_ts, 'l_sl': l_sl,
        }
        return loss_cls, loss_loc, aux

    # ------------------------------------------------------------------ parts
    def _gt_terms(self, d_rgb: torch.Tensor, p_rgb: torch.Tensor,
                  gt_rgb: Dict[str, torch.Tensor]):
        """Eq.(8) cross entropy and Eq.(11) smooth-L1 against the ground truth.

        Every student detection is attached to the ground-truth box with the
        largest IoU (standard detection practice).  A detection that is not
        attached is treated as background.

        Args:
            d_rgb:  (N,4,2) student vertices
            p_rgb:  (N,K)  student class probabilities
            gt_rgb: dict with 'dets' (M,4,2) and 'labels' (M,)
        Returns:
            l_ce, l_sl, assignment
        """
        device = p_rgb.device
        labels = gt_rgb['labels'].to(device).long()
        gt = gt_rgb['dets'].to(device)
        n = d_rgb.shape[0]

        if n == 0 or labels.numel() == 0:
            zero = torch.zeros((), device=device, dtype=p_rgb.dtype)
            return zero, zero, None

        ious = rotated_iou_pairwise(d_rgb, gt)          # (N, M)
        best_iou, best_idx = ious.max(dim=1)
        assigned = best_iou > self.gt_iou_thr

        # ---- Eq.(8): classification ------------------------------------- #
        eps = 1e-8
        logp = torch.log(p_rgb.clamp(min=eps))
        if assigned.any():
            cls = labels[best_idx[assigned]].clamp(0, self.num_classes - 1)
            l_pos = -logp[assigned].gather(1, cls.unsqueeze(1)).squeeze(1)
        else:
            l_pos = p_rgb.new_zeros(0)
        if (~assigned).any():
            # background: push the probability of every class towards 0
            l_neg = -torch.log((1.0 - p_rgb[~assigned]).clamp(min=eps))
            l_bg = l_neg.sum(dim=-1)
        else:
            l_bg = p_rgb.new_zeros(0)
        ce_terms = torch.cat([l_pos, l_bg]) if (l_pos.numel() + l_bg.numel()) else p_rgb.new_zeros(0)
        l_ce = ce_terms.mean() if self.reduce == 'mean' else ce_terms.sum()

        # ---- Eq.(11): localisation --------------------------------------- #
        if assigned.any():
            pred_k = d_rgb[assigned]
            tgt_k = gt[best_idx[assigned]]
            fn = smooth_l1_pointwise if self.sl1_mode == 'vector' else smooth_l1_elementwise
            per_obj = fn(pred_k, tgt_k)
            l_sl = per_obj.mean() if self.reduce == 'mean' else per_obj.sum()
        else:
            l_sl = torch.zeros((), device=device, dtype=p_rgb.dtype)

        return l_ce, l_sl, (best_idx, assigned)
