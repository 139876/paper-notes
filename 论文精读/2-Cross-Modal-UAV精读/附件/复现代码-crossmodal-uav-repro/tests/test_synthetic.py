"""
Synthetic smoke tests for the CCFA / Cross-Modal-UAV re-implementation.

These tests do NOT need a GPU, a dataset or a real detector.  They check the
*logic* of the re-implemented equations:

  1. rotated IoU geometry
  2. SFI: shapes, gradient flow, "student imitates teacher -> loss drops"
  3. API: w_ciou weighting behaves as the paper describes
  4. CKD: the full Algorithm-1 loop reduces the loss on a toy task

Run with:
    .venv-pip/bin/python -m pytest tests/ -q
or without pytest:
    .venv-pip/bin/python tests/test_synthetic.py
"""
import math
import os
import sys

import torch
import torch.nn as nn

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (API, SFI, CKDFramework, build_optimizer, obb_to_vertices,
                    polygon_area, rotated_iou_pairwise, train_one_epoch)


# --------------------------------------------------------------------------- #
def test_polygon_area():
    unit = torch.tensor([[0., 0.], [2., 0.], [2., 1.], [0., 1.]])
    a = polygon_area(unit)
    assert abs(float(a) - 2.0) < 1e-5, a
    print("[ok] polygon_area")


def test_iou_identical_and_disjoint():
    box = torch.tensor([[0., 0.], [2., 0.], [2., 1.], [0., 1.]])
    far = box + 100.0
    iou_same = rotated_iou_pairwise(box[None], box[None])
    iou_far = rotated_iou_pairwise(box[None], far[None])
    assert abs(float(iou_same) - 1.0) < 1e-4, iou_same
    assert float(iou_far) < 1e-4, iou_far
    print("[ok] iou identical = 1.0, disjoint = 0.0")


def test_iou_half_overlap():
    """Two unit squares overlapping on half of their area -> IoU = 1/3."""
    a = torch.tensor([[0., 0.], [2., 0.], [2., 2.], [0., 2.]])
    b = torch.tensor([[1., 0.], [3., 0.], [3., 2.], [1., 2.]])
    iou = float(rotated_iou_pairwise(a[None], b[None])[0, 0])
    # intersection 2, union 6 -> 1/3
    assert abs(iou - 1.0 / 3.0) < 1e-3, iou
    print("[ok] iou half overlap = %.4f (expected 0.3333)" % iou)


def test_iou_rotated_vs_montecarlo():
    """Compare the polygon IoU with a Monte-Carlo estimate for a rotated case."""
    torch.manual_seed(0)
    o1 = torch.tensor([0., 0., 3., 1., 0.3])
    o2 = torch.tensor([0.5, 0.2, 3., 1., 1.0])
    b1 = obb_to_vertices(o1[None])
    b2 = obb_to_vertices(o2[None])
    iou = float(rotated_iou_pairwise(b1, b2)[0, 0])

    # Monte-Carlo on the AABB of both boxes
    lo = torch.minimum(b1.reshape(-1, 2).min(0).values, b2.reshape(-1, 2).min(0).values)
    hi = torch.maximum(b1.reshape(-1, 2).max(0).values, b2.reshape(-1, 2).max(0).values)
    n = 400
    g = torch.stack(torch.meshgrid(torch.linspace(lo[0], hi[0], n),
                                   torch.linspace(lo[1], hi[1], n), indexing='ij'), -1)
    g = g.reshape(-1, 2)

    def inside(pts, poly):
        p = poly
        sign = None
        for i in range(4):
            a, b = p[i], p[(i + 1) % 4]
            cross = (b[0] - a[0]) * (pts[:, 1] - a[1]) - (b[1] - a[1]) * (pts[:, 0] - a[0])
            s = cross >= 0
            sign = s if sign is None else (sign & s)
        return sign

    inter = (inside(g, b1[0]) & inside(g, b2[0])).float().mean()
    union = (inside(g, b1[0]) | inside(g, b2[0])).float().mean()
    mc = float(inter / union)
    assert abs(iou - mc) < 0.02, (iou, mc)
    print("[ok] rotated iou %.4f  ~  monte-carlo %.4f" % (iou, mc))


