#!/usr/bin/env bash
# يجمع ملفات الصفحة داخل app/www ليحزمها التطبيق (نفس الصفحة المنشورة على GitHub Pages).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/app/www"
rm -rf "$OUT" && mkdir -p "$OUT/data"
for f in index.html manifest.webmanifest icon.svg icon-192.png icon-512.png icon-maskable-512.png; do
  cp "$ROOT/$f" "$OUT/$f"
done
cp "$ROOT/data/words.json" "$ROOT/data/progress.json" "$OUT/data/"
echo "www ready: $(find "$OUT" -type f | wc -l) files, $(du -sk "$OUT" | cut -f1) KB"
