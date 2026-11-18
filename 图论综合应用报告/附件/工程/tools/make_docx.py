# -*- coding: utf-8 -*-
"""
Markdown -> DOCX（python-docx）。

运行（需要带 python-docx 的解释器）：
    /Users/yoyo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
        tools/make_docx.py [input.md] [output.docx]

与 tools/make_pdf.py 共用同一份 Markdown 源、同一套块级解析，版式规则保持一致：
  * 全文黑色，不使用蓝色字体；表头改用浅灰底纹代替深蓝底纹
  * 不输出英文摘要与英文关键词
  * 目录页码用「渲染成 PDF -> 量页码 -> 回填」两遍构建自动生成
"""
from __future__ import annotations

import copy
import json
import os
import re
import subprocess
import sys

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Mm, Pt, RGBColor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_pdf import (parse, latex_to_text, collect_chapters, h1_key,  # noqa: E402
                      toc_key, _norm)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATH_MANIFEST = os.path.join(ROOT, "tools/_math/manifest.json")

TITLE = "基于图论的重庆大学虎溪校区快递配送路径优化研究"

# ---- 颜色：全黑（需求：不要蓝色字体） -------------------------------------
BLACK = RGBColor(0x00, 0x00, 0x00)
GRAY = RGBColor(0x59, 0x59, 0x59)
FILL_HEAD = "EDEDED"     # 表头底纹
FILL_LIGHT = "F7F7F7"    # 代码块 / 引文底纹
LINE_INNER = "9A9A9A"

# ---- 字体 ------------------------------------------------------------------
F_CJK = "宋体"           # 正文中文
F_HEAD = "黑体"          # 标题中文
F_LAT = "Times New Roman"
F_MONO = "Menlo"

CONTENT_W_CM = 17.2
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"

SOFFICE = ("/Users/yoyo/.cache/codex-runtimes/codex-primary-runtime/"
           "dependencies/bin/override/soffice")


# =============================================================================
# 低层 OOXML 工具
# =============================================================================
def _ins(parent, el, *successors):
    """按 OOXML schema 顺序插入子元素。"""
    parent.insert_element_before(el, *successors)
    return el


def rfonts(el, cjk=F_CJK, latin=F_LAT):
    rPr = el.get_or_add_rPr()
    rf = rPr.get_or_add_rFonts()
    rf.set(qn("w:ascii"), latin)
    rf.set(qn("w:hAnsi"), latin)
    rf.set(qn("w:eastAsia"), cjk)
    rf.set(qn("w:cs"), latin)


def style_run(run, size, bold=False, italic=False, color=BLACK,
              cjk=F_CJK, latin=F_LAT):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = latin
    rfonts(run._r, cjk, latin)
    return run


def p_border(par, edges):
    """edges: [('bottom', sz_eighths, color_hex, space_pt), ...]"""
    pPr = par._p.get_or_add_pPr()
    pbdr = pPr.find(qn("w:pBdr"))
    if pbdr is None:
        pbdr = _ins(pPr, OxmlElement("w:pBdr"),
                    "w:shd", "w:tabs", "w:suppressAutoHyphens", "w:kinsoku",
                    "w:wordWrap", "w:overflowPunct", "w:topLinePunct",
                    "w:autoSpaceDE", "w:autoSpaceDN", "w:bidi",
                    "w:adjustRightInd", "w:snapToGrid", "w:spacing", "w:ind",
                    "w:contextualSpacing", "w:mirrorIndents", "w:suppressOverlap",
                    "w:jc", "w:textDirection", "w:textAlignment",
                    "w:textboxTightWrap", "w:outlineLvl", "w:divId",
                    "w:cnfStyle", "w:rPr", "w:sectPr", "w:pPrChange")
    for name, sz, color, space in edges:
        e = OxmlElement("w:" + name)
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), str(sz))
        e.set(qn("w:space"), str(space))
        e.set(qn("w:color"), color)
        pbdr.append(e)


def cell_shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    _ins(tcPr, shd, "w:noWrap", "w:tcMar", "w:textDirection",
         "w:tcFitText", "w:vAlign", "w:hideMark")


def cell_borders(cell, edges):
    tcPr = cell._tc.get_or_add_tcPr()
    b = tcPr.find(qn("w:tcBorders"))
    if b is None:
        b = _ins(tcPr, OxmlElement("w:tcBorders"), "w:shd", "w:noWrap",
                 "w:tcMar", "w:textDirection", "w:tcFitText", "w:vAlign",
                 "w:hideMark")
    for name, sz, color in edges:
        e = OxmlElement("w:" + name)
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), str(sz))
        e.set(qn("w:space"), "0")
        e.set(qn("w:color"), color)
        b.append(e)


def table_borders(table, outer_sz=6, inner_sz=4):
    tblPr = table._tbl.tblPr
    b = _ins(tblPr, OxmlElement("w:tblBorders"), "w:shd", "w:tblLayout",
             "w:tblCellMar", "w:tblLook", "w:tblCaption", "w:tblDescription")
    for name in ("top", "left", "bottom", "right"):
        e = OxmlElement("w:" + name)
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), str(outer_sz))
        e.set(qn("w:space"), "0")
        e.set(qn("w:color"), "000000")
        b.append(e)
    for name in ("insideH", "insideV"):
        e = OxmlElement("w:" + name)
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), str(inner_sz))
        e.set(qn("w:space"), "0")
        e.set(qn("w:color"), LINE_INNER)
        b.append(e)