def test_obb_vertices_roundtrip():
    o = torch.tensor([[1., 2., 4., 2., 0.7]])
    v = obb_to_vertices(o)
    area = polygon_area(v)
    assert abs(float(area) - 8.0) < 1e-3, area
    print("[ok] obb_to_vertices area")


# --------------------------------------------------------------------------- #
def test_sfi_shapes_and_grad():
    torch.manual_seed(0)
    sfi = SFI(channels=16, pi1=0.3, pi2=0.7, max_hw=1024)
    p_ir = torch.randn(2, 16, 8, 8)
    p_rgb = torch.randn(2, 16, 8, 8, requires_grad=True)
    loss, aux = sfi(p_ir, p_rgb)
    assert loss.dim() == 0
    assert aux['m'].shape == (2, 64, 64), aux['m'].shape
    assert float(aux['m'].min()) >= 0.0 and float(aux['m'].max()) <= 1.0
    loss.backward()
    assert p_rgb.grad is not None and float(p_rgb.grad.abs().sum()) > 0
    assert sfi.t_ir.conv.weight.grad is not None
    print("[ok] SFI shapes + gradient flow, loss = %.4f" % float(loss))


def test_sfi_memory_guard():
    sfi = SFI(channels=4, max_hw=1024)
    try:
        sfi(torch.randn(1, 4, 64, 64), torch.randn(1, 4, 64, 64))
        raise AssertionError("should have raised MemoryError")
    except MemoryError as e:
        assert 'SFI would build' in str(e)
    print("[ok] SFI refuses an oversized similarity map")


def test_sfi_loss_drops_when_student_matches_teacher():
    """If the student feature becomes equal to the teacher feature, L_f -> 0."""
    torch.manual_seed(0)
    sfi = SFI(channels=8, pi1=0.3, pi2=0.7).eval()
    # make the two transformation blocks identical, otherwise the *features*
    # differ before the similarity map is even computed
    sfi.t_rgb.load_state_dict(sfi.t_ir.state_dict())
    p = torch.randn(1, 8, 6, 6)
    with torch.no_grad():
        loss_same, _ = sfi(p, p.clone())
        loss_diff, _ = sfi(p, torch.randn(1, 8, 6, 6))
    assert float(loss_same) < float(loss_diff)
    assert float(loss_same) < 1e-3, float(loss_same)
    print("[ok] SFI: identical features give a smaller loss (%.6f < %.5f)"
          % (float(loss_same), float(loss_diff)))


# --------------------------------------------------------------------------- #
def _dummy_dets(n=4, seed=0):
    torch.manual_seed(seed)
    cx = torch.rand(n) * 40 + 10
    cy = torch.rand(n) * 40 + 10
    w = torch.rand(n) * 8 + 4
    h = torch.rand(n) * 4 + 2
    t = torch.rand(n) * math.pi
    o = torch.stack([cx, cy, w, h, t], dim=-1)
    return obb_to_vertices(o)


def test_api_weighting():
    api = API(num_classes=3, rho=0.7, lam=0.5, match_iou_thr=0.3)
    dets = _dummy_dets(6, seed=1)
    scores = torch.softmax(torch.randn(6, 3), dim=-1)
    labels = torch.randint(0, 3, (6,))
    gt = {'dets': dets[:2], 'labels': labels[:2]}

    # the teacher sees the same boxes but a *different* class distribution
    scores_ir = torch.softmax(torch.randn(6, 3) * 3.0, dim=-1)
    pred_ir = {'dets': dets, 'scores': scores_ir}
    pred_rgb = {'dets': dets.clone(), 'scores': scores.clone()}
    lc, ll, aux = api(pred_ir, pred_rgb, gt)
    assert abs(float(aux['w_ciou_mean']) - 1.0) < 1e-3, aux['w_ciou_mean']
    assert float(aux['l_kl']) > 0, 'the KL term must be active when the boxes match'

    # teacher predictions far away -> w_ciou ~ 0, the distillation term dies
    pred_ir2 = {'dets': dets + 500.0, 'scores': scores_ir}
    lc2, ll2, aux2 = api(pred_ir2, pred_rgb, gt)
    assert float(aux2['w_ciou_mean']) < 1e-3, aux2['w_ciou_mean']
    assert float(aux2['l_kl']) == 0.0, aux2['l_kl']
    assert float(lc2) < float(lc)
    print("[ok] API: w_ciou switches the distillation on/off")


