#!/usr/bin/env bash
# Rebuild from the source of truth and put it live. Safe to run any time.
set -euo pipefail
cd "$(dirname "$0")"

echo "==> rebuilding from ~/mromars-store/toybox (prices come from the workshop)"
python3 ~/mromars-store/toybox/build.py 84 --split "$PWD"

# Anything the build no longer emits is dead weight; index.html names what it needs.
echo "==> dropping assets the page no longer references"
for f in assets/*; do
  grep -q "$(basename "$f")" index.html || { echo "    - $(basename "$f")"; rm -f "$f"; }
done

if [ -z "$(git status --porcelain)" ]; then echo "==> nothing changed"; exit 0; fi
git add -A
git commit -q -m "${1:-site: rebuild from the workshop}"
git push -q origin main
echo "==> pushed. GitHub Pages usually serves it within a minute."
