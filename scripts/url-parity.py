#!/usr/bin/env python3
"""Does the Starlight build serve everything turingpi.xyz serves?

A GATE with --strict (CI and `just site-parity` pass it), a report without.
Four questions, each against the live site, which is the reference:

  pages   every <loc> in the live sitemap.xml has an index.html in dist/,
          at the same directory URL;
  assets  every file the live pages reference from this site -- images,
          downloads, the feed -- and every Git LFS file under docs/, is in
          dist/ with the SAME BYTES (sha256), and none of them is a Git LFS
          pointer. URL parity alone once passed while every image on another
          site was a 129-byte LFS pointer;
  head    each page's <title>, description, canonical, robots, Open Graph
          and Twitter tags, and JSON-LD (parsed, and compared per @type, so
          formatting does not count) agree with the live page;
  anchors every heading id a live page has is on the built page, so deep
          links into a page keep landing.

--strict fails on a missing page, a missing or different asset, an LFS
pointer, a lost anchor, a live page or asset that could not be read, and a
head difference that is not in DELIBERATE below. DELIBERATE is the list of
things the new build fixes on purpose; an entry whose difference has gone
(the live site was fixed, or this build stopped fixing it) also fails, so the
list cannot outlive what it excuses.

--mkdocs site/ names the MkDocs build of the SAME commit. The live site is
the commit pages.yml last deployed, so a pull request that edits a page --
or the hourly refresh, on main a minute before its deploy lands -- differs
from it for a reason that has nothing to do with the port. A difference the
same-commit MkDocs build shares with this one is reported as "moved since
the live deploy" and does not fail; one this build has alone does. Without
--mkdocs every difference counts.

Material's own theme files (assets/javascripts, assets/stylesheets, the
favicon, the search index) are counted separately: Starlight brings its own
and nothing links to Material's from outside.

usage: scripts/url-parity.py [--dist starlight/dist] [--site https://turingpi.xyz]
                             [--sitemap URL|FILE] [--mkdocs site] [--markdown FILE]
                             [--json FILE] [--strict]
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
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


# -- the deliberate differences ------------------------------------------------
#
# Each entry is one head field on one page that the Starlight build gets
# RIGHT and turingpi.xyz gets wrong, keyed by (URL, field). The field is
# "title", "canonical", a meta name or property ("description",
# "og:description", ...), or "json-ld:<@type>". The test says what the
# difference must look like, so a second, accidental change to the same field
# is still caught: it is given the reference value (live, or the same-commit
# MkDocs build) and this build's, and returns True when the difference is the
# fix and nothing else.
#
# Remove an entry when the live site stops having the fault -- the gate says
# so. Add one only for a fix made on purpose, with the reason.


def _cut_at_quote(ref: str | None, mine: str | None) -> bool:
    """Live writes the description into the attribute unescaped, so the
    attribute ends at the first `"` in it. This build escapes it: the same
    text, continued from where live stops, starting at that quote."""
    return bool(ref and mine and mine.startswith(ref)
                and mine[len(ref):].startswith('"'))


def _faq_rendered(ref, mine) -> bool:
    """The same questions; live's answers carry raw Jinja and these carry
    the values a reader sees on the page."""
    def questions(docs):
        return [q.get("name") for d in docs or [] for q in d.get("mainEntity", [])]
    blob = lambda docs: json.dumps(docs or [], ensure_ascii=False)
    return (bool(ref) and bool(mine) and questions(ref) == questions(mine)
            and "{{" in blob(ref) and "{{" not in blob(mine)
            and "{%" not in blob(mine))


_V2390 = "/news/v2.39.0/"
_V292 = "/news/v2.9.2/"
DELIBERATE = {
    # (a) The FAQ's FAQPage. main.py's _faq_entities() reads faq.md before
    # the macros render it, so every answer that quotes a fact says
    # `{{ roadmap.count }}` to a search engine. route-data.ts asks lib/faq.ts
    # for 'value' since phase 3: the numbers the page itself shows.
    ("/faq/", "json-ld:FAQPage"): (_faq_rendered,
        "FAQ answers carry the facts' values; live carries raw {{ ... }}"),
    # (b) Two release posts whose description contains a `"`.
    # overrides/main.html writes it into content="..." unescaped, so live's
    # meta tags stop at the quote; Starlight escapes it (&quot;) and the
    # whole description arrives. The JSON-LD was already whole on both.
    (_V2390, "description"): (_cut_at_quote, "live cuts it at an unescaped \""),
    (_V2390, "og:description"): (_cut_at_quote, "live cuts it at an unescaped \""),
    (_V2390, "twitter:description"): (_cut_at_quote, "live cuts it at an unescaped \""),
    (_V292, "description"): (_cut_at_quote, "live cuts it at an unescaped \""),
    (_V292, "og:description"): (_cut_at_quote, "live cuts it at an unescaped \""),
    (_V292, "twitter:description"): (_cut_at_quote, "live cuts it at an unescaped \""),
}


# -- reading -------------------------------------------------------------------

def fetch(url: str, timeout: float = 30) -> tuple[str, bytes | None]:
    """("ok", body), ("404", None) or ("error", None) after three tries.

    The two failures are not the same answer. A 404 is the live site saying
    it has no such thing; an error is the reference being unreadable, and a
    gate must not count a page it could not read as a page that agreed.
    """
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return "ok", r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return "404", None
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            pass
    return "error", None


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

    def fields(self) -> dict[str, object]:
        """Every compared head field, by the name DELIBERATE keys on."""
        out: dict[str, object] = {"title": self.title,
                                  "canonical": self.canonical.rstrip("/")}
        out.update(self.meta)
        by_type: dict[str, list] = {}
        for d in self.jsonld:
            kind = d.get("@type", "?") if isinstance(d, dict) else "?"
            by_type.setdefault(f"json-ld:{kind}", []).append(d)
        key = lambda d: json.dumps(d, sort_keys=True)
        for k, docs in by_type.items():
            out[k] = sorted(docs, key=key)
        return out


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


def short(v: object, n: int = 300) -> str:
    s = repr(v) if isinstance(v, str) or v is None else json.dumps(
        v, sort_keys=True, ensure_ascii=False)
    return s if len(s) <= n else s[:n] + "…"


# -- the comparison ------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dist", default=str(ROOT / "starlight" / "dist"))
    ap.add_argument("--site", default="https://turingpi.xyz")
    ap.add_argument("--sitemap", help="URL or file (default: <site>/sitemap.xml)")
    ap.add_argument("--mkdocs", help="the MkDocs build of the same commit (site/): "
                    "a difference it shares is content that moved since the live "
                    "deploy, not a port fault")
    ap.add_argument("--markdown", help="also write the report here (e.g. $GITHUB_STEP_SUMMARY)")
    ap.add_argument("--json", help="write the full findings here")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 on any fault (see the module docstring)")
    args = ap.parse_args()
    dist = pathlib.Path(args.dist)
    site = args.site.rstrip("/")
    mk = pathlib.Path(args.mkdocs) if args.mkdocs else None
    if not (dist / "index.html").is_file():
        print(f"url-parity: no build at {dist}; run `just site-build` first", file=sys.stderr)
        return 2
    if mk and not (mk / "index.html").is_file():
        print(f"url-parity: no MkDocs build at {mk}; run `just build` first", file=sys.stderr)
        return 2
    read_at = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    src = args.sitemap or f"{site}/sitemap.xml"
    if pathlib.Path(src).is_file():
        raw = pathlib.Path(src).read_bytes()
    else:
        _, raw = fetch(src)
    if raw is None:
        print(f"url-parity: cannot read {src}; nothing to compare", file=sys.stderr)
        return 0 if not args.strict else 1
    locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", raw.decode())
    paths = [urllib.parse.urlsplit(l).path or "/" for l in locs]

    def mk_has(p: str) -> bool:
        return mk is not None and dist_file(mk, p).is_file()

    # -- pages ----------------------------------------------------------------
    missing_pages, moved_pages = [], []
    for p in paths:
        if dist_file(dist, p).is_file():
            continue
        # Gone from the same-commit MkDocs build too: removed in this commit.
        (moved_pages if mk and not mk_has(p) else missing_pages).append(p)
    built = set()
    for f in dist.rglob("index.html"):
        rel = f.parent.relative_to(dist).as_posix()
        if rel.startswith(("demo/stock", "demo/fork", "demo/fleet", "_astro", "pagefind")):
            continue
        built.add("/" if rel == "." else f"/{rel}/")
    extra_pages = sorted(built - set(paths))

    # -- live pages: head and references --------------------------------------
    def live(p):
        return p, fetch(site + p)
    with cf.ThreadPoolExecutor(8) as ex:
        live_pages = dict(ex.map(live, paths))
    unreadable = [p for p, (status, _) in live_pages.items() if status == "error"]

    head_faults: dict[str, list[str]] = {}
    head_moved: dict[str, list[str]] = {}
    deliberate_hit: set[tuple[str, str]] = set()     # the fix, as declared
    deliberate_seen: set[tuple[str, str]] = set()    # any difference at all
    lost_anchors: dict[str, list[str]] = {}
    moved_anchors: dict[str, list[str]] = {}
    live_anchors = 0
    refs: set[str] = set()
    compared: set[str] = set()
    for p, (status, body) in live_pages.items():
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
        compared.add(p)
        dh = parse(f.read_bytes())
        mh = parse(dist_file(mk, p).read_bytes()) if mk_has(p) else None

        live_anchors += len(lh.anchors)
        for a in sorted(lh.anchors - dh.anchors):
            gone = mh is not None and a not in mh.anchors
            (moved_anchors if gone else lost_anchors).setdefault(p, []).append(a)

        lf, df = lh.fields(), dh.fields()
        mf = mh.fields() if mh else None
        for k in sorted(set(lf) | set(df)):
            lv, dv = lf.get(k), df.get(k)
            if lv == dv:
                continue
            line = f"{k}: live {short(lv)} / dist {short(dv)}"
            entry = DELIBERATE.get((p, k))
            if entry:
                test, why = entry
                deliberate_seen.add((p, k))
                if test(lv, dv) or (mf is not None and test(mf.get(k), dv)):
                    deliberate_hit.add((p, k))
                    continue
                head_faults.setdefault(p, []).append(
                    f"{line} -- allowlisted ({why}), but this is not that difference")
            elif mf is not None and mf.get(k) == dv:
                head_moved.setdefault(p, []).append(line)
            else:
                head_faults.setdefault(p, []).append(line)
    # Stale: the page was compared and the field AGREES, so there is nothing
    # left to excuse. (A field that still differs, but not as declared, is a
    # head fault above.) A page that could not be compared is no evidence
    # either way; it fails anyway, as unreadable or missing.
    stale = sorted(k for k in DELIBERATE if k not in deliberate_seen and k[0] in compared)
    unjudged = sorted(k for k in DELIBERATE if k[0] not in compared)

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
    moved_assets = []
    for p, (status, body) in sorted(live_assets.items()):
        f = dist_file(dist, p)
        mkf = dist_file(mk, p) if mk else None
        if not f.is_file():
            # Not in the same-commit MkDocs build either: removed in this commit.
            if mkf is not None and not mkf.is_file():
                moved_assets.append(p)
            else:
                missing_assets.append(p)
            continue
        mine = f.read_bytes()
        if mine.startswith(LFS_POINTER):
            pointers.append(p)
        if status == "error":
            unreadable.append(p)
        elif body is None:
            live_missing.append(p)
        elif sha(body) == sha(mine):
            same.append(p)
        elif mkf is not None and mkf.is_file() and sha(mkf.read_bytes()) == sha(mine):
            moved_assets.append(p)
        else:
            differ.append(p)
    unreadable = sorted(set(unreadable))

    # -- report ---------------------------------------------------------------
    n_faults = sum(map(len, head_faults.values()))
    n_moved = sum(map(len, head_moved.values()))
    out = []
    w = out.append
    w("## URL parity: Starlight build vs " + site)
    w("")
    w(f"Reference: **{site}**, read {read_at}. "
      + (f"A difference the same commit's MkDocs build (`{args.mkdocs}`) shares is "
         "content that moved since the live deploy, and does not fail. " if mk else
         "No same-commit MkDocs build given, so every difference counts. ")
      + ("**Gate (--strict).**" if args.strict else "Report only."))
    w("")
    w(f"**Pages:** {len(paths)} in the live sitemap, "
      f"{len(paths) - len(missing_pages) - len(moved_pages)} built, "
      f"**{len(missing_pages)} missing**, {len(moved_pages)} removed in this commit; "
      f"{len(extra_pages)} built pages not in the sitemap.")
    for p in missing_pages:
        w(f"- missing: `{p}`")
    for p in moved_pages:
        w(f"- removed in this commit (the MkDocs build no longer has it either): `{p}`")
    for p in extra_pages:
        w(f"- extra: `{p}`")
    w("")
    w(f"**Assets:** {len(assets)} checked ({len(lfs)} Git LFS files under docs/, plus every "
      f"same-site file the live pages reference). **{len(same)} byte-identical**, "
      f"**{len(differ)} differ**, **{len(missing_assets)} missing from dist**, "
      f"{len(moved_assets)} moved since the live deploy, "
      f"{len(live_missing)} not on the live site, **{len(pointers)} LFS pointers in dist**.")
    for label, items in (("differs", differ), ("missing from dist", missing_assets),
                         ("moved since the live deploy", moved_assets),
                         ("not on the live site", live_missing), ("LFS POINTER", pointers)):
        for p in items:
            w(f"- {label}: `{p}`")
    w(f"- referenced by the live pages and not expected in dist (Material's theme, "
      f"Cloudflare's /cdn-cgi/): {len(theme)}")
    w("")
    differing = set(head_faults) | set(head_moved) | {k[0] for k in deliberate_hit}
    w(f"**Head:** {len(compared) - len(differing)} of {len(compared)} pages agree on title, "
      f"description, canonical, robots, Open Graph, Twitter and JSON-LD; "
      f"**{n_faults} faults** on {len(head_faults)} pages, {len(deliberate_hit)} deliberate "
      f"fixes, {n_moved} moved since the live deploy.")
    for title, groups in (("faults", head_faults), ("moved since the live deploy", head_moved)):
        for p, diffs in sorted(groups.items()):
            w(f"<details><summary><code>{p}</code>: {len(diffs)} {title}</summary>\n")
            for d in diffs:
                w(f"- {d}")
            w("\n</details>")
    w("")
    w(f"**Deliberate fixes** (DELIBERATE in scripts/url-parity.py): {len(DELIBERATE)} "
      f"allowlisted, {len(deliberate_hit)} present, **{len(stale)} stale**"
      + (f", {len(unjudged)} not judged (page not compared)" if unjudged else "") + ".")
    for k in sorted(DELIBERATE):
        state = ("present" if k in deliberate_hit else
                 "**STALE**: the difference is gone; remove the entry" if k in stale else
                 "**differs otherwise**: see the head faults" if k in deliberate_seen else
                 "not judged")
        w(f"- `{k[0]}` {k[1]}: {DELIBERATE[k][1]}. {state}")
    w("")
    w(f"**Anchors:** {live_anchors} heading ids on the live pages, "
      f"**{sum(map(len, lost_anchors.values()))} missing** from the build, "
      f"{sum(map(len, moved_anchors.values()))} removed in this commit.")
    for p, ids in sorted(lost_anchors.items()):
        w(f"- `{p}`: " + ", ".join(f"`#{i}`" for i in ids[:10]))
    for p, ids in sorted(moved_anchors.items()):
        w(f"- removed in this commit, `{p}`: " + ", ".join(f"`#{i}`" for i in ids[:10]))
    if unreadable:
        w("")
        w(f"**Unreadable on the live site:** {len(unreadable)} (network errors after three "
          f"tries; a gate cannot count them as agreeing).")
        for p in unreadable[:20]:
            w(f"- `{p}`")

    bad = {
        "missing pages": len(missing_pages),
        "assets that differ": len(differ),
        "assets missing from dist": len(missing_assets),
        "LFS pointers": len(pointers),
        "head faults": n_faults,
        "stale allowlist entries": len(stale),
        "lost anchors": sum(map(len, lost_anchors.values())),
        "unreadable live URLs": len(unreadable),
    }
    failed = {k: v for k, v in bad.items() if v}
    w("")
    w("**Verdict:** " + ("FAIL: " + ", ".join(f"{v} {k}" for k, v in failed.items())
                         if failed else "pass") + ".")
    report = "\n".join(out) + "\n"
    print(report)
    if args.markdown:
        with open(args.markdown, "a") as fh:
            fh.write(report)
    if args.json:
        pathlib.Path(args.json).write_text(json.dumps({
            "reference": {"site": site, "read_at": read_at, "mkdocs": args.mkdocs},
            "pages": {"live": len(paths), "missing": missing_pages,
                      "removed_in_commit": moved_pages, "extra": extra_pages},
            "assets": {"checked": len(assets), "same": same, "differ": differ,
                       "missing": missing_assets, "moved": moved_assets,
                       "live_missing": live_missing, "lfs_pointers": pointers,
                       "theme": sorted(theme)},
            "head": {"faults": head_faults, "moved": head_moved,
                     "deliberate": sorted(map(list, deliberate_hit)),
                     "stale": [list(k) for k in stale]},
            "anchors": {"live": live_anchors, "missing": lost_anchors,
                        "removed_in_commit": moved_anchors},
            "unreadable": unreadable,
            "verdict": "fail" if failed else "pass",
        }, indent=2) + "\n")
    return 1 if (args.strict and failed) else 0


if __name__ == "__main__":
    sys.exit(main())
