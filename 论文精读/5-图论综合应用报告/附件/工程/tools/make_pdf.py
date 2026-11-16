# -*- coding: utf-8 -*-
"""
Markdown -> PDF（reportlab），公式用 matplotlib mathtext 预先渲染成 PNG。

运行（需要带 reportlab 的解释器）：
    /Users/yoyo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
        tools/make_pdf.py [input.md] [output.pdf]

若公式缓存缺失，会自动调用 tools/_render_math.py（需要 matplotlib 的解释器）生成。
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import subprocess
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (ActionFlowable, BaseDocTemplate, Flowable, Frame, Image,
                                KeepTogether, PageBreak, PageTemplate, Paragraph,
                                Spacer, Table, TableStyle, HRFlowable)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATH_DIR = os.path.join(ROOT, "tools/_math")
MATH_MANIFEST = os.path.join(MATH_DIR, "manifest.json")
GTVENV_PY = "/tmp/gtvenv/bin/python"

TITLE = "基于图论的重庆大学虎溪校区快递配送路径优化研究"
C_DARK = colors.HexColor("#16324f")
C_MID = colors.HexColor("#2e5c7a")
C_ACC = colors.HexColor("#2e7d9e")
C_GRID = colors.HexColor("#b8c4d0")
C_ROW = colors.HexColor("#f4f7fa")
C_CODEBG = colors.HexColor("#f4f6f8")
C_QBG = colors.HexColor("#fdf9ef")
C_QBAR = colors.HexColor("#d9a441")

# ------------------------------------------------------------------ 字体
F_BODY, F_BOLD, F_HEAD = "Song", "Song-Bold", "Hei"
F_MONO = "Menlo"
F_CJK = "Hei"   # 代码块里中文片段的兜底字体


def register_fonts() -> None:
    """注册中文字体（macOS 系统字体）。"""
    songti = "/System/Library/Fonts/Supplemental/Songti.ttc"
    heiti = "/System/Library/Fonts/STHeiti Medium.ttc"
    # Songti.ttc: 0=SC-Black 1=SC-Bold 3=SC-Light；再找 Regular
    body_idx = None
    for idx in range(0, 10):
        try:
            f = TTFont(f"SongProbe{idx}", songti, subfontIndex=idx)
            name = f.face.name.decode() if isinstance(f.face.name, bytes) else str(f.face.name)
            if "Songti-SC-Regular" in name or "SongtiSC-Regular" in name:
                body_idx = idx
                break
        except Exception:
            pass
    if body_idx is None:
        body_idx = 3  # Songti SC Light
    pdfmetrics.registerFont(TTFont(F_BODY, songti, subfontIndex=body_idx))
    pdfmetrics.registerFont(TTFont(F_BOLD, songti, subfontIndex=1))
    pdfmetrics.registerFont(TTFont(F_HEAD, heiti, subfontIndex=0))
    # 等宽拉丁字体（Menlo 真等宽，且覆盖 ∈ ← ∞ ≤ ≥ 等数学符号）
    menlo = "/System/Library/Fonts/Menlo.ttc"
    if os.path.exists(menlo):
        pdfmetrics.registerFont(TTFont(F_MONO, menlo, subfontIndex=0))
    pdfmetrics.registerFontFamily(F_BODY, normal=F_BODY, bold=F_BOLD,
                                  italic=F_BODY, boldItalic=F_BOLD)
    pdfmetrics.registerFontFamily(F_HEAD, normal=F_HEAD, bold=F_HEAD,
                                  italic=F_HEAD, boldItalic=F_HEAD)


# ------------------------------------------------------------------ LaTeX
LATEX_CMD = {
    r"\times": "×", r"\cdot": "·", r"\le": "≤", r"\leq": "≤",
    r"\ge": "≥", r"\geq": "≥", r"\ne": "≠", r"\neq": "≠",
    r"\approx": "≈", r"\in": "∈", r"\notin": "∉",
    r"\forall": "任意", r"\exists": "∃", r"\cup": "∪", r"\cap": "∩",
    r"\setminus": "∖", r"\sum": "Σ", r"\prod": "Π",
    r"\min": "min", r"\max": "max", r"\log": "log",
    r"\ldots": "…", r"\dots": "…", r"\lfloor": "⌊", r"\rfloor": "⌋",
    r"\quad": "  ", r"\qquad": "    ", r"\big": "", r"\left": "", r"\right": "",
    r"\rightarrow": "→", r"\leftarrow": "←", r"\to": "→", r"\sim": "~",
    r"\emptyset": "∅", r"\infinity": "∞",
}


def latex_to_text(s: str) -> str:
    """行内 LaTeX -> 纯文本（用于正文里的小公式）。"""
    s = re.sub(r"\\(?:text|mathrm|mathbf|mathit|operatorname|mathcal)\{([^{}]*)\}", r"\1", s)
    for k, v in LATEX_CMD.items():
        s = s.replace(k, v)
    s = s.replace(r"\{", "{").replace(r"\}", "}")
    s = re.sub(r"_\{([^{}]*)\}", r"_\1", s)
    s = re.sub(r"\^\{([^{}]*)\}", r"^\1", s)
    s = s.replace("\\", "")
    return re.sub(r"[ \t]{2,}", " ", s).strip()


def esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# CJK / 全角标点：等宽字体没有这些字形，会渲染成 ■，需切回中文字体
CJK_RE = re.compile(r"([\u2e80-\u303f\u3040-\u9fff\uf900-\ufaff\uff00-\uffef]+)")


def cjk_wrap(t: str) -> str:
    """把已转义文本中的 CJK 片段包进中文字体，避免缺字形变方块。"""
    return CJK_RE.sub(lambda m: '<font face="%s">%s</font>' % (F_CJK, m.group(1)), t)


# ------------------------------------------------------------------ 解析
def split_row(line: str):
    """按 | 切分表格行（处理 \\| 转义）。"""
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    cells, cur, i = [], [], 0
    while i < len(line):
        ch = line[i]
        if ch == "\\" and i + 1 < len(line) and line[i + 1] == "|":
            cur.append("|"); i += 2; continue
        if ch == "|":
            cells.append("".join(cur).strip()); cur = []; i += 1; continue
        cur.append(ch); i += 1
    cells.append("".join(cur).strip())
    return cells


def parse(md: str):
    lines = md.split("\n")
    blocks, i, n = [], 0, len(lines)
    while i < n:
        raw = lines[i]
        s = raw.strip()
        if not s:
            i += 1; continue
        if s.startswith("```"):
            i += 1; buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i]); i += 1
            i += 1
            blocks.append(("code", "\n".join(buf))); continue
        if s.startswith("$$"):
            i += 1; buf = []
            if s.endswith("$$") and len(s) > 2:
                buf.append(s[2:-2]); i += 1
            else:
                while i < n:
                    t = lines[i].strip()
                    if t.endswith("$$"):
                        buf.append(t[:-2]); i += 1; break
                    buf.append(t); i += 1
            blocks.append(("math", " ".join("\n".join(buf).split()))); continue
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            blocks.append((f"h{len(m.group(1))}", m.group(2).strip())); i += 1; continue
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", s):
            blocks.append(("hr", None)); i += 1; continue
        if s.startswith("|") and i + 1 < n and re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i])); i += 1
            if len(rows) >= 2:
                blocks.append(("table", (rows[0], rows[2:])))
            continue
        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", s)
        if m:
            blocks.append(("img", (m.group(1), m.group(2)))); i += 1; continue
        if s.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i])); i += 1
            blocks.append(("quote", "\n".join(buf).strip())); continue
        if re.match(r"^\s*([-*+]|\d+[.)])\s+", raw):
            items = []
            while i < n:
                t = lines[i]
                if not t.strip():
                    if i + 1 < n and re.match(r"^\s{2,}\S", lines[i + 1]):
                        if items:
                            items[-1] += " " + lines[i + 1].strip(); i += 2; continue
                    break
                mm = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", t)
                if mm and len(mm.group(1)) < 3:
                    items.append(mm.group(3)); i += 1; continue
                if items and (t.startswith("  ") or t.startswith("\t")):
                    items[-1] += " " + t.strip(); i += 1; continue
                break
            blocks.append(("ul", items)); continue
        buf = []
        while i < n and lines[i].strip() and \
                not re.match(r"^\s*([-*+]|\d+[.)])\s+", lines[i]) and \
                not lines[i].strip().startswith(("#", ">", "|", "```", "$$", "![")) and \
                not re.match(r"^(-{3,}|\*{3,}|_{3,})$", lines[i].strip()):
            buf.append(lines[i].strip()); i += 1
        if buf:
            txt = " ".join(buf)
            # 题注：**表 N　xxx** / **图 N　xxx**
            m = re.match(r"^\*\*\s*([表图])\s*(\d+)\s*[　\s]\s*(.+?)\s*\*\*$", txt)
            if m:
                blocks.append(("cap", (m.group(1), m.group(2), m.group(3))))
            else:
                blocks.append(("p", txt))
        else:
            i += 1
    return blocks


# ------------------------------------------------------------------ 行内
CODE_TOKEN = "\x00CODE%d\x00"


def inline(text: str) -> str:
    """Markdown 行内 -> reportlab 段落标记。"""
    codes = []

    def _stash(m):
        codes.append(m.group(1))
        return CODE_TOKEN % (len(codes) - 1)
    text = re.sub(r"`([^`]+)`", _stash, text)
    text = esc(text)
    # 行内公式
    def _math(m):
        return esc(latex_to_text(m.group(1)))
    text = re.sub(r"\$([^$\n]+?)\$", _math, text)
    # 链接
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
                  r'<link href="\2" color="#2e7d9e"><u>\1</u></link>', text)
    # 粗体 / 斜体
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text, flags=re.S)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", text, flags=re.S)
    # 代码回填
    for i, c in enumerate(codes):
        text = text.replace(
            CODE_TOKEN % i,
            f'<font face="{F_MONO}" size="8.4" color="#1f3b52">'
            f'{cjk_wrap(esc(c))}</font>')
    return text


# ------------------------------------------------------------------ 样式
def build_styles():
    S = {}
    S["h1"] = ParagraphStyle("h1", fontName=F_HEAD, fontSize=17, leading=24,
                              textColor=C_DARK, alignment=TA_CENTER,
                              spaceBefore=6, spaceAfter=12)
    S["h2"] = ParagraphStyle("h2", fontName=F_HEAD, fontSize=13, leading=19,
                              textColor=C_DARK, spaceBefore=15, spaceAfter=8,
                              leftIndent=6)
    S["h3"] = ParagraphStyle("h3", fontName=F_HEAD, fontSize=11.5, leading=17,
                              textColor=C_MID, spaceBefore=11, spaceAfter=6)
    S["h4"] = ParagraphStyle("h4", fontName=F_HEAD, fontSize=10.5, leading=16,
                              textColor=C_MID, spaceBefore=9, spaceAfter=5)
    S["p"] = ParagraphStyle("p", fontName=F_BODY, fontSize=10.2, leading=17.5,
                             alignment=TA_JUSTIFY, spaceAfter=7, firstLineIndent=0)
    S["li"] = ParagraphStyle("li", fontName=F_BODY, fontSize=10.2, leading=17,
                              spaceAfter=3.5, leftIndent=15, bulletIndent=4)
    S["tc"] = ParagraphStyle("tc", fontName=F_BODY, fontSize=8.4, leading=11.8,
                              textColor=colors.HexColor("#1a1a1a"))
    S["th"] = ParagraphStyle("th", fontName=F_HEAD, fontSize=8.6, leading=12,
                              textColor=colors.white)
    S["code"] = ParagraphStyle("code", fontName=F_MONO, fontSize=7.6, leading=10.6,
                                textColor=colors.HexColor("#22303c"))
    S["quote"] = ParagraphStyle("quote", fontName=F_BODY, fontSize=9.8, leading=16,
                                 textColor=colors.HexColor("#4a3c1c"))
    S["cap"] = ParagraphStyle("cap", fontName=F_BODY, fontSize=8.6, leading=12,
                               alignment=TA_CENTER, textColor=colors.HexColor("#6b7a88"),
                               spaceAfter=8)
    # 正式题注：表题在表上方、图题在图下方，五号黑体居中
    S["capt"] = ParagraphStyle("capt", fontName=F_HEAD, fontSize=9.4, leading=14,
                                alignment=TA_CENTER, textColor=C_DARK,
                                spaceBefore=9, spaceAfter=4)
    S["capf"] = ParagraphStyle("capf", fontName=F_HEAD, fontSize=9.4, leading=14,
                                alignment=TA_CENTER, textColor=C_DARK,
                                spaceBefore=5, spaceAfter=11)
    # wordWrap="CJK"：按中文字符边界断行。
    # 否则中英混排的两端对齐会把行内空白拉成巨大空隙。
    for k in ("p", "li", "tc", "th", "quote", "capt", "capf"):
        S[k].wordWrap = "CJK"
    return S


class SmartPageBreak(ActionFlowable):
    """章节分页。

    与 reportlab 的 PageBreak 区别：PageBreak 无条件翻页，如果当前页已经是
    一张空白页（前一段内容刚好排满上一页），就会多出一张只有页眉页脚的空页。
    这里在翻页前检查「当前页是否已有内容」，空页则直接跳过。
    """

    locChanger = 1

    def __init__(self):
        ActionFlowable.__init__(self, ())

    def apply(self, doc):
        if getattr(doc, "_curPageFlowableCount", 0) <= 0:
            return                      # 当前页是空的，不必再翻
        doc.handle_pageBreak()


# ------------------------------------------------------------------ 目录页码
_CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6,
           "七": 7, "八": 8, "九": 9, "十": 10}


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", s or "")


def toc_key(label: str):
    """目录行首（'第 1 章' / '附录 A'）-> 统一 key（'第1章' / '附录A'）。"""
    t = _norm(label)
    m = re.match(r"^第([0-9一二三四五六七八九十]+)章$", t)
    if m:
        g = m.group(1)
        n = int(g) if g.isdigit() else _CN_NUM.get(g)
        return f"第{n}章" if n else None
    m = re.match(r"^附录([A-D])$", t)
    if m:
        return f"附录{m.group(1)}"
    if t == "参考文献":
        return "参考文献"
    return None


def h1_key(payload: str):
    """一级标题（'第一章 绪论'）-> 统一 key。"""
    t = _norm(payload)
    m = re.match(r"^第([一二三四五六七八九十]+)章", t)
    if m:
        n = _CN_NUM.get(m.group(1))
        return f"第{n}章" if n else None
    m = re.match(r"^附录([A-D])", t)
    if m:
        return f"附录{m.group(1)}"
    if t == "参考文献":
        return "参考文献"
    if t == "目录":
        return "目录"
    return None


def collect_chapters(blocks):
    """所有一级标题 -> {key: 标题原文}。"""
    out = {}
    for kind, payload in blocks:
        if kind == "h1":
            k = h1_key(payload)
            if k:
                out[k] = payload
    return out


def augment_toc(blocks, toc_pages):
    """给「目录」表追加一列「页码」。页码未知时填 '—'。"""
    toc_idx = None
    for i, (kind, payload) in enumerate(blocks):
        if kind == "h1" and _norm(payload) == "目录":
            toc_idx = i
            break
    if toc_idx is None:
        return blocks
    for j in range(toc_idx + 1, len(blocks)):
        kind, payload = blocks[j]
        if kind == "h1":
            break
        if kind == "table":
            head, rows = payload
            if head and _norm(head[0]) == "章节":
                new_rows = []
                for r in rows:
                    key = toc_key(r[0]) if r else None
                    pg = str(toc_pages.get(key, "—")) if key else "—"
                    new_rows.append(list(r) + [pg])
                blocks[j] = ("table", (list(head) + ["页码"], new_rows))
            break
    return blocks


def chapter_at(page_no, chapter_map):
    """页码 -> 所在章节名（页眉用）。"""
    name = ""
    for start, title in chapter_map:
        if start <= page_no:
            name = title
        else:
            break
    return name


def _first_body_line(text: str):
    """去掉页眉页脚后的第一行正文（章节页就是标题行）。"""
    for ln in (text or "").split("\n"):
        s = ln.strip()
        if not s:
            continue
        if s == TITLE:
            continue
        if re.match(r"^[—-]\s*\d+\s*[—-]$", s):
            continue
        return s
    return ""


def measure_toc(pdf_path, chapters):
    """从已生成的 PDF 里量出每个一级标题所在页码。

    判定方式：章节页的「首行正文」就是该章的一级标题（每章另起一页），
    比全文包含匹配更精确 —— 不会把目录里的一行误判成章节位置。
    """
    try:
        from pypdf import PdfReader
    except Exception:
        return {}
    try:
        pages = [(pg.extract_text() or "") for pg in PdfReader(pdf_path).pages]
    except Exception:
        return {}
    # 目录页 = 含独立一行「目录」的页
    toc_page = -1
    for i, t in enumerate(pages):
        if any(ln.strip() == "目录" for ln in t.split("\n")):
            toc_page = i
            break
    out = {}
    for key, title in chapters.items():
        needle = _norm(title)
        if not needle:
            continue
        if key == "目录":
            if toc_page >= 0:
                out[key] = toc_page + 1
            continue
        for i, t in enumerate(pages):
            if i <= toc_page:
                continue
            if _norm(_first_body_line(t)) == needle:
                out[key] = i + 1
                break
    return out


class TocFlowable(Flowable):
    """正式目录：条目 + 点引导线 + 右对齐页码。"""

    def __init__(self, entries, width, leading=18.0, size=10.4):
        Flowable.__init__(self)
        self.entries = entries
        self.width = width
        self.leading = leading
        self.size = size
        self.height = leading * len(entries)

    def wrap(self, availWidth, availHeight):
        return (self.width, self.height)

    def draw(self):
        # reportlab 的 drawOn 已把画布平移到本 flowable 的左下角，
        # 因此这里用局部坐标 (0, 0) 起画
        c = self.canv
        x0 = 0
        y = self.height
        for text, page in self.entries:
            y -= self.leading
            c.setFont(F_BODY, self.size)
            c.setFillColor(colors.HexColor("#1d2733"))
            c.drawString(x0, y, text)
            pw = c.stringWidth(str(page), F_BODY, self.size)
            tw = c.stringWidth(text, F_BODY, self.size)
            x1 = x0 + tw + 7
            x2 = x0 + self.width - pw - 7
            if x2 > x1:
                c.setStrokeColor(colors.HexColor("#9fb0c0"))
                c.setLineWidth(0.6)
                c.setDash(1, 2.2)
                c.line(x1, y + 3.0, x2, y + 3.0)
                c.setDash()
            c.setFillColor(C_DARK)
            c.setFont(F_BODY, self.size)
            c.drawRightString(x0 + self.width, y, str(page))


# ------------------------------------------------------------------ 构建
def build_flowables(blocks, styles, math_manifest, content_w, base_dir):
    # 章节 h1 之前紧邻的 hr 是冗余的（h1 自身已带一条横线），而且它可能
    # 被单独挤到新的一页，形成几乎空白的孤页 —— 直接去掉
    cleaned = []
    for i, (kind, payload) in enumerate(blocks):
        if kind == "hr":
            j = i + 1
            while j < len(blocks) and blocks[j][0] == "hr":
                j += 1
            if j < len(blocks) and blocks[j][0] == "h1":
                continue
        cleaned.append((kind, payload))
    blocks = cleaned

    flow = []
    first_h1 = True
    for kind, payload in blocks:
        if kind == "h1":
            if not first_h1:
                flow.append(SmartPageBreak())
            first_h1 = False
            flow.append(Paragraph(inline(payload), styles["h1"]))
            flow.append(HRFlowable(width="100%", thickness=1.6, color=C_DARK,
                                    spaceBefore=2, spaceAfter=12))
        elif kind in ("h2", "h3", "h4"):
            flow.append(Paragraph(inline(payload), styles[kind]))
            if kind == "h2":
                flow.append(HRFlowable(width="22%", thickness=2.2, color=C_ACC,
                                        spaceBefore=0, spaceAfter=7,
                                        hAlign="LEFT"))
        elif kind == "p":
            flow.append(Paragraph(inline(payload), styles["p"]))
        elif kind == "ul":
            for it in payload:
                bullet = "•" if not re.match(r"^\d+[.)]", payload[0] or "") else ""
                flow.append(Paragraph(inline(it), styles["li"],
                                      bulletText="•"))
        elif kind == "cap":
            which, num, title = payload
            st = styles["capt"] if which == "表" else styles["capf"]
            flow.append(Paragraph(f"{which} {num}　{title}", st))
        elif kind == "hr":
            flow.append(Spacer(1, 5))
            flow.append(HRFlowable(width="100%", thickness=0.5,
                                    color=colors.HexColor("#ccd6e0"),
                                    spaceBefore=4, spaceAfter=8))
        elif kind == "quote":
            inner = []
            for ln in payload.split("\n"):
                ln = ln.strip()
                if not ln:
                    continue
                if re.match(r"^([-*+]|\d+[.)])\s+", ln):
                    inner.append(Paragraph(inline(re.sub(r"^([-*+]|\d+[.)])\s+", "• ", ln)),
                                           styles["quote"]))
                else:
                    inner.append(Paragraph(inline(ln), styles["quote"]))
            t = Table([[inner]], colWidths=[content_w - 6])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), C_QBG),
                ("LINEBEFORE", (0, 0), (0, -1), 3, C_QBAR),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]))
            flow.append(t)
            flow.append(Spacer(1, 8))
        elif kind == "code":
            lines = payload.split("\n")
            while lines and not lines[0].strip():
                lines.pop(0)
            while lines and not lines[-1].strip():
                lines.pop()
            if not lines:
                continue
            # 先把空格转成 &nbsp;（保留缩进），再切 CJK 字体，
            # 顺序不能反：否则会把 <font face="..."> 标签内的空格吃掉
            txt = "<br/>".join(
                cjk_wrap(esc(l).replace(" ", "&nbsp;")) for l in lines)
            t = Table([[Paragraph(txt, styles["code"])]], colWidths=[content_w - 4])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), C_CODEBG),
                ("LINEBEFORE", (0, 0), (0, -1), 2.5, C_ACC),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            flow.append(t)
            flow.append(Spacer(1, 8))
        elif kind == "table":
            head, rows = payload
            # 目录表 -> 正式的点引导线目录
            if head and _norm(head[0]) == "章节" and rows:
                entries = []
                for r in rows:
                    if len(r) >= 4:
                        entries.append((f"{r[0]}　{r[1]}", r[3]))
                    elif len(r) >= 2:
                        entries.append((f"{r[0]}　{r[1]}", "—"))
                flow.append(Spacer(1, 4))
                flow.append(TocFlowable(entries, content_w))
                flow.append(Spacer(1, 12))
                continue
            ncol = len(head)
            data = [[Paragraph(inline(c), styles["th"]) for c in head]]
            for r in rows:
                r = (r + [""] * ncol)[:ncol]
                data.append([Paragraph(inline(c), styles["tc"]) for c in r])
            # 列宽按内容长度分配
            weights = []
            for c in range(ncol):
                mx = len(head[c])
                for r in rows[:60]:
                    if c < len(r):
                        mx = max(mx, min(len(r[c]), 60))
                weights.append(max(4, mx))
            tot = sum(weights)
            widths = [content_w * w / tot for w in weights]
            t = Table(data, colWidths=widths, repeatRows=1)
            style = [
                ("BACKGROUND", (0, 0), (-1, 0), C_DARK),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, C_GRID),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ]
            for i in range(1, len(data)):
                if i % 2 == 0:
                    style.append(("BACKGROUND", (0, i), (-1, i), C_ROW))
            t.setStyle(TableStyle(style))
            flow.append(t)
            flow.append(Spacer(1, 9))
        elif kind == "img":
            alt, src = payload
            p = src if os.path.isabs(src) else os.path.join(base_dir, src)
            if not os.path.exists(p):
                p2 = os.path.join(ROOT, src.lstrip("./"))
                p = p2 if os.path.exists(p2) else p
            if not os.path.exists(p):
                continue
            from PIL import Image as PILImage
            iw, ih = PILImage.open(p).size
            w = min(content_w, iw)
            h = w * ih / iw
            maxh = 225 * mm
            if h > maxh:
                h = maxh; w = h * iw / ih
            flow.append(Image(p, width=w, height=h))
            flow.append(Spacer(1, 3))
        elif kind == "math":
            key = hashlib.sha1(payload.strip().encode("utf-8")).hexdigest()[:16]
            entry = math_manifest.get(key)
            if entry:
                p = os.path.join(ROOT, entry["png"])
                if os.path.exists(p):
                    from PIL import Image as PILImage
                    iw, ih = PILImage.open(p).size
                    w = min(content_w - 20, iw)
                    h = w * ih / iw
                    if h > 34 * mm:
                        h = 34 * mm; w = h * iw / ih
                    img = Image(p, width=w, height=h)
                    img.hAlign = "CENTER"
                    flow.append(Spacer(1, 3))
                    flow.append(img)
                    flow.append(Spacer(1, 9))
                    continue
            flow.append(Paragraph(esc(latex_to_text(payload)), styles["p"]))
    return flow


def build_cover(blocks, content_w):
    """封面：题目 + 课程信息表 + 摘要 + 关键词。"""
    st_title = ParagraphStyle("ct", fontName=F_HEAD, fontSize=21, leading=30,
                               textColor=C_DARK, alignment=TA_CENTER)
    st_sub = ParagraphStyle("cs", fontName=F_HEAD, fontSize=13, leading=22,
                             textColor=C_MID, alignment=TA_CENTER)
    st_org = ParagraphStyle("co", fontName=F_BODY, fontSize=11.5, leading=20,
                             textColor=colors.HexColor("#3b4b5a"), alignment=TA_CENTER)
    st_h2 = ParagraphStyle("ch", fontName=F_HEAD, fontSize=13.5, leading=22,
                           textColor=C_DARK, alignment=TA_CENTER)
    st_abs = ParagraphStyle("ca", fontName=F_BODY, fontSize=10.3, leading=18,
                             alignment=TA_JUSTIFY, firstLineIndent=21,
                             spaceAfter=8)
    st_kw = ParagraphStyle("ck", fontName=F_BODY, fontSize=10.3, leading=18,
                            alignment=TA_JUSTIFY, spaceBefore=4)
    st_th = ParagraphStyle("cth", fontName=F_HEAD, fontSize=9.4, leading=14,
                            textColor=C_DARK)
    st_td = ParagraphStyle("ctd", fontName=F_BODY, fontSize=9.8, leading=14.5,
                            textColor=colors.HexColor("#1a1a1a"))

    for _st in (st_abs, st_kw, st_td):
        _st.wordWrap = "CJK"

    flow = []
    in_abs = False
    for kind, payload in blocks:
        if kind == "h1":
            flow.append(Spacer(1, 42 * mm))
            flow.append(Paragraph(inline(payload), st_title))
            flow.append(Spacer(1, 9 * mm))
        elif kind == "p":
            if in_abs:
                txt = inline(payload)
                if txt.startswith("<b>关键词") or txt.startswith("<b>Key words"):
                    flow.append(Paragraph(txt, st_kw))
                elif txt.startswith("<b>Abstract"):
                    flow.append(Paragraph(txt, st_abs))
                else:
                    flow.append(Paragraph(txt, st_abs))
            else:
                st = st_sub if payload.startswith("**") else st_org
                flow.append(Paragraph(inline(payload), st))
                flow.append(Spacer(1, 3 * mm))
        elif kind == "h2":
            in_abs = True
            flow.append(Spacer(1, 10 * mm))
            flow.append(Paragraph(inline(payload), st_h2))
            flow.append(HRFlowable(width="18%", thickness=1.4, color=C_ACC,
                                    spaceBefore=4, spaceAfter=9, hAlign="CENTER"))
        elif kind == "table":
            head, rows = payload
            data = [[Paragraph(inline(c), st_th) for c in head]]
            for r in rows:
                r = (r + [""] * len(head))[:len(head)]
                data.append([Paragraph(inline(c), st_td) for c in r])
            t = Table(data, colWidths=[30 * mm, content_w - 30 * mm], hAlign="CENTER")
            t.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.4, C_GRID),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf0f6")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            flow.append(Spacer(1, 6 * mm))
            flow.append(t)
            flow.append(Spacer(1, 4 * mm))
    return flow


# ------------------------------------------------------------------ 文档
def _render_once(md_path: str, pdf_path: str, toc_pages=None, chapter_map=None):
    toc_pages = toc_pages or {}
    chapter_map = chapter_map or []
    register_fonts()
    # 公式缓存
    if not os.path.exists(MATH_MANIFEST) or os.path.getmtime(MATH_MANIFEST) < os.path.getmtime(md_path):
        if os.path.exists(GTVENV_PY):
            subprocess.run([GTVENV_PY, os.path.join(ROOT, "tools/_render_math.py"), md_path],
                           check=False, stdout=subprocess.DEVNULL)
    math_manifest = {}
    if os.path.exists(MATH_MANIFEST):
        math_manifest = json.load(open(MATH_MANIFEST, encoding="utf-8"))

    md = open(md_path, encoding="utf-8").read()
    cover_md, body_md = "", md
    cm = re.search(r"<!-- COVER -->(.*?)<!-- /COVER -->", md, re.S)
    if cm:
        cover_md = cm.group(1)
        body_md = md[:cm.start()] + md[cm.end():]
    blocks = parse(body_md)
    cover_blocks = parse(cover_md) if cover_md else []
    blocks = augment_toc(blocks, toc_pages)
    styles = build_styles()

    LM, RM, TM, BM = 20 * mm, 18 * mm, 20 * mm, 16 * mm
    PW, PH = A4
    content_w = PW - LM - RM

    def on_page(canvas, doc):
        if doc.page == 1:            # 封面不排页眉页脚
            return
        canvas.saveState()
        canvas.setFont(F_BODY, 7.6)
        canvas.setFillColor(colors.HexColor("#8a97a5"))
        canvas.drawString(LM, PH - TM + 7 * mm, TITLE)
        chap = chapter_at(doc.page, chapter_map)
        if chap:
            canvas.setFont(F_BODY, 7.6)
            canvas.drawRightString(PW - RM, PH - TM + 7 * mm, chap)
        canvas.setStrokeColor(colors.HexColor("#d6dee6"))
        canvas.setLineWidth(0.4)
        canvas.line(LM, PH - TM + 4.6 * mm, PW - RM, PH - TM + 4.6 * mm)
        canvas.line(LM, BM - 4 * mm, PW - RM, BM - 4 * mm)
        canvas.setFont(F_BODY, 8)
        canvas.drawCentredString(PW / 2, BM - 9 * mm, f"— {doc.page} —")
        canvas.restoreState()

    doc = BaseDocTemplate(pdf_path, pagesize=A4,
                          leftMargin=LM, rightMargin=RM,
                          topMargin=TM, bottomMargin=BM,
                          title=TITLE, author="图论综合应用报告")
    frame = Frame(LM, BM, content_w, PH - TM - BM, id="main",
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="std", frames=[frame], onPage=on_page)])
    flow = []
    if cover_blocks:
        flow += build_cover(cover_blocks, content_w)
        flow.append(PageBreak())
    flow += build_flowables(blocks, styles, math_manifest, content_w,
                            os.path.dirname(os.path.abspath(md_path)))
    doc.build(flow)
    return pdf_path


def make_pdf(md_path: str, pdf_path: str):
    """生成 PDF，并自动把「目录」里的页码回填为真实页码。

    做法：先构建一版（页码列填 '—'）-> 从 PDF 里量出各章所在页 ->
    再构建一版并复核页码是否稳定（最多 4 轮）。
    """
    md = open(md_path, encoding="utf-8").read()
    body_md = md
    cm = re.search(r"<!-- COVER -->(.*?)<!-- /COVER -->", md, re.S)
    if cm:
        body_md = md[:cm.start()] + md[cm.end():]
    chapters = collect_chapters(parse(body_md))

    def _cmap(pages):
        return sorted((pages[k], chapters[k]) for k in pages if k in chapters)

    toc_pages, measured = {}, {}
    for _ in range(4):
        _render_once(md_path, pdf_path, toc_pages, _cmap(toc_pages))
        measured = measure_toc(pdf_path, chapters)
        if measured == toc_pages:
            break
        toc_pages = measured
    else:
        # 最后一轮按量到的页码重建，保证目录与正文一致
        _render_once(md_path, pdf_path, toc_pages, _cmap(toc_pages))
    return pdf_path


if __name__ == "__main__":
    md = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "report/图论综合应用报告-合订版.md")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "report/图论综合应用报告.pdf")
    p = make_pdf(md, out)
    print(f"[pdf] {p}  ({os.path.getsize(p)/1024:.0f} KB)")
