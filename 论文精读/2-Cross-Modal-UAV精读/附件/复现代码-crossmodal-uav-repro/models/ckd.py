"""
Cross-Modal Knowledge Distillation framework (CKD)  --  Section III-D,
Algorithm 1 of Li et al., "Cross-Modal Object Detection via UAV".

The framework is intentionally detector-agnostic: you hand it

  * ``student``:  any callable that maps an RGB image batch to
                  {'feats': [level tensors], 'dets': (N,4,2), 'scores': (N,K)}
  * ``teacher``:  the frozen IR detector with the same interface

and it wires the two losses (SFI + API) on top of the student's own detection
loss, exactly like Algorithm 1 in the paper.

Algorithm 1 (paper)
--------------------
for e = 1 .. E:
    X_IR, X_RGB  <- batch
    F_IR, p_IR, R_IR   <- theta_IR(X_IR)          # teacher, FROZEN
    F_RGB, p_RGB, R_RGB <- theta_RGB(X_RGB)        # student, trainable
    L <- loss(F_IR, p_IR, R_IR, F_RGB, p_RGB, R_RGB)
    theta_RGB <- theta_RGB - eta * dL/dtheta_RGB

Deployment (paper, Section III-E)
--------------------------------
At test time the IR detector, the SFI module and the API module are removed:
only the RGB detector is shipped to the UAV.  That is the whole selling point
of the method -- no IR sensor on board, same accuracy as a two-sensor system.
"""
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import torch
import torch.nn as nn


class CKDFramework(nn.Module):
    """Glue code between a student detector and the two distillation modules.

    Args:
        student:  nn.Module, the RGB detector (trainable)
        teacher:  nn.Module, the IR detector (frozen)
        sfi:      models.sfi.SFI
        api:      models.api.API
        det_weight:  weight of the student's own detection loss
        feat_levels:  which FPN levels feed the SFI module (freedom #1).
                      The paper does not say; 'P4'/'P5' are the affordable
                      choices because M is a (H*W) x (H*W) matrix.
    """

    def __init__(self,
                 student: nn.Module,
                 teacher: nn.Module,
                 sfi: nn.Module,
                 api: nn.Module,
                 det_weight: float = 1.0,
                 feat_levels: Sequence[str] = ('P4',)):
        super().__init__()
        self.student = student
        self.teacher = teacher
        self.sfi = sfi
        self.api = api
        self.det_weight = det_weight
        self.feat_levels = tuple(feat_levels)

        # freeze the teacher -- Algorithm 1 line "theta_IR do not need to be
        # further updated"
        for p in self.teacher.parameters():
            p.requires_grad_(False)
        self.teacher.eval()

    # ------------------------------------------------------------------ utils
    def train(self, mode: bool = True):  # type: ignore[override]
        super().train(mode)
        if mode:
            self.teacher.eval()      # keep BN statistics of the teacher frozen
        return self

    def _pick_levels(self, feats: Dict[str, torch.Tensor]) -> List[torch.Tensor]:
        out = []
        for name in self.feat_levels:
            if name in feats:
                out.append(feats[name])
        if not out:                       # fall back to every available level
            out = list(feats.values())
        return out

    # ---------------------------------------------------------------- forward
    def forward(self, batch: Dict[str, torch.Tensor]) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """One optimisation step's worth of computation (Algorithm 1, lines 8-10).

        Args:
            batch: dict with
                'img_rgb': (B,3,H,W)  RGB images
                'img_ir':  (B,3,H,W)  IR images
                'gt_rgb':  list of B dicts {'dets': (M,4,2), 'labels': (M,)}
                'gt_ir':   list of B dicts (used only by the teacher loss, if any)
        Returns:
            total_loss, aux
        """
        # ---- teacher (no grad) ------------------------------------------- #
        with torch.no_grad():
            out_ir = self.teacher(batch['img_ir'])
        # ---- student ------------------------------------------------------ #
        out_rgb = self.student(batch['img_rgb'])

        aux: Dict[str, torch.Tensor] = {}

        # ---- the student's own detection loss ----------------------------- #
        det_loss = out_rgb.get('loss', torch.zeros((), device=out_rgb['scores'].device))
        total = self.det_weight * det_loss
        aux['loss_det'] = det_loss.detach()

        # ---- SFI: feature level ------------------------------------------ #
        f_ir = self._pick_levels(out_ir['feats'])
        f_rgb = self._pick_levels(out_rgb['feats'])
        loss_f = torch.zeros((), device=total.device)
        if f_ir and f_rgb:
            for a, b in zip(f_ir, f_rgb):
                l, sfi_aux = self.sfi(a.detach(), b)
                loss_f = loss_f + l
            aux['loss_sfi'] = loss_f.detach()
        else:
            aux['loss_sfi'] = loss_f.detach()
        total = total + loss_f

        # ---- API: prediction level ---------------------------------------- #
        # the paper applies the distillation image by image (the teacher and
        # the student see a *paired* image), so we loop over the batch.
        loss_cls = torch.zeros((), device=total.device)
        loss_loc = torch.zeros((), device=total.device)
        w_list: List[torch.Tensor] = []
        for i in range(batch['img_rgb'].shape[0]):
            sl = slice(i, i + 1)
            pred_ir = {
                'dets': out_ir['dets'][sl].reshape(-1, 4, 2),
                'scores': out_ir['scores'][sl].reshape(-1, out_ir['scores'].shape[-1]),
            }
            pred_rgb = {
                'dets': out_rgb['dets'][sl].reshape(-1, 4, 2),
                'scores': out_rgb['scores'][sl].reshape(-1, out_rgb['scores'].shape[-1]),
            }
            gt = batch['gt_rgb'][i]
            lc, ll, a_aux = self.api(pred_ir, pred_rgb, gt)
            loss_cls = loss_cls + lc
            loss_loc = loss_loc + ll
            w_list.append(a_aux['w_ciou_mean'].reshape(1))
        n = max(1, batch['img_rgb'].shape[0])
        loss_cls = loss_cls / n
        loss_loc = loss_loc / n
        total = total + loss_cls + loss_loc
        aux['loss_cls'] = loss_cls.detach()
        aux['loss_loc'] = loss_loc.detach()
        aux['w_ciou_mean'] = torch.cat(w_list).mean() if w_list else torch.zeros(())

        aux['loss_total'] = total.detach()
        return total, aux


