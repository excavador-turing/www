#!/usr/bin/env python3
"""Does the Starlight build serve everything turingpi.xyz serves?

A REPORT, not a gate (yet): it always exits 0 unless --strict is given.
Three questions, each against the live site (or a sitemap/directory given
on the command line):

  pages   every <loc> in the live sitemap.xml has an index.html in dist/,
          at the same directory URL;
  assets  every file the live pages reference from this site -- images,
          downloads, the feed -- and every Git LFS file under docs/, is in
          dist/ with the SAME BYTES (sha256). URL parity alone once passed
          while every image on another site was a 129-byte LFS pointer;
  head    each page's <title>, description, canonical, robots, Open Graph
          and Twitter tags, and JSON-LD (parsed, so formatting does not
          count) agree with the live page;
  anchors every heading id a live page has is on the built page, so deep
          links into a page keep landing.

Material's own theme files (assets/javascripts, assets/stylesheets, the
favicon, the search index) are counted separately: Starlight brings its own
and nothing links to Material's from outside.

usage: scripts/url-parity.py [--dist starlight/dist] [--site https://turingpi.xyz]
                             [--sitemap URL|FILE] [--markdown FILE] [--strict]
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import html.parser
import json
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
UA = "turingpi-url-parity/1 (+https://github.com/excavador-turing/www)"
LFS_POINTER = b"version https://git-lfs.github.com/spec/v1"

# Material's theme, not the site's content: Starlight ships its own. And
# Cloudflare's edge, which rewrites pages on the way out (email obfuscation
# under /cdn-cgi/) and will do the same to whatever the origin serves.
THEME = re.compile(r"^/(assets/(javascripts|stylesheets|images)/|search/|cdn-cgi/)")


def fetch(url: str, timeout: float = 30) -> bytes | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            pass
    return None


class Head(html.parser.HTMLParser):
    """The head tags this report compares, and every same-site reference."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.meta: dict[str, str] = {}
        self.canonical = ""
        self.jsonld: list = []
        self.refs: set[str] = set()
        self.anchors: set[str] = set()
        self._in_title = False
        self._in_ld = False
        self._ld = ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("h2", "h3", "h4", "h5", "h6") and a.get("id"):
            self.anchors.add(a["id"])
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            key = a.get("property") or a.get("name")
            if key and (key in ("description", "robots") or key.startswith(("og:", "twitter:", "article:"))):
                self.meta[key] = a.get("content") or ""
        elif tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href") or ""
        elif tag == "script" and a.get("type") == "application/ld+json":
            self._in_ld, self._ld = True, ""
        for attr in ("src", "href", "data-src", "poster"):
            if a.get(attr):
                self.refs.add(a[attr])
        if a.get("srcset"):
            for part in a["srcset"].split(","):
                self.refs.add(part.strip().split(" ")[0])

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "script" and self._in_ld:
            self._in_ld = False
            try:
                self.jsonld.append(json.loads(self._ld))
            except ValueError:
                self.jsonld.append({"unparseable": self._ld.strip()[:80]})

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._in_ld:
            self._ld += data


def parse(html_bytes: bytes) -> Head:
    h = Head()
    h.feed(html_bytes.decode("utf-8", "replace"))
    h.title = " ".join(h.title.split())
    return h


def same_site_path(ref: str, page_url: str, site: str) -> str | None:
    """A reference on a page -> the site path it names, or None if elsewhere."""
    u = urllib.parse.urljoin(page_url, ref)
    p = urllib.parse.urlsplit(u)
    s = urllib.parse.urlsplit(site)
    if p.scheme not in ("http", "https") or p.netloc != s.netloc:
        return None
    return urllib.parse.unquote(p.path)


