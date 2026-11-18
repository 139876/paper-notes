# -*- coding: utf-8 -*-
"""
用 matplotlib mathtext 把报告里的 $$...$$ 公式渲染成 PNG（供 PDF 使用）。

必须用带 matplotlib 的解释器运行（gtvenv）：
    /tmp/gtvenv/bin/python tools/_render_math.py <input.md>

输出：tools/_math/<sha1>.png  +  tools/_math/manifest.json
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["mathtext.fontset"] = "cm"
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "tools/_math")
DPI = 400

DISPLAY_RE = re.compile(r"\$\$(.+?)\$\$", re.S)


def _hash(latex: str) -> str:
    return hashlib.sha1(latex.strip().encode("utf-8")).hexdigest()[:16]


def render(latex: str, out_png: str) -> bool:
    """渲染一条公式；失败则返回 False（调用方回退到纯文本）。

    注意：matplotlib 的 mathtext 在 $...$ 内部遇到换行会「静默降级」为普通文本，
    因此必须先把换行/连续空白压成单个空格。
    """
    latex = " ".join(latex.split())
    tex = "$" + latex + "$"
    try:
        fig = plt.figure(figsize=(0.1, 0.1), dpi=DPI)
        t = fig.text(0, 0, tex, fontsize=13, color="#111111")
        fig.canvas.draw()
        bb = t.get_window_extent(fig.canvas.get_renderer())
        w, h = bb.width / fig.dpi, bb.height / fig.dpi
        fig.set_size_inches(max(w + 0.06, 0.2), max(h + 0.06, 0.2))
        t.set_position((0.03 / (w + 0.06), 0.03 / (h + 0.06)))
        fig.savefig(out_png, dpi=DPI, transparent=True,
                    bbox_inches="tight", pad_inches=0.02)
        plt.close(fig)
        return True
    except Exception as e:
        plt.close("all")
        print(f"  [math fail] {latex.strip()[:60]} -> {str(e)[:60]}")
        return False


def main() -> int:
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        ROOT, "report/图论综合应用报告-合订版.md")
    os.makedirs(CACHE, exist_ok=True)
    text = open(src, encoding="utf-8").read()
    formulas = [m.group(1).strip() for m in DISPLAY_RE.finditer(text)]
    manifest, ok, fail = {}, 0, 0
    for latex in formulas:
        latex = " ".join(latex.split())
        key = _hash(latex)
        png = os.path.join(CACHE, key + ".png")
        if not os.path.exists(png):
            if render(latex, png):
                ok += 1
            else:
                fail += 1
                continue
        manifest[key] = {"latex": latex, "png": os.path.relpath(png, ROOT)}
    with open(os.path.join(CACHE, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"[math] {len(formulas)} 条公式，渲染成功 {len(manifest)}，失败 {fail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
