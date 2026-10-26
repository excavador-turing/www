#!/usr/bin/env bash
# What the built site must contain, checked in starlight/dist (or the
# directory given, relative to the repository root). Each check fails
# closed: a missing file or an empty match is a failure.
#
# usage: starlight/scripts/check-built.sh [dist]
set -euo pipefail
cd "$(dirname "$0")/../.."
dist=${1:-starlight/dist}
fail=0
bad() { echo "check-built: $*" >&2; fail=1; }

for f in index.html 404.html llms.txt llms-full.txt sitemap.xml sitemap-index.xml robots.txt \
         feed.xml stylesheets/landing.css features/index.html news/index.html \
         news/page/2/index.html reference/api/index.html; do
  [ -s "$dist/$f" ] || bad "missing or empty: $f"
done

# Search: Pagefind's index and its entry point.
[ -s "$dist/pagefind/pagefind.js" ] || bad "no Pagefind entry point in $dist/pagefind"
[ -n "$(ls "$dist"/pagefind/index 2>/dev/null)" ] || bad "no Pagefind index shards in $dist/pagefind/index"

# No Git LFS pointer may be published as the file it stands for. A checkout
# without `lfs: true` builds green and serves 130-byte text files as every
# image and font -- URL parity cannot see it, so it is checked here, on
# every file small enough to be a pointer.
pointers=$(find "$dist" -type f -size -1024c -print0 |
  xargs -0 -r grep -l -m1 '^version https://git-lfs.github.com/spec/v1' 2>/dev/null || true)
if [ -n "$pointers" ]; then
  bad "Git LFS pointers in the build (check out with LFS): $(echo "$pointers" | head -5 | tr '\n' ' ')"
fi
images=$(find "$dist/assets" -type f \( -name '*.png' -o -name '*.jpg' \) | wc -l)
[ "$images" -gt 0 ] || bad "no images under $dist/assets"

# Macros were rendered, not printed, and Material's block syntax was
# converted, not printed. Visible text only: the FAQ's JSON-LD carries raw
# `{{ ... }}` on the live site too (main.py parses faq.md before rendering),
# and reference/metrics quotes a Prometheus template on purpose.
leftovers=$(python3 - "$dist" <<'PY'
import pathlib, re, sys
for f in sorted(pathlib.Path(sys.argv[1]).rglob("index.html")):
    t = f.read_text(errors="replace")
    t = re.sub(r'<script type="application/ld\+json">.*?</script>', "", t, flags=re.S)
    t = re.sub(r"<(pre|code)[\s>].*?</\1>", "", t, flags=re.S)
    if re.search(r"\{\{ *[a-z_]+[ .(|]|\{%|<p>(!!!|\?\?\?|===) ", t):
        print(f)
PY
)
[ -z "$leftovers" ] || bad "unrendered macros or Material syntax in: $(echo "$leftovers" | head -3 | tr '\n' ' ')"

# The known-broken list may only shrink: a listed link whose page now exists
# has been fixed, and its line must go so the validator checks it again.
while read -r link; do
  path=${link%%#*}
  [ -n "$path" ] || continue
  if [ -s "$dist${path}index.html" ]; then
    bad "$link is listed in starlight/src/known-broken-links.mjs and now exists: delete the line"
  fi
done < <(grep -oE '^ +"/[^"]*"' starlight/src/known-broken-links.mjs | tr -d ' "')

[ "$fail" -eq 0 ] || exit 1
echo "check-built: ok ($(find "$dist" -name '*.html' | wc -l) HTML files, $images images, no LFS pointers)"