def table_fixed_layout(table):
    """固定列宽布局。python-docx 建表时已带 tblLayout，不要重复插入
    （w:tblLayout 在 schema 中只允许出现一次）。"""
    tblPr = table._tbl.tblPr
    lay = tblPr.find(qn("w:tblLayout"))
    if lay is None:
        lay = OxmlElement("w:tblLayout")
        _ins(tblPr, lay, "w:tblCellMar", "w:tblLook", "w:tblCaption",
             "w:tblDescription")
    lay.set(qn("w:type"), "fixed")


def table_cell_margins(table, top=3.5, left=5, bottom=3.5, right=5):
    tblPr = table._tbl.tblPr
    mar = _ins(tblPr, OxmlElement("w:tblCellMar"), "w:tblLook",
               "w:tblCaption", "w:tblDescription")
    for name, val in (("top", top), ("left", left), ("bottom", bottom),
                      ("right", right)):
        e = OxmlElement("w:" + name)
        e.set(qn("w:w"), str(int(val * 20)))
        e.set(qn("w:type"), "dxa")
        mar.append(e)


def repeat_header(row):
    trPr = row._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    th.set(qn("w:val"), "true")
    trPr.append(th)


def add_field(par, instr, cached="1", size=9, color=GRAY, cjk=F_CJK,
              latin=F_LAT):
    """插入一个 Word 域（PAGE / NUMPAGES 等）。"""
    runs = []

    def _fc(kind):
        r = par.add_run()
        e = OxmlElement("w:fldChar")
        e.set(qn("w:fldCharType"), kind)
        r._r.append(e)
        runs.append(r)

    _fc("begin")
    r = par.add_run()
    it = OxmlElement("w:instrText")
    it.set(XML_SPACE, "preserve")
    it.text = instr
    r._r.append(it)
    runs.append(r)
    _fc("separate")
    runs.append(par.add_run(cached))
    _fc("end")
    for rr in runs:
        style_run(rr, size, color=color, cjk=cjk, latin=latin)
    return runs


# =============================================================================
# 行内 Markdown -> runs
# =============================================================================
TOKEN = re.compile(
    r"`([^`]+)`"          # 1 行内代码
    r"|\$([^$\n]+?)\$"    # 2 行内公式
    r"|\*\*(.+?)\*\*"     # 3 粗体
    r"|(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)"  # 4 斜体
    , re.S)


def inline_runs(text, flags=""):
    """-> [(text, flags)]；flags 含 b/i/c/m。"""
    out, pos = [], 0
    for m in TOKEN.finditer(text):
        if m.start() > pos:
            out.append((text[pos:m.start()], flags))
        if m.group(1) is not None:
            out.append((m.group(1), flags + "c"))
        elif m.group(2) is not None:
            out.append((latex_to_text(m.group(2)), flags + "m"))
        elif m.group(3) is not None:
            out.extend(inline_runs(m.group(3), flags + "b"))
        else:
            out.extend(inline_runs(m.group(4), flags + "i"))
        pos = m.end()
    if pos < len(text):
        out.append((text[pos:], flags))
    return out


def add_inline(par, text, size, base_flags="", color=BLACK, cjk=F_CJK,
               latin=F_LAT, bold_size=None):
    """把行内 Markdown 写进段落，返回是否含特殊格式。"""
    for t, fl in inline_runs(text, base_flags):
        if not t:
            continue
        r = par.add_run(t)
        mono = "c" in fl
        style_run(
            r,
            size if not mono else max(size - 1.0, 6.5),
            bold=("b" in fl),
            italic=("i" in fl) and not mono,
            color=color,
            cjk=F_CJK if not mono else F_CJK,
            latin=F_MONO if mono else latin,
        )
    return par


# =============================================================================
# 样式
# =============================================================================
def _style(doc, name, base="Normal"):
    from docx.enum.style import WD_STYLE_TYPE
    try:
        st = doc.styles[name]
    except KeyError:
        st = doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        st.base_style = doc.styles[base]
    return st


