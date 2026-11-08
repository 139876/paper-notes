# crossmodal-uav-repro

Re-implementation of **"Cross-Modal Object Detection via UAV"**
(Li et al., IEEE Transactions on Vehicular Technology, 2023, 72(8): 10898-10909).

> The paper has **no official code**.  This repository is an independent
> re-implementation of the two modules the paper proposes (SFI and API) plus
> the training loop of Algorithm 1, written so that the *logic* can be
> verified on a laptop without a GPU.

## What is here

| file | paper reference | what it does |
|---|---|---|
| `models/sfi.py` | Section III-B, Eq.(2)-(5) | Selective Feature Imitation: similarity map, common/residual split, weighted feature loss |
| `models/api.py` | Section III-C, Eq.(6)-(13) | Adaptive Prediction Imitation: cross-modal IoU weight, weighted KL, smooth-L1 localisation loss |
| `models/ckd.py` | Section III-D, Algorithm 1 | Frozen teacher + trainable student, hybrid loss, SGD/StepLR with the paper's hyper-parameters |
| `models/rotated_iou.py` | needed by Eq.(6) | Pure-PyTorch polygon IoU (Sutherland-Hodgman clipping + shoelace).  Replaces the CUDA extension `poly_nms` so that the geometry runs on a CPU-only Mac. |
| `tests/test_synthetic.py` | -- | 11 synthetic tests (geometry, gradients, weight behaviour, training loop) |
| `docs/REPRO_PLAN.md` | -- | The full reproduction plan: 4 levels, 3 routes, the 6 under-specified decisions |
| `docs/PAPER_SPEC.md` | -- | Equation-by-equation mapping table: paper -> code -> what the paper left open |

## Run the tests

```bash
/Users/yoyo/Documents/Codex/2026-10-28/xxx/.venv-pip/bin/python tests/test_synthetic.py
```

Expected output ends with `11/11 tests passed`.

## Environment

```
Python 3.9.6   (/usr/bin/python3 -m venv .venv-pip)
PyTorch 2.2.2  (CPU wheel for macOS arm64)
numpy 1.26.4
```

No GPU required.  The full training run needs a Linux + CUDA box
(`mmcv-full` / `mmrotate` do not build on macOS arm64).

## Status

- [x] SFI implemented (3 normalisation modes, 2 matrix-orientation modes)
- [x] API implemented (w_ciou weighted KL + smooth-L1, greedy IoU matching)
- [x] Algorithm 1 training loop with a frozen teacher
- [x] Pure-PyTorch rotated IoU, cross-validated against Monte-Carlo
- [x] 11/11 synthetic tests pass
- [ ] Level 0: Oriented R-CNN baseline on DroneVehicle (needs GPU)
- [ ] Level 1-3: SFI / API on top of the baseline (needs GPU)
- [ ] Level 4: ablation sweep (needs GPU)
