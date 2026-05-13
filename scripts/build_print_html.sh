#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INPUT_MD="${1:-$ROOT_DIR/从零开始学习自动驾驶_合并版.md}"
OUTPUT_HTML="${2:-$ROOT_DIR/从零开始学习自动驾驶.html}"
FILTER_LUA="$ROOT_DIR/tools/pandoc/github_print.lua"
CSS_FILE="$ROOT_DIR/tools/pandoc/print.css"
HEADER_FILE="$ROOT_DIR/tools/pandoc/print_header.html"
COMBINE_SCRIPT="$ROOT_DIR/scripts/build_combined_markdown.py"
RENDER_SUPPORT_JS="$ROOT_DIR/tools/pandoc/render_support.js"

python3 "$COMBINE_SCRIPT"

pandoc \
  -f gfm-yaml_metadata_block+tex_math_dollars \
  -t html5 \
  -s \
  --embed-resources \
  --css "$CSS_FILE" \
  --lua-filter "$FILTER_LUA" \
  --metadata title="从零开始学习自动驾驶" \
  --include-in-header "$HEADER_FILE" \
  -o "$OUTPUT_HTML" \
  "$INPUT_MD"

python3 - "$OUTPUT_HTML" "$RENDER_SUPPORT_JS" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
render_support = Path(sys.argv[2]).read_text(encoding="utf-8")
text = path.read_text(encoding="utf-8")

text = re.sub(r"<body>", "<body>\n<main>", text, count=1)
text = re.sub(r"</body>", "</main>\n</body>", text, count=1)
text = re.sub(r'\s*<a href="[^"]+">\s*</a>', "", text)
text = re.sub(r'\s*&lt;a href=&quot;[^"]+&quot;&gt;\s*', "\n", text)
text = re.sub(r'\s*&lt;/a&gt;\s*', "\n", text)
text = re.sub(
    r'<a href="https://github\.com/qwefvb/Autonomous-Driving-From-Zero">.*?<h2>🚀 从学术基础到前沿实战的自动驾驶科研一站式路径</h2>',
    "<h2>🚀 从学术基础到前沿实战的自动驾驶科研一站式路径</h2>",
    text,
    count=1,
    flags=re.S,
)
text = re.sub(
    r"</body>",
    "<script>\n" + render_support + "\n</script>\n</body>",
    text,
    count=1,
)

path.write_text(text, encoding="utf-8")
print(f"wrote {path}")
PY