def make_styles(doc):
    # ---- Normal ----
    normal = doc.styles["Normal"]
    normal.font.size = Pt(10.2)
    normal.font.color.rgb = BLACK
    normal.font.name = F_LAT
    rfonts(normal.element, F_CJK, F_LAT)
    pf = normal.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf.line_spacing = Pt(17.5)
    pf.space_after = Pt(7)
    pf.space_before = Pt(0)

    # ---- 正文（首行不缩进，与 PDF 版一致） ----
    body = _style(doc, "正文")
    body.font.size = Pt(10.2)
    body.font.color.rgb = BLACK
    body.font.name = F_LAT
    rfonts(body.element, F_CJK, F_LAT)
    bpf = body.paragraph_format
    bpf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    bpf.line_spacing = Pt(17.5)
    bpf.space_after = Pt(7)
    bpf.space_before = Pt(0)

    # ---- 标题 1/2/3：内置样式默认是蓝色 accent1，必须覆盖 ----
    h1 = doc.styles["Heading 1"]
    h1.font.size = Pt(17)
    h1.font.bold = False
    h1.font.color.rgb = BLACK
    h1.font.name = F_LAT
    rfonts(h1.element, F_HEAD, F_LAT)
    h1pf = h1.paragraph_format
    h1pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    h1pf.space_before = Pt(6)
    h1pf.space_after = Pt(12)
    h1pf.line_spacing = Pt(24)
    h1pf.keep_with_next = True
    h1pf.first_line_indent = Pt(0)

    h2 = doc.styles["Heading 2"]
    h2.font.size = Pt(13)
    h2.font.bold = False
    h2.font.color.rgb = BLACK
    h2.font.name = F_LAT
    rfonts(h2.element, F_HEAD, F_LAT)
    h2pf = h2.paragraph_format
    h2pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    h2pf.space_before = Pt(15)
    h2pf.space_after = Pt(8)
    h2pf.line_spacing = Pt(19)
    h2pf.keep_with_next = True
    h2pf.left_indent = Pt(6)
    h2pf.first_line_indent = Pt(0)

    h3 = doc.styles["Heading 3"]
    h3.font.size = Pt(11.5)
    h3.font.bold = False
    h3.font.color.rgb = BLACK
    h3.font.name = F_LAT
    rfonts(h3.element, F_HEAD, F_LAT)
    h3pf = h3.paragraph_format
    h3pf.space_before = Pt(11)
    h3pf.space_after = Pt(6)
    h3pf.line_spacing = Pt(17)
    h3pf.keep_with_next = True
    h3pf.first_line_indent = Pt(0)

    h4 = doc.styles["Heading 4"]
    h4.font.size = Pt(10.5)
    h4.font.bold = False
    h4.font.color.rgb = BLACK
    h4.font.name = F_LAT
    rfonts(h4.element, F_HEAD, F_LAT)
    h4pf = h4.paragraph_format
    h4pf.space_before = Pt(9)
    h4pf.space_after = Pt(5)
    h4pf.line_spacing = Pt(16)
    h4pf.keep_with_next = True
    h4pf.first_line_indent = Pt(0)

    # ---- 参考文献条目（悬挂缩进，左对齐，避免西文两端对齐拉出大空隙） ----
    ref = _style(doc, "文献条目")
    ref.font.size = Pt(10.2)
    ref.font.color.rgb = BLACK
    ref.font.name = F_LAT
    rfonts(ref.element, F_CJK, F_LAT)
    rpf = ref.paragraph_format
    rpf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    rpf.line_spacing = Pt(17.5)
    rpf.space_after = Pt(7)
    rpf.left_indent = Cm(0.95)
    rpf.first_line_indent = Cm(-0.95)

    # ---- 题注 ----
    cap = _style(doc, "题注")
    cap.font.size = Pt(9.4)
    cap.font.color.rgb = BLACK
    cap.font.name = F_LAT
    rfonts(cap.element, F_HEAD, F_LAT)
    cpf = cap.paragraph_format
    cpf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cpf.line_spacing = Pt(14)
    cpf.space_before = Pt(9)
    cpf.space_after = Pt(4)
    cpf.first_line_indent = Pt(0)

    # ---- 表内文字 / 表头 ----
    tc = _style(doc, "表内文字")
    tc.font.size = Pt(8.4)
    tc.font.color.rgb = BLACK
    tc.font.name = F_LAT
    rfonts(tc.element, F_CJK, F_LAT)
    tcpf = tc.paragraph_format
    tcpf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    tcpf.line_spacing = Pt(11.8)
    tcpf.space_before = Pt(0)
    tcpf.space_after = Pt(0)
    tcpf.first_line_indent = Pt(0)

    th = _style(doc, "表头")
    th.font.size = Pt(8.6)
    th.font.color.rgb = BLACK
    th.font.name = F_LAT
    rfonts(th.element, F_HEAD, F_LAT)
    thpf = th.paragraph_format
    thpf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    thpf.line_spacing = Pt(12)
    thpf.space_before = Pt(0)
    thpf.space_after = Pt(0)
    thpf.first_line_indent = Pt(0)

    # ---- 项目符号 ----
    li = _style(doc, "项目符号")
    li.font.size = Pt(10.2)
    li.font.color.rgb = BLACK
    li.font.name = F_LAT
    rfonts(li.element, F_CJK, F_LAT)
    lipf = li.paragraph_format
    lipf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    lipf.line_spacing = Pt(17)
    lipf.space_after = Pt(3.5)
    lipf.left_indent = Pt(21)
    lipf.first_line_indent = Pt(-21)

    # ---- 代码 ----
    code = _style(doc, "代码")
    code.font.size = Pt(7.8)
    code.font.color.rgb = BLACK
    code.font.name = F_MONO
    rfonts(code.element, F_CJK, F_MONO)
    cpf2 = code.paragraph_format
    cpf2.alignment = WD_ALIGN_PARAGRAPH.LEFT
    cpf2.line_spacing = Pt(10.8)
    cpf2.space_before = Pt(0)
    cpf2.space_after = Pt(0)
    cpf2.first_line_indent = Pt(0)
    cpf2.left_indent = Pt(0)

    # ---- 引文 ----
    quote = _style(doc, "引文")
    quote.font.size = Pt(9.8)
    quote.font.color.rgb = BLACK
    quote.font.name = F_LAT
    rfonts(quote.element, F_CJK, F_LAT)
    qpf = quote.paragraph_format
    qpf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    qpf.line_spacing = Pt(16)
    qpf.space_before = Pt(0)
    qpf.space_after = Pt(2)
    qpf.first_line_indent = Pt(0)

    # ---- 封面摘要 / 关键词 ----
    ca = _style(doc, "封面摘要")
    ca.font.size = Pt(10.3)
    ca.font.color.rgb = BLACK
    ca.font.name = F_LAT
    rfonts(ca.element, F_CJK, F_LAT)
    cap2 = ca.paragraph_format
    cap2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    cap2.line_spacing = Pt(18)
    cap2.space_before = Pt(0)
    cap2.space_after = Pt(8)
    cap2.first_line_indent = Pt(0)

    ck = _style(doc, "封面关键词")
    ck.font.size = Pt(10.3)
    ck.font.color.rgb = BLACK
    ck.font.name = F_LAT
    rfonts(ck.element, F_CJK, F_LAT)
    ckp = ck.paragraph_format
    ckp.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    ckp.line_spacing = Pt(18)
    ckp.space_before = Pt(4)
    ckp.space_after = Pt(0)
    ckp.first_line_indent = Pt(0)

    # ---- 封面 ----
    ct = _style(doc, "封面标题")
    ct.font.size = Pt(21)
    ct.font.color.rgb = BLACK
    ct.font.name = F_LAT
    rfonts(ct.element, F_HEAD, F_LAT)
    ctp = ct.paragraph_format
    ctp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    ctp.line_spacing = Pt(30)
    ctp.space_before = Pt(0)
    ctp.space_after = Pt(12)
    ctp.first_line_indent = Pt(0)

    cs = _style(doc, "封面副题")
    cs.font.size = Pt(13)
    cs.font.color.rgb = BLACK
    cs.font.name = F_LAT
    rfonts(cs.element, F_HEAD, F_LAT)
    csp = cs.paragraph_format
    csp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    csp.line_spacing = Pt(22)
    csp.space_after = Pt(4)
    csp.first_line_indent = Pt(0)

    co = _style(doc, "封面单位")
    co.font.size = Pt(11.5)
    co.font.color.rgb = BLACK
    co.font.name = F_LAT
    rfonts(co.element, F_CJK, F_LAT)
    cop = co.paragraph_format
    cop.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cop.line_spacing = Pt(20)
    cop.space_after = Pt(6)
    cop.first_line_indent = Pt(0)


