#!/bin/bash
# 双击本文件即可把报告导出为 PDF（使用本机 Google Chrome 的无头打印）
# 需要本机装有 Google Chrome：/Applications/Google Chrome.app
set -e
DIR="$(cd "$(dirname "$0")/.." && pwd)"
HTML="$DIR/report/图论综合应用报告.html"
PDF="$DIR/report/图论综合应用报告.pdf"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

if [ ! -f "$HTML" ]; then
  echo "未找到 $HTML，请先运行： python main.py"
  exit 1
fi
if [ ! -x "$CHROME" ]; then
  echo "未找到 Google Chrome。请改用手动方式："
  echo "  1) 双击打开 $HTML"
  echo "  2) 按 Cmd+P → 目标选择「另存为 PDF」→ 保存"
  exit 1
fi

echo "正在导出 PDF ..."
"$CHROME" --headless --disable-gpu --no-pdf-header-footer \
         --virtual-time-budget=20000 \
         --print-to-pdf="$PDF" "file://$HTML"
echo "完成： $PDF"
open -R "$PDF" 2>/dev/null || true
