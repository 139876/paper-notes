"""
Selective Feature Imitation (SFI)  --  Li et al., "Cross-Modal Object Detection
via UAV", IEEE T-VT 2023,  Section III-B, Eq. (2) ~ (5).

The module transfers *feature* knowledge from a frozen IR detector (teacher)
to an RGB detector (student) in a way that deliberately emphasises the
*residual* (cross-modal-specific) features instead of the common ones.

Paper equations reproduced here
------------------------------
Eq.(2)  M      = (F_IR . F_RGB) / (||F_IR||_1 ||F_RGB||_1)   # similarity map
Eq.(3)  M_bar  = 1 - M                                        # inverse map
Eq.(4)  F_com_IR  = M . F_IR      F_res_IR  = M_bar . F_IR
         F_com_RGB = F_RGB . M    F_res_RGB = F_RGB . M_bar
Eq.(5)  L_f = pi1 * ||F_com_IR - F_com_RGB||^2
             + pi2 * ||F_res_IR - F_res_RGB||^2

Three places where the paper under-specifies the implementation are exposed as
explicit constructor arguments.  They are the "degrees of freedom" you have to
decide yourself -- see docs/REPRO_PLAN.md.

  * ``sim_mode``  : how Eq.(4) orients the two feature matrices when we
                    subtract them (the paper uses M for IR and M for RGB,
                    which is asymmetric).
  * ``norm``      : the L1 normalisation of Eq.(2) is ambiguous -- global
                    scalar or per-position vector?
  * ``reduction`` : is the squared distance in Eq.(5) a Frobenius norm or a
                    mean of squared errors?
"""
from typing import Dict, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


class TransformBlock(nn.Module):
    """T(.) of the paper: 3x3 Conv -> BatchNorm -> ReLU.

    The paper explicitly argues that a *learnable* transformation is used
    (instead of the non-parametric ReLU used by classic feature distillation)
    because ReLU's limited mapping range loses information.

    Args:
        in_channels:  channel number of the input feature map
        out_channels: channel number of the output (must match the paired
                      modality so that the inner product is meaningful)
    """

    def __init__(self, in_channels: int, out_channels: int = None):
        super().__init__()
        out_channels = in_channels if out_channels is None else out_channels
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False)
        self.bn = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.relu(self.bn(self.conv(x)))


def _l1_normalize_rows(x: torch.Tensor, eps: float = 1e-8) -> torch.Tensor:
    """Normalise each *row* (i.e. each spatial position) to unit L1 norm.

    Args:
        x: (..., N, C)
    Returns:
        (..., N, C)
    """
    return x / x.abs().sum(dim=-1, keepdim=True).clamp(min=eps)


def _l1_normalize_cols(x: torch.Tensor, eps: float = 1e-8) -> torch.Tensor:
    """Normalise each *column* (i.e. each spatial position) to unit L1 norm.

    Args:
        x: (..., C, N)
    Returns:
        (..., C, N)
    """
    return x / x.abs().sum(dim=-2, keepdim=True).clamp(min=eps)


def _l2_normalize_rows(x: torch.Tensor, eps: float = 1e-8) -> torch.Tensor:
    return x / x.norm(dim=-1, keepdim=True).clamp(min=eps)


def _l2_normalize_cols(x: torch.Tensor, eps: float = 1e-8) -> torch.Tensor:
    return x / x.norm(dim=-2, keepdim=True).clamp(min=eps)