# =============================================================================
# 分节
# =============================================================================
def break_section(doc, last_par):
    """在 last_par 之后开新节（nextPage），不产生多余空段落。"""
    doc.add_section(WD_SECTION.NEW_PAGE)
    body = doc.element.body
    holder = None
    for p in body.findall(qn("w:p")):
        pPr = p.find(qn("w:pPr"))
        if pPr is not None and pPr.find(qn("w:sectPr")) is not None:
            holder = p
    if holder is None:
        return
    sectPr = holder.find(qn("w:pPr")).find(qn("w:sectPr"))
    pPr = last_par._p.get_or_add_pPr()
    pPr.append(sectPr)                       # sectPr 放到 pPr 末尾
    holder.getparent().remove(holder)


def setup_section(sec, header_right=None, footer=True, blank=False):
    sec.page_width = Mm(210)
    sec.page_height = Mm(297)
    sec.left_margin = Mm(20)
    sec.right_margin = Mm(18)
    sec.top_margin = Mm(20)
    sec.bottom_margin = Mm(16)
    sec.header_distance = Mm(10)
    sec.footer_distance = Mm(9)

    hdr = sec.header
    hdr.is_linked_to_previous = False
    par = hdr.paragraphs[0]
    if blank:
        for r in list(par.runs):
            r._r.getparent().remove(r._r)
        par.paragraph_format.space_after = Pt(0)
        f0 = sec.footer
        f0.is_linked_to_previous = False
        for r in list(f0.paragraphs[0].runs):
            r._r.getparent().remove(r._r)
        return
    for r in list(par.runs):
        r._r.getparent().remove(r._r)
    par.text = ""
    par.alignment = WD_ALIGN_PARAGRAPH.LEFT
    par.paragraph_format.space_after = Pt(2)
    par.paragraph_format.line_spacing = Pt(11)
    par.paragraph_format.tab_stops.add_tab_stop(
        Cm(CONTENT_W_CM), WD_TAB_ALIGNMENT.RIGHT)
    style_run(par.add_run(TITLE), 8.4, color=GRAY)
    if header_right:
        style_run(par.add_run("\t" + header_right), 8.4, color=GRAY)
    p_border(par, [("bottom", 4, "BFBFBF", 2)])

    ftr = sec.footer
    if not footer:
        ftr.is_linked_to_previous = False
        for r in list(ftr.paragraphs[0].runs):
            r._r.getparent().remove(r._r)
        return
    ftr.is_linked_to_previous = False
    fp = ftr.paragraphs[0]
    for r in list(fp.runs):
        r._r.getparent().remove(r._r)
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fp.paragraph_format.space_before = Pt(2)
    fp.paragraph_format.line_spacing = Pt(11)
    p_border(fp, [("top", 4, "BFBFBF", 4)])
    style_run(fp.add_run("— "), 8.4, color=GRAY)
    add_field(fp, " PAGE ", "1", size=8.4)
    style_run(fp.add_run(" —"), 8.4, color=GRAY)