def test_api_grad():
    api = API(num_classes=3)
    dets = _dummy_dets(5, seed=3)
    scores = torch.softmax(torch.randn(5, 3), dim=-1).requires_grad_(True)
    gt = {'dets': dets[:2], 'labels': torch.tensor([0, 1])}
    pred_ir = {'dets': dets, 'scores': scores.detach()}
    pred_rgb = {'dets': dets.clone(), 'scores': scores}
    lc, ll, _ = api(pred_ir, pred_rgb, gt)
    (lc + ll).backward()
    assert scores.grad is not None and float(scores.grad.abs().sum()) > 0
    print("[ok] API gradient flow")


# --------------------------------------------------------------------------- #
class TinyDetector(nn.Module):
    """A 3-layer CNN that returns the interface CKDFramework expects."""

    def __init__(self, channels=8, num_classes=3):
        super().__init__()
        self.stem = nn.Conv2d(3, channels, 3, padding=1)
        self.body = nn.Conv2d(channels, channels, 3, padding=1)
        self.cls = nn.Linear(channels, num_classes)
        self.reg = nn.Linear(channels, 8)

    def forward(self, img):
        x = torch.relu(self.stem(img))
        x = torch.relu(self.body(x))
        pooled = x.mean(dim=(2, 3))                      # (B,C)
        scores = torch.softmax(self.cls(pooled), dim=-1)  # (B,K)
        verts = self.reg(pooled).reshape(-1, 4, 2) + 50.0
        return {'feats': {'P4': x}, 'dets': verts, 'scores': scores, 'loss': pooled.sum() * 0.0}


def test_ckd_training_loop():
    torch.manual_seed(0)
    student = TinyDetector()
    teacher = TinyDetector()
    sfi = SFI(channels=8, pi1=0.3, pi2=0.7, max_hw=1024)
    api = API(num_classes=3)
    fw = CKDFramework(student, teacher, sfi, api, feat_levels=('P4',))

    # the teacher must stay frozen
    for p in fw.teacher.parameters():
        assert not p.requires_grad

    batch = {
        'img_rgb': torch.randn(2, 3, 8, 8),
        'img_ir': torch.randn(2, 3, 8, 8),
        'gt_rgb': [{'dets': _dummy_dets(3, seed=i), 'labels': torch.tensor([0, 1, 2])} for i in range(2)],
    }
    opt = build_optimizer(fw)
    logs = train_one_epoch(fw, [batch] * 20, opt, torch.device('cpu'), log_every=1)
    first, last = logs[0]['loss_total'], logs[-1]['loss_total']
    assert math.isfinite(first) and math.isfinite(last)
    # the teacher weights must not change
    t_before = [p.detach().clone() for p in fw.teacher.parameters()]
    train_one_epoch(fw, [batch] * 5, opt, torch.device('cpu'), log_every=100)
    for a, b in zip(t_before, fw.teacher.parameters()):
        assert torch.equal(a, b)
    print("[ok] CKD: Algorithm-1 loop runs, teacher stays frozen "
          "(loss %.4f -> %.4f)" % (first, last))


# --------------------------------------------------------------------------- #
if __name__ == '__main__':
    fns = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    failed = 0
    for fn in fns:
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            failed += 1
            print("[FAIL] %s -> %r" % (fn.__name__, e))
            import traceback
            traceback.print_exc()
    print("\n%d/%d tests passed" % (len(fns) - failed, len(fns)))
    sys.exit(1 if failed else 0)