def dist_file(dist: pathlib.Path, path: str) -> pathlib.Path:
    rel = path.lstrip("/")
    if rel == "" or rel.endswith("/"):
        rel += "index.html"
    return dist / rel


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def lfs_paths() -> list[str]:
    try:
        out = subprocess.run(["git", "lfs", "ls-files", "-n"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return []
    return sorted("/" + l[len("docs/"):] for l in out.splitlines() if l.startswith("docs/"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dist", default=str(ROOT / "starlight" / "dist"))
    ap.add_argument("--site", default="https://turingpi.xyz")
    ap.add_argument("--sitemap", help="URL or file (default: <site>/sitemap.xml)")
    ap.add_argument("--markdown", help="also write the report here (e.g. $GITHUB_STEP_SUMMARY)")
    ap.add_argument("--json", help="write the full findings here")
    ap.add_argument("--strict", action="store_true", help="exit 1 on any miss")
    args = ap.parse_args()
    dist = pathlib.Path(args.dist)
    site = args.site.rstrip("/")
    if not (dist / "index.html").is_file():
        print(f"url-parity: no build at {dist}; run `just site-build` first", file=sys.stderr)
        return 2

    src = args.sitemap or f"{site}/sitemap.xml"
    raw = pathlib.Path(src).read_bytes() if pathlib.Path(src).is_file() else fetch(src)
    if raw is None:
        print(f"url-parity: cannot read {src}; nothing to compare", file=sys.stderr)
        return 0 if not args.strict else 1
    locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", raw.decode())
    paths = [urllib.parse.urlsplit(l).path or "/" for l in locs]

    # -- pages ----------------------------------------------------------------
    missing_pages = [p for p in paths if not dist_file(dist, p).is_file()]
    built = set()
    for f in dist.rglob("index.html"):
        rel = f.parent.relative_to(dist).as_posix()
        if rel.startswith(("demo/stock", "_astro", "pagefind")):
            continue
        built.add("/" if rel == "." else f"/{rel}/")
    extra_pages = sorted(built - set(paths))

    # -- live pages: head and references --------------------------------------
    def live(p):
        return p, fetch(site + p)
    with cf.ThreadPoolExecutor(8) as ex:
        live_pages = dict(ex.map(live, paths))

    head_diffs: dict[str, list[str]] = {}
    lost_anchors: dict[str, list[str]] = {}
    live_anchors = 0
    refs: set[str] = set()
    for p, body in live_pages.items():
        if body is None:
            continue
        lh = parse(body)
        for r in lh.refs:
            sp = same_site_path(r, site + p, site)
            if sp:
                refs.add(sp)
        f = dist_file(dist, p)
        if not f.is_file():
            continue
        dh = parse(f.read_bytes())
        live_anchors += len(lh.anchors)
        if lh.anchors - dh.anchors:
            lost_anchors[p] = sorted(lh.anchors - dh.anchors)
        diffs = []
        if lh.title != dh.title:
            diffs.append(f"title: live {lh.title!r} / dist {dh.title!r}")
        if lh.canonical.rstrip("/") != dh.canonical.rstrip("/"):
            diffs.append(f"canonical: live {lh.canonical!r} / dist {dh.canonical!r}")
        for k in sorted(set(lh.meta) | set(dh.meta)):
            if lh.meta.get(k) != dh.meta.get(k):
                diffs.append(f"{k}: live {lh.meta.get(k)!r} / dist {dh.meta.get(k)!r}")
        key = lambda d: json.dumps(d, sort_keys=True)
        if sorted(map(key, lh.jsonld)) != sorted(map(key, dh.jsonld)):
            diffs.append("json-ld: live " + "; ".join(sorted(map(key, lh.jsonld)))[:400]
                         + " / dist " + "; ".join(sorted(map(key, dh.jsonld)))[:400])
        if diffs:
            head_diffs[p] = diffs

    # -- assets ---------------------------------------------------------------
    page_paths = set(paths)
    assets = set()
    theme = set()
    for r in refs:
        if r in page_paths or r.endswith("/") or r.endswith(".html"):
            continue
        (theme if THEME.match(r) else assets).add(r)
    lfs = lfs_paths()
    assets |= {p for p in lfs if not p.startswith(("/demo/fork/", "/demo/fleet/"))}

    def asset(p):
        return p, fetch(site + urllib.parse.quote(p))
    with cf.ThreadPoolExecutor(8) as ex:
        live_assets = dict(ex.map(asset, sorted(assets)))
    same, differ, missing_assets, live_missing, pointers = [], [], [], [], []
    for p, body in sorted(live_assets.items()):
        f = dist_file(dist, p)
        if not f.is_file():
            missing_assets.append(p)
            continue
        mine = f.read_bytes()
        if mine.startswith(LFS_POINTER):
            pointers.append(p)
        if body is None:
            live_missing.append(p)
        elif sha(body) == sha(mine):
            same.append(p)
        else:
            differ.append(p)

    # -- report ---------------------------------------------------------------
    out = []
    w = out.append
    w("## URL parity: Starlight build vs " + site)
    w("")
    w(f"**Pages:** {len(paths)} in the live sitemap, {len(paths) - len(missing_pages)} built, "
      f"**{len(missing_pages)} missing**; {len(extra_pages)} built pages not in the sitemap.")
    for p in missing_pages:
        w(f"- missing: `{p}`")
    for p in extra_pages:
        w(f"- extra: `{p}`")
    w("")
    w(f"**Assets:** {len(assets)} checked ({len(lfs)} Git LFS files under docs/, plus every "
      f"same-site file the live pages reference). **{len(same)} byte-identical**, "
      f"**{len(differ)} differ**, **{len(missing_assets)} missing from dist**, "
      f"{len(live_missing)} not on the live site, **{len(pointers)} LFS pointers in dist**.")
    for label, items in (("differs", differ), ("missing from dist", missing_assets),
                         ("not on the live site", live_missing), ("LFS POINTER", pointers)):
        for p in items:
            w(f"- {label}: `{p}`")
    w(f"- referenced by the live pages and not expected in dist (Material's theme, "
      f"Cloudflare's /cdn-cgi/): {len(theme)}")
    w("")
    w(f"**Head:** {len(paths) - len(missing_pages) - len(head_diffs)} pages agree on title, "
      f"description, canonical, robots, Open Graph, Twitter and JSON-LD; "
      f"**{len(head_diffs)} differ**.")
    for p, diffs in sorted(head_diffs.items()):
        w(f"<details><summary><code>{p}</code>: {len(diffs)}</summary>\n")
        for d in diffs:
            w(f"- {d}")
        w("\n</details>")
    w("")
    w(f"**Anchors:** {live_anchors} heading ids on the live pages, "
      f"**{sum(map(len, lost_anchors.values()))} missing** from the build.")
    for p, ids in sorted(lost_anchors.items()):
        w(f"- `{p}`: " + ", ".join(f"`#{i}`" for i in ids[:10]))
    report = "\n".join(out) + "\n"
    print(report)
    if args.markdown:
        with open(args.markdown, "a") as fh:
            fh.write(report)
    if args.json:
        pathlib.Path(args.json).write_text(json.dumps({
            "pages": {"live": len(paths), "missing": missing_pages, "extra": extra_pages},
            "assets": {"checked": len(assets), "same": same, "differ": differ,
                       "missing": missing_assets, "live_missing": live_missing,
                       "lfs_pointers": pointers, "theme": sorted(theme)},
            "head": head_diffs,
            "anchors": {"live": live_anchors, "missing": lost_anchors},
        }, indent=2) + "\n")
    bad = missing_pages or differ or missing_assets or pointers or lost_anchors
    return 1 if (args.strict and bad) else 0


if __name__ == "__main__":
    sys.exit(main())