# =============================================================================
# 内容构建
# =============================================================================
def set_table_width(table, widths_cm):
    """固定列宽：必须同时写 tblW、tblGrid 与每个单元格的 tcW，
    否则 Word/LibreOffice 仍按默认等分网格排版（表现为列宽不均、整表右移）。"""
    twips = [int(round(w * 567)) for w in widths_cm]      # 1 cm = 567 twips
    tbl = table._tbl
    tblPr = tbl.tblPr

    tblW = tblPr.find(qn("w:tblW"))
    if tblW is None:
        tblW = OxmlElement("w:tblW")
        tblPr.insert_element_before(
            tblW, "w:jc", "w:tblCellSpacing", "w:tblInd", "w:tblBorders",
            "w:shd", "w:tblLayout", "w:tblCellMar", "w:tblLook",
            "w:tblCaption", "w:tblDescription")
    tblW.set(qn("w:w"), str(sum(twips)))
    tblW.set(qn("w:type"), "dxa")

    old = tbl.find(qn("w:tblGrid"))
    if old is not None:
        tbl.remove(old)
    grid = OxmlElement("w:tblGrid")
    for t in twips:
        gc = OxmlElement("w:gridCol")
        gc.set(qn("w:w"), str(t))
        grid.append(gc)
    tblPr.addnext(grid)

    for row in table.rows:
        for i, cell in enumerate(row.cells):
            if i < len(widths_cm):
                cell.width = Cm(widths_cm[i])
    return table


def add_caption(doc, which, num, title):
    par = doc.add_paragraph(style="题注")
    if which == "图":
        par.paragraph_format.space_before = Pt(5)
        par.paragraph_format.space_after = Pt(11)
    else:
        par.paragraph_format.space_before = Pt(9)
        par.paragraph_format.space_after = Pt(4)
    style_run(par.add_run("%s %s　%s" % (which, num, title)), 9.4,
              cjk=F_HEAD, latin=F_LAT)
    return par


def add_table(doc, head, rows):
    ncol = len(head)
    data = [head] + [list(r) + [""] * (ncol - len(r)) for r in rows]
    table = doc.add_table(rows=len(data), cols=ncol)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table_fixed_layout(table)
    table_borders(table)
    table_cell_margins(table)

    weights = []
    for c in range(ncol):
        mx = len(head[c])
        for r in rows[:60]:
            if c < len(r):
                mx = max(mx, min(len(r[c]), 60))
        weights.append(max(4, mx))
    tot = sum(weights)
    widths = [CONTENT_W_CM * w / tot for w in weights]

    set_table_width(table, widths)
    for ri, rowdata in enumerate(data):
        row = table.rows[ri]
        for ci in range(ncol):
            cell = row.cells[ci]
            par = cell.paragraphs[0]
            par.style = doc.styles["表头" if ri == 0 else "表内文字"]
            txt = rowdata[ci] if ci < len(rowdata) else ""
            add_inline(par, txt, 8.6 if ri == 0 else 8.4,
                       cjk=F_HEAD if ri == 0 else F_CJK)
            if ri == 0:
                cell_shade(cell, FILL_HEAD)
        if ri == 0:
            repeat_header(row)
    # 空行间隔
    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(0)
    sp.paragraph_format.line_spacing = Pt(6)
    style_run(sp.add_run(""), 6)
    return table


def add_code_block(doc, payload):
    lines = payload.split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        return None
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table_fixed_layout(table)
    table_cell_margins(table, top=6, left=8, bottom=6, right=6)
    set_table_width(table, [CONTENT_W_CM - 0.3])
    cell = table.rows[0].cells[0]
    cell_shade(cell, FILL_LIGHT)
    cell_borders(cell, [("left", 24, "000000")])
    for i, ln in enumerate(lines):
        par = cell.paragraphs[0] if i == 0 else cell.add_paragraph()
        par.style = doc.styles["代码"]
        if ln.strip():
            style_run(par.add_run(ln), 7.8, cjk=F_CJK, latin=F_MONO)
    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(0)
    sp.paragraph_format.line_spacing = Pt(6)
    style_run(sp.add_run(""), 6)
    return table


