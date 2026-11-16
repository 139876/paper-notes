# -*- coding: utf-8 -*-
"""
生成自包含的打印就绪 HTML（图片 base64 内联 + MathJax 本地内联）。

用法: python tools/build_html.py [input.md] [output.html]

之后可直接用浏览器打开 -> Cmd+P -> 另存为 PDF；
或运行 tools/导出PDF.command 一键导出（用本机 Chrome 的 headless 打印）。
"""
from __future__ import annotations
import base64
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PANDOC = "/opt/anaconda3/bin/pandoc"
MATHJAX = os.path.join(ROOT, "tools/vendor/mathjax/tex-svg.js")

PRINT_CSS = r"""
@page { size: A4; margin: 20mm 18mm 18mm 18mm; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body {
  font-family: "Songti SC", "STSong", "PingFang SC", "Heiti SC", serif;
  font-size: 10.5pt; line-height: 1.8; color: #1a1a1a; margin: 0;
  text-align: justify; word-wrap: break-word;
}
h1, h2, h3, h4, h5 {
  font-family: "PingFang SC", "Heiti SC", "Helvetica Neue", sans-serif;
  color: #16324f; line-height: 1.45; page-break-after: avoid; break-after: avoid;
}
h1 { font-size: 19pt; margin: 0 0 16pt; padding: 0 0 8pt; text-align: center;
     border-bottom: 2.4pt solid #16324f; page-break-before: always; break-before: page; }
h1:first-of-type { page-break-before: avoid; break-before: auto; }
h2 { font-size: 14pt; margin: 20pt 0 9pt; padding-left: 8pt; border-left: 4pt solid #2e7d9e; }
h3 { font-size: 12pt; margin: 15pt 0 7pt; color: #2e5c7a; }
h4 { font-size: 11pt; margin: 12pt 0 6pt; }
p { margin: 0 0 9pt; }
strong { color: #0d2b45; }
em { color: #33475b; }
table { border-collapse: collapse; width: 100%; margin: 10pt 0 15pt; font-size: 9pt;
        page-break-inside: avoid; break-inside: avoid; }
th { background: #16324f; color: #fff; font-weight: 600; padding: 5.5pt 7pt;
     border: 0.6pt solid #16324f; text-align: left; }
td { padding: 5pt 7pt; border: 0.5pt solid #b8c4d0; vertical-align: top; }
tr:nth-child(even) td { background: #f4f7fa; }
img { max-width: 100%; height: auto; display: block; margin: 12pt auto 4pt;
      page-break-inside: avoid; break-inside: avoid; }
code { font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 9pt;
       background: #eef2f6; padding: 1pt 3.5pt; border-radius: 3pt; color: #1f3b52; }
pre { background: #f4f6f8; border-left: 3pt solid #2e7d9e; padding: 9pt 11pt;
      font-size: 8.5pt; line-height: 1.55; overflow-x: auto;
      page-break-inside: avoid; break-inside: avoid; }
pre code { background: none; padding: 0; font-size: 8.5pt; }
blockquote { border-left: 3.5pt solid #d9a441; background: #fdf9ef; margin: 11pt 0;
             padding: 9pt 13pt; color: #4a3c1c; page-break-inside: avoid; break-inside: avoid; }
blockquote p { margin: 0 0 6pt; }
blockquote p:last-child { margin-bottom: 0; }
hr { border: none; border-top: 0.6pt solid #ccd6e0; margin: 18pt 0; }
ul, ol { margin: 0 0 9pt; padding-left: 24pt; }
li { margin: 2.5pt 0; }
mjx-container[jax="SVG"][display="true"] { margin: 10pt 0 !important; }
"""


def build(md_path: str, html_path: str) -> str:
    md_path = os.path.abspath(md_path)
    html_path = os.path.abspath(html_path)
    tmp = html_path + ".tmp.html"
    subprocess.run([
        PANDOC, md_path,
        "-f", "markdown+raw_html+tex_math_dollars",
        "-t", "html5",
        "--standalone", "--mathjax",
        "--metadata", "title=基于图论的重庆大学虎溪校区快递配送路径优化研究",
        "--metadata", "lang=zh-CN",
        "--resource-path", os.path.dirname(md_path) + os.pathsep + ROOT,
        "-o", tmp,
    ], check=True)

    html = open(tmp, encoding="utf-8").read()
    # 内联图片（base64），保证单文件可分发
    def _img(m):
        src = m.group(1)
        if src.startswith("data:"):
            return m.group(0)
        p = src if os.path.isabs(src) else os.path.join(os.path.dirname(md_path), src)
        if not os.path.exists(p):
            p2 = os.path.join(ROOT, src.lstrip("./"))
            if os.path.exists(p2):
                p = p2
            else:
                return m.group(0)
        ext = os.path.splitext(p)[1].lower().lstrip(".") or "png"
        mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                "gif": "image/gif", "svg": "image/svg+xml", "webp": "image/webp"}.get(ext, "application/octet-stream")
        b64 = base64.b64encode(open(p, "rb").read()).decode()
        return f'src="data:{mime};base64,{b64}"'
    html = re.sub(r'src="([^"]+)"', _img, html)

    # 内联打印样式
    html = html.replace("</head>", f"<style>\n{PRINT_CSS}\n</style>\n</head>")

    # 内联 MathJax（本地，离线可用）
    mj = open(MATHJAX, encoding="utf-8").read()
    html = html.replace("</body>", """
<script>
window.MathJax = {
  tex: { inlineMath: [['\\\\(','\\\\)']], displayMath: [['\\\\[','\\\\]']] },
  svg: { fontCache: 'global' },
  options: { skipHtmlTags: ['script','noscript','style','textarea','pre','code'] },
  startup: { typeset: true }
};
</script>
<script>""" + mj + """</script>
</body>""")
    open(html_path, "w", encoding="utf-8").write(html)
    os.remove(tmp)
    return html_path


if __name__ == "__main__":
    md = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "report/图论综合应用报告-合订版.md")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "report/图论综合应用报告.html")
    p = build(md, out)
    print(f"[html] {p}  ({os.path.getsize(p)/1024/1024:.2f} MB)")