class SFI(nn.Module):
    """Selective Feature Imitation.

    Args:
        channels:   channel number C of the backbone feature maps
        pi1:        weight of the *common* feature term   (paper: 0.3)
        pi2:        weight of the *residual* feature term (paper: 0.7)
        norm:       'l1_rowcol' (default) | 'l2_cos' | 'l1_global'
        sim_mode:   'paper' (default) | 'sym'
        reduction:  'frobenius' (default) | 'mse'
        loss_scale: 'raw' (default, literal Eq.5) | 'mean' (divide by H*W*C so
                    that the loss does not explode with the feature size)
        clamp_sim:  clamp the similarity map into [0, 1] (default True)
        max_hw:     guard -- refuse to build an M larger than this many
                    entries and tell the user what to do (default 4096)
    """

    def __init__(self,
                 channels: int,
                 pi1: float = 0.3,
                 pi2: float = 0.7,
                 norm: str = 'l1_rowcol',
                 sim_mode: str = 'paper',
                 reduction: str = 'frobenius',
                 loss_scale: str = 'raw',
                 clamp_sim: bool = True,
                 max_hw: int = 4096):
        super().__init__()
        assert norm in ('l1_rowcol', 'l2_cos', 'l1_global')
        assert sim_mode in ('paper', 'sym')
        assert reduction in ('frobenius', 'mse')
        assert loss_scale in ('raw', 'mean')
        self.channels = channels
        self.pi1 = pi1
        self.pi2 = pi2
        self.norm = norm
        self.sim_mode = sim_mode
        self.reduction = reduction
        self.loss_scale = loss_scale
        self.clamp_sim = clamp_sim
        self.max_hw = max_hw

        # T(.) transformation blocks -- one per modality (they are NOT shared:
        # IR and RGB live in different feature spaces).
        self.t_ir = TransformBlock(channels, channels)
        self.t_rgb = TransformBlock(channels, channels)

    # ------------------------------------------------------------------ utils
    def _similarity(self, f_ir: torch.Tensor, f_rgb: torch.Tensor) -> torch.Tensor:
        """Eq.(2): similarity map M.

        Args:
            f_ir:  (B, HW, C)   teacher feature, position-major
            f_rgb: (B, C, HW)   student feature, channel-major
        Returns:
            (B, HW, HW)
        """
        if self.norm == 'l1_rowcol':
            a = _l1_normalize_rows(f_ir)
            b = _l1_normalize_cols(f_rgb)
        elif self.norm == 'l2_cos':
            a = _l2_normalize_rows(f_ir)
            b = _l2_normalize_cols(f_rgb)
        else:  # 'l1_global' -- the literal formula of the paper
            eps = 1e-8
            a = f_ir / f_ir.abs().sum().clamp(min=eps)
            b = f_rgb / f_rgb.abs().sum().clamp(min=eps)
        m = torch.bmm(a, b)
        if self.clamp_sim:
            m = m.clamp(0.0, 1.0)
        return m

    def _distance(self, a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
        """Squared distance used in Eq.(5)."""
        diff = a - b
        if self.reduction == 'frobenius':
            return diff.pow(2).sum(dim=(-2, -1))          # ||.||_F^2
        return diff.pow(2).mean(dim=(-2, -1))              # mean of squares

    # ---------------------------------------------------------------- forward
    def forward(self, p_ir: torch.Tensor, p_rgb: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """Compute the SFI loss.

        Args:
            p_ir:  (B, C, H, W)  backbone feature of the IR image  (teacher)
            p_rgb: (B, C, H, W)  backbone feature of the RGB image (student)
        Returns:
            loss:  scalar tensor (Eq. 5)
            aux:   dict with the intermediate tensors (for debugging / figures)
        """
        assert p_ir.shape == p_rgb.shape, \
            "IR and RGB features must have the same shape, got %s vs %s" % (p_ir.shape, p_rgb.shape)
        b, c, h, w = p_ir.shape
        hw = h * w
        if hw > self.max_hw:
            raise MemoryError(
                "SFI would build a %dx%d similarity map (%.1f GB in fp32).\n"
                "Apply SFI on a lower FPN level (P4/P5), or pool the features "
                "spatially before the similarity map.\n"
                "See docs/REPRO_PLAN.md -> 'freedom #1'." % (hw, hw, hw * hw * 4 / 1e9))

        f_ir = self.t_ir(p_ir)                    # (B,C,H,W)  Eq.(2) input
        f_rgb = self.t_rgb(p_rgb)                 # (B,C,H,W)

        f_ir = f_ir.flatten(2).transpose(1, 2)    # (B,HW,C)   as in the paper
        f_rgb = f_rgb.flatten(2)                  # (B,C,HW)   as in the paper

        m = self._similarity(f_ir, f_rgb)         # Eq.(2)  (B,HW,HW)
        m_bar = 1.0 - m                          # Eq.(3)

        if self.sim_mode == 'paper':
            # literal reading of Eq.(4)
            com_ir = torch.bmm(m, f_ir)           # (B,HW,C)
            res_ir = torch.bmm(m_bar, f_ir)       # (B,HW,C)
            com_rgb = torch.bmm(f_rgb, m)         # (B,C,HW)
            res_rgb = torch.bmm(f_rgb, m_bar)     # (B,C,HW)
            com_rgb = com_rgb.transpose(1, 2)     # (B,HW,C)
            res_rgb = res_rgb.transpose(1, 2)
        else:
            # symmetric variant: use the same mixing matrix for both modalities
            m_sym = 0.5 * (m + m.transpose(1, 2))
            m_bar_sym = 1.0 - m_sym
            com_ir = torch.bmm(m_sym, f_ir)                      # (B,HW,C)
            res_ir = torch.bmm(m_bar_sym, f_ir)                  # (B,HW,C)
            f_rgb_t = f_rgb.transpose(1, 2)                      # (B,HW,C)
            com_rgb = torch.bmm(m_sym, f_rgb_t)                  # (B,HW,C)
            res_rgb = torch.bmm(m_bar_sym, f_rgb_t)              # (B,HW,C)

        l_com = self._distance(com_ir, com_rgb)   # (B,)
        l_res = self._distance(res_ir, res_rgb)   # (B,)
        if self.loss_scale == 'mean':
            l_com = l_com / (hw * c)
            l_res = l_res / (hw * c)
        loss = self.pi1 * l_com.mean() + self.pi2 * l_res.mean()   # Eq.(5)

        aux = {
            'f_ir': f_ir, 'f_rgb': f_rgb, 'm': m, 'm_bar': m_bar,
            'com_ir': com_ir, 'com_rgb': com_rgb,
            'res_ir': res_ir, 'res_rgb': res_rgb,
            'l_common': l_com, 'l_residual': l_res,
            'sim_mean': m.mean().detach(),
        }
        return loss, aux
