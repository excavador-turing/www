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

for f in index.html 404.html llms.txt sitemap.xml sitemap-index.xml robots.txt \
         feed.xml stylesheets/landing.css features/index.html news/index.html \
         news/page/2/index.html reference/api/index.html favicon.svg build.json; do
  [ -s "$dist/$f" ] || bad "missing or empty: $f"
done

# /build.json (stamp-build.py) names the commit that was built: it is what
# the publish workflow's `published` job compares with the live site.
if [ -s "$dist/build.json" ] && ! python3 - "$dist/build.json" "$(git rev-parse HEAD)" <<'PY'
import json, re, sys
b = json.load(open(sys.argv[1]))
ok = (b.get("commit") == sys.argv[2] and bool(b.get("run"))
      and re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", b.get("built_at") or ""))
sys.exit(0 if ok else 1)
PY
then
  bad "build.json does not name this commit, a run and a build time: $(tr -d '\n' < "$dist/build.json")"
fi

# /llms.txt: astro.config.mjs's `llmsTxt` switch. starlight-llms-txt writes
# llms-full.txt beside it; without that, it must be the curated index,
# byte for byte what scripts/llms.py wrote.
if [ ! -e "$dist/llms-full.txt" ] && ! cmp -s "$dist/llms.txt" docs/llms.txt; then
  bad "llms.txt is neither starlight-llms-txt's (no llms-full.txt) nor docs/llms.txt"
fi

# The feed: refresh-changelog.py writes it, and it is served as written, at
# the address the live site's <head> announces. Every entry links a post
# that this build has.
if ! cmp -s "$dist/feed.xml" docs/feed.xml; then
  bad "feed.xml is not docs/feed.xml byte for byte"
fi
while read -r href; do
  path=${href#https://turingpi.xyz}
  [ -s "$dist${path}index.html" ] || bad "feed.xml links $href, which this build does not have"
done < <(grep -oE '<link href="https://turingpi\.xyz/news/[^"]*"' "$dist/feed.xml" | sed -E 's/<link href="([^"]*)"/\1/')

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
# converted, not printed: in the visible text and in the JSON-LD, whose FAQ
# answers carry raw `{{ ... }}` on the live site (main.py parses faq.md
# before rendering) and real values here since phase 3. Code is skipped:
# reference/metrics quotes a Prometheus template on purpose.
leftovers=$(python3 - "$dist" <<'PY'
import pathlib, re, sys
for f in sorted(pathlib.Path(sys.argv[1]).rglob("index.html")):
    t = f.read_text(errors="replace")
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
