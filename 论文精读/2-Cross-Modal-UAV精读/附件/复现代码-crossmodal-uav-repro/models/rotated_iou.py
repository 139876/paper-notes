"""
Rotated-box IoU (polygon based) in pure PyTorch -- no CUDA extension needed.

Why this file exists
--------------------
The paper's API module (Eq. 6) needs the IoU between two *oriented* bounding
boxes (4 vertices each):

    w_ciou = Area(D_RGB & D_IR) / Area(D_RGB | D_IR)

mmdetection / mmrotate normally compute this with a compiled CUDA extension
(`poly_nms`, `rbbox_overlaps`).  On an Apple-silicon Mac that extension cannot
be compiled, so the geometry is re-implemented here in plain PyTorch:

  * Sutherland-Hodgman convex polygon clipping  -> intersection polygon
  * shoelace formula                           -> polygon area

The implementation is fully vectorised over a pair of *sets* of boxes:
`rotated_iou_pairwise(boxes1, boxes2)` returns the (N, M) IoU matrix.

Input convention
----------------
boxes: Tensor (..., 4, 2) -- the four vertices of an oriented rectangle,
       ordered counter-clockwise (the function fixes the winding for you).
"""
from typing import Tuple

import torch

# The intersection of two convex polygons with 4 vertices each has at most
# 8 vertices; 16 gives plenty of head-room for the intermediate clipping
# steps.
_CAP = 16


def polygon_area(poly: torch.Tensor) -> torch.Tensor:
    """Shoelace area of a polygon.

    Args:
        poly: (..., N, 2) polygon vertices.
    Returns:
        (...,) unsigned area.
    """
    x, y = poly[..., 0], poly[..., 1]
    x_next = torch.roll(x, -1, dims=-1)
    y_next = torch.roll(y, -1, dims=-1)
    return 0.5 * (x * y_next - x_next * y).sum(dim=-1).abs()


def _ensure_ccw(boxes: torch.Tensor) -> torch.Tensor:
    """Flip a polygon to counter-clockwise order if needed.

    Args:
        boxes: (..., 4, 2)
    Returns:
        (..., 4, 2) CCW-ordered polygon.
    """
    x, y = boxes[..., 0], boxes[..., 1]
    x_next = torch.roll(x, -1, dims=-1)
    y_next = torch.roll(y, -1, dims=-1)
    signed = (x * y_next - x_next * y).sum(dim=-1)
    flip = signed < 0
    return torch.where(flip.unsqueeze(-1).unsqueeze(-1),
                       torch.flip(boxes, dims=[-2]), boxes)


def _cross(edge_pt: torch.Tensor, edge_dir: torch.Tensor, pt: torch.Tensor) -> torch.Tensor:
    """Signed area of the triangle (edge_pt, edge_pt+edge_dir, pt).

    Args:
        edge_pt:  (..., 2)
        edge_dir: (..., 2)
        pt:       (..., 2)
    Returns:
        (...)  > 0 means `pt` is on the inner side of the (CCW) edge.
    """
    return (edge_dir[..., 0] * (pt[..., 1] - edge_pt[..., 1])
            - edge_dir[..., 1] * (pt[..., 0] - edge_pt[..., 0]))


def _line_intersection(p1: torch.Tensor, p2: torch.Tensor,
                       q1: torch.Tensor, q2: torch.Tensor) -> torch.Tensor:
    """Intersection of the line (p1, p2) with the line (q1, q2).

    All args are (..., 2).  Returns (..., 2).  Degenerate (parallel) lines
    return the midpoint of the two "p" points instead of NaN.
    """
    x1, y1 = p1[..., 0], p1[..., 1]
    x2, y2 = p2[..., 0], p2[..., 1]
    x3, y3 = q1[..., 0], q1[..., 1]
    x4, y4 = q2[..., 0], q2[..., 1]

    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    safe_den = torch.where(den.abs() < 1e-12, torch.full_like(den, 1e-12), den)

    a = x1 * y2 - y1 * x2
    b = x3 * y4 - y3 * x4
    px = (a * (x3 - x4) - (x1 - x2) * b) / safe_den
    py = (a * (y3 - y4) - (y1 - y2) * b) / safe_den
    out = torch.stack([px, py], dim=-1)
    return torch.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0).clamp(-1e6, 1e6)