def add_quote(doc, payload):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table_fixed_layout(table)
    table_cell_margins(table, top=7, left=10, bottom=7, right=9)
    set_table_width(table, [CONTENT_W_CM - 0.3])
    cell = table.rows[0].cells[0]
    cell_shade(cell, FILL_LIGHT)
    cell_borders(cell, [("left", 24, "000000")])
    lines = [l.strip() for l in payload.split("\n") if l.strip()]
    for i, ln in enumerate(lines):
        par = cell.paragraphs[0] if i == 0 else cell.add_paragraph()
        par.style = doc.styles["引文"]
        if re.match(r"^([-*+]|\d+[.)])\s+", ln):
            ln = re.sub(r"^([-*+]|\d+[.)])\s+", "• ", ln)
        add_inline(par, ln, 9.8)
    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(0)
    sp.paragraph_format.line_spacing = Pt(6)
    style_run(sp.add_run(""), 6)
    return table


def add_hr(doc):
    par = doc.add_paragraph()
    par.paragraph_format.space_before = Pt(4)
    par.paragraph_format.space_after = Pt(8)
    par.paragraph_format.line_spacing = Pt(1)
    p_border(par, [("bottom", 4, "C8C8C8", 1)])
    return par


def add_picture(doc, src, base_dir):
    p = src if os.path.isabs(src) else os.path.join(base_dir, src)
    if not os.path.exists(p):
        p2 = os.path.join(ROOT, src.lstrip("./"))
        p = p2 if os.path.exists(p2) else p
    if not os.path.exists(p):
        return None
    from PIL import Image as PILImage
    iw, ih = PILImage.open(p).size
    w_cm = CONTENT_W_CM
    h_cm = w_cm * ih / iw
    if h_cm > 21.5:
        h_cm = 21.5
        w_cm = h_cm * iw / ih
    par = doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.paragraph_format.line_spacing = 1.0          # 单倍行距：图片不被裁
    par.paragraph_format.space_before = Pt(6)
    par.paragraph_format.space_after = Pt(3)
    par.paragraph_format.first_line_indent = Pt(0)
    par.add_run().add_picture(p, width=Cm(w_cm))
    return par


def add_math(doc, payload, manifest):
    import hashlib
    key = hashlib.sha1(payload.strip().encode("utf-8")).hexdigest()[:16]
    entry = manifest.get(key)
    if entry:
        p = os.path.join(ROOT, entry["png"])
        if os.path.exists(p):
            from PIL import Image as PILImage
            iw, ih = PILImage.open(p).size
            # 渲染时是 400 dpi / 13 pt，按原始尺寸放回即为 13 pt 的观感
            w_cm = min(CONTENT_W_CM, iw / 400.0 * 2.54)
            h_cm = w_cm * ih / iw
            par = doc.add_paragraph()
            par.alignment = WD_ALIGN_PARAGRAPH.CENTER
            par.paragraph_format.line_spacing = 1.0  # 单倍行距：公式不被裁
            par.paragraph_format.space_before = Pt(4)
            par.paragraph_format.space_after = Pt(9)
            par.paragraph_format.first_line_indent = Pt(0)
            par.add_run().add_picture(p, width=Cm(w_cm))
            return par
    par = doc.add_paragraph(style="正文")
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_inline(par, latex_to_text(payload), 10.2)
    return par


# =============================================================================
# 封面
# =============================================================================
def build_cover(doc, cover_blocks):
    """封面：题目 + 课程信息表 + 中文摘要 + 关键词（不含英文摘要）。"""
    last = None
    skip_en = False
    in_abs = False
    for kind, payload in cover_blocks:
        if kind == "h1":
            sp = doc.add_paragraph(style="封面标题")
            sp.paragraph_format.space_before = Pt(42)
            add_inline(sp, payload, 21, cjk=F_HEAD)
            last = sp
        elif kind == "p":
            if skip_en:
                continue
            if in_abs:
                # 摘要正文 / 关键词：两端对齐
                if payload.startswith("**关键词") or payload.startswith("**Key words"):
                    sp = doc.add_paragraph(style="封面关键词")
                else:
                    sp = doc.add_paragraph(style="封面摘要")
                add_inline(sp, payload, 10.3)
            elif payload.startswith("**"):
                sp = doc.add_paragraph(style="封面副题")
                add_inline(sp, payload, 13, cjk=F_HEAD)
            else:
                sp = doc.add_paragraph(style="封面单位")
                add_inline(sp, payload, 11.5)
            last = sp
        elif kind == "h2":
            if _norm(payload).lower() == "abstract":
                skip_en = True
                continue
            in_abs = True
            sp = doc.add_paragraph(style="封面副题")
            sp.paragraph_format.space_before = Pt(14)
            sp.paragraph_format.space_after = Pt(8)
            add_inline(sp, payload, 13.5, cjk=F_HEAD)
            sp.paragraph_format.left_indent = Cm(5)
            sp.paragraph_format.right_indent = Cm(5)
            p_border(sp, [("bottom", 6, "000000", 6)])
            last = sp
        elif kind == "table":
            head, rows = payload
            data = [head] + [list(r) + [""] * (len(head) - len(r)) for r in rows]
            ncol = len(head)
            table = doc.add_table(rows=len(data), cols=ncol)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            table.autofit = False
            table_fixed_layout(table)
            table_borders(table)
            table_cell_margins(table, top=5, left=7, bottom=5, right=7)
            set_table_width(table, [3.6, CONTENT_W_CM - 3.6])
            for ri, rowdata in enumerate(data):
                for ci in range(ncol):
                    cell = table.rows[ri].cells[ci]
                    par = cell.paragraphs[0]
                    par.style = doc.styles["表头" if ri == 0 else "表内文字"]
                    par.paragraph_format.alignment = (
                        WD_ALIGN_PARAGRAPH.CENTER if ri == 0
                        else WD_ALIGN_PARAGRAPH.LEFT)
                    txt = rowdata[ci] if ci < len(rowdata) else ""
                    add_inline(par, txt, 9.4 if ri == 0 else 9.8,
                               cjk=F_HEAD if ri == 0 else F_CJK)
                    if ri == 0:
                        cell_shade(cell, FILL_HEAD)
            sp = doc.add_paragraph()
            sp.paragraph_format.space_after = Pt(0)
            sp.paragraph_format.line_spacing = Pt(6)
            style_run(sp.add_run(""), 6)
            last = sp
    # 摘要正文（cover_blocks 里的摘要段落已在上面处理）
    return last