# --------------------------------------------------------------------------- #
#  Algorithm 1
# --------------------------------------------------------------------------- #
def train_one_epoch(framework: CKDFramework,
                    loader: Iterable[Dict[str, torch.Tensor]],
                    optimizer: torch.optim.Optimizer,
                    device: torch.device,
                    max_steps: Optional[int] = None,
                    log_every: int = 50) -> List[Dict[str, float]]:
    """Algorithm 1 of the paper, as a normal PyTorch training loop.

    Args:
        framework:  CKDFramework
        loader:     iterable of batches
        optimizer:  SGD with lr=0.001, momentum=0.9, weight_decay=0.0005
        device:     cpu / cuda / mps
    Returns:
        list of per-step logged dicts
    """
    framework.train()
    logs: List[Dict[str, float]] = []
    for step, batch in enumerate(loader):
        if max_steps is not None and step >= max_steps:
            break
        batch = {
            'img_rgb': batch['img_rgb'].to(device),
            'img_ir': batch['img_ir'].to(device),
            'gt_rgb': [
                {'dets': g['dets'].to(device), 'labels': g['labels'].to(device)}
                for g in batch['gt_rgb']
            ],
        }
        optimizer.zero_grad(set_to_none=True)
        loss, aux = framework(batch)
        loss.backward()
        optimizer.step()

        if step % log_every == 0:
            rec = {k: float(v) for k, v in aux.items()}
            rec['step'] = step
            logs.append(rec)
    return logs


def build_optimizer(framework: CKDFramework, lr: float = 0.001,
                    momentum: float = 0.9, weight_decay: float = 0.0005):
    """SGD + the paper's hyper-parameters.  Only the student is optimised."""
    params = [p for p in framework.student.parameters() if p.requires_grad]
    return torch.optim.SGD(params, lr=lr, momentum=momentum, weight_decay=weight_decay)


def build_lr_scheduler(optimizer: torch.optim.Optimizer, epochs: int = 50, step: int = 20):
    """Step LR: multiply by 0.1 every `step` epochs (paper: every 20 epochs)."""
    return torch.optim.lr_scheduler.StepLR(optimizer, step_size=step, gamma=0.1)