def _gather_points(x: torch.Tensor, index: torch.Tensor) -> torch.Tensor:
    """Gather along the vertex dimension.

    Args:
        x:     (..., CAP, 2)
        index: (..., CAP) long
    Returns:
        (..., CAP, 2)
    """
    idx = index.unsqueeze(-1).expand(*index.shape, 2)
    return torch.gather(x, -2, idx)


def _clip_convex(subject: torch.Tensor, clip: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
    """Sutherland-Hodgman clip of `subject` by the convex polygon `clip`.

    Args:
        subject: (P, Q, _CAP, 2) polygon to clip (Q = 4 vertices)
        clip:    (P, Q, 4, 2)    convex CCW clipping polygon
    Returns:
        out:  (P, Q, _CAP, 2) intersection polygon (invalid slots are zero)
        mask: (P, Q, _CAP) bool, True = valid vertex
    """
    p, q = subject.shape[0], subject.shape[1]
    out = subject.clone()
    mask = torch.zeros(p, q, _CAP, dtype=torch.bool, device=subject.device)
    mask[..., :4] = True

    ar = torch.arange(_CAP, device=subject.device).view(1, 1, _CAP)

    for i in range(4):
        a = clip[..., i, :]                     # (P,Q,2)
        b = clip[..., (i + 1) % 4, :]           # (P,Q,2)
        edge_dir = b - a

        count = mask.sum(dim=-1)                               # (P,Q)
        # "previous" vertex: j-1, and for j == 0 it is the last valid one
        prev_idx = torch.where(ar > 0, ar - 1,
                               (count - 1).clamp(min=0).unsqueeze(-1))
        prev = _gather_points(out, prev_idx)
        prev_mask = torch.gather(mask, -1, prev_idx)
        prev_inside = torch.gather(_cross(a.unsqueeze(-2), edge_dir.unsqueeze(-2),
                                          out) >= -1e-9, -1, prev_idx)

        inside = (_cross(a.unsqueeze(-2), edge_dir.unsqueeze(-2), out) >= -1e-9) & mask
        inter = _line_intersection(prev, out, a.unsqueeze(-2), b.unsqueeze(-2))
        crossing = (prev_inside ^ inside) & mask & prev_mask

        # emit order per slot: intersection point first, then the vertex
        # interleave the emission order: [inter_0, cur_0, inter_1, cur_1, ...]
        cand = torch.stack([inter, out], dim=3).reshape(p, q, 2 * _CAP, 2)
        cand_mask = torch.stack([crossing, inside], dim=3).reshape(p, q, 2 * _CAP)

        # stable sort -> valid candidates first, original cyclic order kept
        order = torch.argsort((~cand_mask).to(torch.int8), dim=-1, stable=True)
        cand = _gather_points(cand, order)
        cand_mask = torch.gather(cand_mask, -1, order)
        out = cand[..., :_CAP, :]
        mask = cand_mask[..., :_CAP]

    return out, mask


def _masked_area(poly: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    """Area of a polygon stored in a fixed-size buffer.

    The valid vertices occupy the slots ``0 .. count-1`` in cyclic order; the
    wrap-around edge (last -> first) is handled explicitly.

    Args:
        poly:  (..., CAP, 2)
        mask:  (..., CAP) bool
    Returns:
        (...,) area
    """
    count = mask.sum(dim=-1)                                  # (...,)
    ar = torch.arange(poly.shape[-2], device=poly.device).expand(count.shape + (poly.shape[-2],))
    nxt = torch.where(ar < (count.unsqueeze(-1) - 1), ar + 1,
                      torch.zeros_like(ar))                   # wrap to slot 0
    nxt = nxt.clamp(max=poly.shape[-2] - 1)

    x, y = poly[..., 0], poly[..., 1]
    x_next = torch.gather(x, -1, nxt)
    y_next = torch.gather(y, -1, nxt)
    valid = (ar < count.unsqueeze(-1)).to(poly.dtype)
    contrib = (x * y_next - x_next * y) * valid
    return 0.5 * contrib.sum(dim=-1).abs()


def rotated_iou_pairwise(boxes1: torch.Tensor, boxes2: torch.Tensor) -> torch.Tensor:
    """Pairwise IoU between two sets of oriented boxes.

    Args:
        boxes1: (N, 4, 2)
        boxes2: (M, 4, 2)
    Returns:
        (N, M) IoU matrix.
    """
    n, m = boxes1.shape[0], boxes2.shape[0]
    if n == 0 or m == 0:
        return boxes1.new_zeros((n, m))

    b1 = _ensure_ccw(boxes1)
    b2 = _ensure_ccw(boxes2)

    a1 = polygon_area(b1)                              # (N,)
    a2 = polygon_area(b2)                              # (M,)

    subject = b1.unsqueeze(1).expand(n, m, 4, 2)       # (N,M,4,2)
    clip = b2.unsqueeze(0).expand(n, m, 4, 2)          # (N,M,4,2)

    # put the subject into the fixed-size buffer
    subj_buf = torch.zeros(n, m, _CAP, 2, dtype=b1.dtype, device=b1.device)
    subj_buf[..., :4, :] = subject
    clip_buf = torch.zeros(n, m, _CAP, 2, dtype=b1.dtype, device=b1.device)
    clip_buf[..., :4, :] = clip

    inter_poly, inter_mask = _clip_convex(subj_buf, clip_buf)
    inter_area = _masked_area(inter_poly, inter_mask)

    union = a1.unsqueeze(1) + a2.unsqueeze(0) - inter_area
    return inter_area / union.clamp(min=1e-7)


def obb_to_vertices(boxes: torch.Tensor) -> torch.Tensor:
    """Convert (cx, cy, w, h, angle) into 4 vertices.

    Args:
        boxes: (..., 5) -> (cx, cy, w, h, theta), theta in radians
    Returns:
        (..., 4, 2) vertices
    """
    cx, cy, w, h, t = boxes.unbind(-1)
    cos, sin = torch.cos(t), torch.sin(t)
    a, b = w / 2.0, h / 2.0
    corners = torch.stack([
        torch.stack([-a, -b], dim=-1),
        torch.stack([a, -b], dim=-1),
        torch.stack([a, b], dim=-1),
        torch.stack([-a, b], dim=-1),
    ], dim=-2)                                          # (...,4,2)
    rot = torch.stack([cos, -sin, sin, cos], dim=-1).reshape(*boxes.shape[:-1], 2, 2)
    return corners @ rot.transpose(-1, -2) + torch.stack([cx, cy], dim=-1).unsqueeze(-2)


def vertices_to_obb(verts: torch.Tensor) -> torch.Tensor:
    """Inverse of :func:`obb_to_vertices`.

    Args:
        verts: (..., 4, 2)
    Returns:
        (..., 5) -> (cx, cy, w, h, theta)
    """
    center = verts.mean(dim=-2)
    d = verts - center.unsqueeze(-2)
    theta = 0.5 * torch.atan2(
        2 * (d[..., 0, 0] * d[..., 0, 1] + d[..., 1, 0] * d[..., 1, 1]),
        d[..., 0, 0] ** 2 + d[..., 1, 1] ** 2 - d[..., 0, 1] ** 2 - d[..., 1, 0] ** 2)
    u = torch.stack([torch.cos(theta), torch.sin(theta)], dim=-1)
    v = torch.stack([-torch.sin(theta), torch.cos(theta)], dim=-1)
    proj_u = (d * u.unsqueeze(-2)).sum(-1)
    proj_v = (d * v.unsqueeze(-2)).sum(-1)
    w = 2 * proj_u.abs().max(dim=-1).values
    h = 2 * proj_v.abs().max(dim=-1).values
    return torch.stack([center[..., 0], center[..., 1], w, h, theta], dim=-1)