# =============================================================================
# 正文
# =============================================================================
def build_body(doc, blocks, manifest, base_dir, chapter_titles):
    """构建正文；返回 (最后一段, 分节标题列表)。"""
    last = None
    sections = []           # 与 doc.sections 一一对应的页眉右侧文字
    cur_title = None
    first_h1 = True

    for kind, payload in blocks:
        if kind == "h1":
            if not first_h1:
                break_section(doc, last)
                sections.append(cur_title)
            cur_title = payload
            first_h1 = False
            par = doc.add_paragraph(style="Heading 1")
            add_inline(par, payload, 17, cjk=F_HEAD)
            p_border(par, [("bottom", 10, "000000", 6)])
            last = par
        elif kind in ("h2", "h3", "h4"):
            lvl = int(kind[1])
            par = doc.add_paragraph(style="Heading %d" % lvl)
            add_inline(par, payload, {2: 13, 3: 11.5, 4: 10.5}[lvl],
                       cjk=F_HEAD)
            last = par
        elif kind == "p":
            if re.match(r"^\[\d+\]\s", payload):
                par = doc.add_paragraph(style="文献条目")
            else:
                par = doc.add_paragraph(style="正文")
            add_inline(par, payload, 10.2)
            last = par
        elif kind == "ul":
            for it in payload:
                par = doc.add_paragraph(style="项目符号")
                par.paragraph_format.tab_stops.add_tab_stop(Pt(21))
                style_run(par.add_run("•"), 10.2)
                style_run(par.add_run("\t"), 10.2)
                add_inline(par, it, 10.2)
                last = par
        elif kind == "cap":
            which, num, title = payload
            par = add_caption(doc, which, num, title)
            last = par
        elif kind == "hr":
            par = add_hr(doc)
            last = par
        elif kind == "quote":
            t = add_quote(doc, payload)
            last = doc.paragraphs[-1]
        elif kind == "code":
            t = add_code_block(doc, payload)
            last = doc.paragraphs[-1]
        elif kind == "table":
            head, rows = payload
            add_table(doc, head, rows)
            last = doc.paragraphs[-1]
        elif kind == "img":
            alt, src = payload
            p = add_picture(doc, src, base_dir)
            if p is not None:
                last = p
        elif kind == "math":
            p = add_math(doc, payload, manifest)
            if p is not None:
                last = p
    return last, sections, cur_title


# =============================================================================
# 目录页码：渲染 -> 量页码 -> 回填
# =============================================================================
def augment_toc(blocks, toc_pages):
    """给「目录」表追加「页码」列。"""
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


def _first_body_line(text):
    """跳过页眉（含报告题目）与页脚，取第一行正文。"""
    for ln in (text or "").split("\n"):
        s = ln.strip()
        if not s:
            continue
        if TITLE in s:
            continue
        if re.match(r"^[—–\-]?\s*\d+\s*[—–\-]?$", s):
            continue
        return s
    return ""


def measure_toc(pdf_path, chapters):
    from pypdf import PdfReader
    try:
        pages = [(pg.extract_text() or "") for pg in PdfReader(pdf_path).pages]
    except Exception:
        return {}
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


def render_pdf(docx_path, out_dir):
    """用无头 LibreOffice 把 docx 渲染成 PDF（用于量页码 + 视觉质检）。"""
    subprocess.run([SOFFICE, "--headless", "--convert-to", "pdf",
                    "--outdir", out_dir, docx_path],
                   check=False, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)
    pdf = os.path.join(out_dir,
                       os.path.splitext(os.path.basename(docx_path))[0] + ".pdf")
    return pdf if os.path.exists(pdf) else None


# =============================================================================
# 主流程
# =============================================================================
def _render_once(md_path, out_path, toc_pages=None):
    toc_pages = toc_pages or {}
    manifest = {}
    if os.path.exists(MATH_MANIFEST):
        manifest = json.load(open(MATH_MANIFEST, encoding="utf-8"))

    md = open(md_path, encoding="utf-8").read()
    cover_md, body_md = "", md
    cm = re.search(r"<!-- COVER -->(.*?)<!-- /COVER -->", md, re.S)
    if cm:
        cover_md = cm.group(1)
        body_md = md[:cm.start()] + md[cm.end():]
    blocks = augment_toc(parse(body_md), toc_pages)
    cover_blocks = parse(cover_md) if cover_md else []

    doc = Document()
    make_styles(doc)

    # --- 封面（独立分节，无页眉页脚） ---
    last_cover = build_cover(doc, cover_blocks)
    if last_cover is None:
        last_cover = doc.add_paragraph()
    break_section(doc, last_cover)

    # --- 目录之前的说明文字（生成时间等），属于「目录」节 ---
    body_blocks = list(blocks)
    first_h1_idx = None
    for i, (k, p) in enumerate(body_blocks):
        if k == "h1":
            first_h1_idx = i
            break
    pre = body_blocks[:first_h1_idx] if first_h1_idx else []
    rest = body_blocks[first_h1_idx:] if first_h1_idx else body_blocks
    for kind, payload in pre:
        if kind == "quote":
            add_quote(doc, payload)
        elif kind == "p":
            par = doc.add_paragraph(style="正文")
            add_inline(par, payload, 10.2)
        elif kind == "hr":
            add_hr(doc)

    # --- 正文 ---
    last_body, sections, last_title = build_body(
        doc, rest, manifest, os.path.dirname(os.path.abspath(md_path)), None)

    # --- 页眉 / 页脚：封面节无，其余每节一个章节名 ---
    hdr_names = [""] + sections + [last_title]
    for i, sec in enumerate(doc.sections):
        name = hdr_names[i] if i < len(hdr_names) else ""
        setup_section(sec, header_right=name, footer=(i > 0), blank=(i == 0))

    doc.core_properties.title = TITLE
    doc.core_properties.author = ""
    doc.save(out_path)
    scrub_blue_styles(out_path)
    return out_path


BLUEISH = {"17365D", "1F497D", "243F60", "31849B", "348DA5", "365F91",
           "4F81BD", "5F497A", "664E82", "76923C", "7E9C40", "943634",
           "9E3A38", "C0504D", "E36C0A", "F2730A", "2F5496", "1F3864"}


def scrub_blue_styles(docx_path):
    """把 styles.xml 里内置但未使用的蓝系样式统一改成黑色。

    这些样式（Heading5-9 / Title / Subtitle / Caption / 各类强调表格样式）
    本报告一个都没用，但留着蓝色定义，读者一旦套用就会冒出蓝色字。
    直接抹掉，避免误解。"""
    import shutil
    import tempfile
    import zipfile
    from lxml import etree

    tmp = tempfile.mkdtemp(prefix="docx_scrub_")
    try:
        with zipfile.ZipFile(docx_path, "r") as z:
            z.extractall(tmp)
        changed = 0
        for name in ("word/styles.xml", "word/stylesWithEffects.xml"):
            path = os.path.join(tmp, name)
            if not os.path.exists(path):
                continue
            tree = etree.parse(path)
            for el in tree.iter(qn("w:color")):
                v = (el.get(qn("w:val")) or "").upper()
                if v in BLUEISH:
                    el.set(qn("w:val"), "000000")
                    changed += 1
            tree.write(path, xml_declaration=True, encoding="UTF-8",
                       standalone=True)
        out = docx_path + ".tmp"
        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for root, _, files in os.walk(tmp):
                for f in files:
                    full = os.path.join(root, f)
                    z.write(full, os.path.relpath(full, tmp))
        shutil.move(out, docx_path)
        return changed
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def make_docx(md_path, out_path):
    """两遍构建：先量页码，再回填目录页码。"""
    md = open(md_path, encoding="utf-8").read()
    body_md = md
    cm = re.search(r"<!-- COVER -->(.*?)<!-- /COVER -->", md, re.S)
    if cm:
        body_md = md[:cm.start()] + md[cm.end():]
    chapters = collect_chapters(parse(body_md))

    tmp_dir = "/tmp/gt_docx_render"
    os.makedirs(tmp_dir, exist_ok=True)
    probe = os.path.join(tmp_dir, "probe.docx")

    toc_pages = {}
    measured = {}
    for _ in range(4):
        _render_once(md_path, probe, toc_pages)
        pdf = render_pdf(probe, tmp_dir)
        if not pdf:
            break
        measured = measure_toc(pdf, chapters)
        if measured == toc_pages:
            break
        toc_pages = measured
    else:
        _render_once(md_path, out_path, toc_pages)
        return out_path

    _render_once(md_path, out_path, toc_pages)
    return out_path


if __name__ == "__main__":
    md = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        ROOT, "report/图论综合应用报告-合订版.md")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        ROOT, "report/图论综合应用报告.docx")
    p = make_docx(md, out)
    print("[docx] %s  (%.0f KB)" % (p, os.path.getsize(p) / 1024))
