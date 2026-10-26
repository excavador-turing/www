#!/usr/bin/env python3
"""Prove every internal link in the BUILT site lands on a file.

    just links-internal

starlight-links-validator checks the links in the content and nothing else.
A link written as raw HTML -- the cards, the plates, the "next" blocks, the
header and the footer -- is resolved by the BROWSER against the served URL,
so one written for a page at a different depth is a 404 that nothing
noticed: under MkDocs 62 of them were live, among them every plate on the
Features index (`../<slug>/` on /features/ is /<slug>/). This resolves each
href and src in the build the way a browser would and fails on a miss.

Skipped on purpose: external links (`just links` owns those), fragments (a
bare `#id` stays on the page; `/#demo/...` is a script route on the front
page), and the demo panes under /demo/fork/ and /demo/fleet/, which are
somebody else's bundle, built in the deploy and not here.
"""
from __future__ import annotations

import argparse
import html.parser
import pathlib
import sys
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "starlight" / "dist"
ORIGIN = "https://turingpi.xyz"
NOT_BUILT_HERE = ("/demo/fork/", "/demo/fleet/")


class Refs(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs: list[str] = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in ("href", "src") and value:
                self.refs.append(value)


def page_url(f: pathlib.Path, site: pathlib.Path = SITE) -> str:
    rel = f.relative_to(site).as_posix()
    return "/" + rel.removesuffix("index.html")


def exists(path: str, site: pathlib.Path = SITE) -> bool:
    target = site / path.lstrip("/")
    if path.endswith("/"):
        return (target / "index.html").is_file()
    return target.is_file() or (target / "index.html").is_file()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--site", default=str(SITE),
                    help="the built site to read (default: starlight/dist)")
    ap.add_argument("--known-missing", action="append", default=[], metavar="PATH",
                    help="a target this build is known not to have yet; it is "
                         "not reported, and the run FAILS once it exists, so "
                         "the exception cannot outlive the fault")
    args = ap.parse_args()
    site = pathlib.Path(args.site).resolve()
    if not site.is_dir():
        name = site.relative_to(ROOT).as_posix() if site.is_relative_to(ROOT) else str(site)
        build = "just build" if site == SITE else "just site-build"
        print(f"internal-links: no {name}/ -- run `{build}` first", file=sys.stderr)
        return 1
    checked, bad, known_hits = 0, [], set()
    for f in sorted(site.rglob("*.html")):
        # The 404 page is served at any depth, so it has no depth to resolve
        # against; the demo bundles are not ours to judge.
        url = page_url(f, site)
        if f.name == "404.html" or url.startswith(("/demo/fork/", "/demo/fleet/")):
            continue
        p = Refs()
        p.feed(f.read_text(errors="replace"))
        for ref in p.refs:
            ref = ref.removeprefix(ORIGIN) if ref.startswith(ORIGIN) else ref
            if ref.startswith("//") or urllib.parse.urlsplit(ref).scheme:
                continue
            path = urllib.parse.urlsplit(urllib.parse.urljoin(url, ref)).path
            if not path or path.startswith(NOT_BUILT_HERE):
                continue
            checked += 1
            if not exists(urllib.parse.unquote(path), site):
                if path in args.known_missing:
                    known_hits.add(path)
                    checked -= 1
                    continue
                bad.append(f"{url}  ->  {ref}  ({path})")
    for line in sorted(set(bad)):
        print(f"internal-links: 404: {line}", file=sys.stderr)
    # An exception that matched nothing is stale: the target was built, or
    # nothing links it any more. Either way its line must go.
    stale = sorted(set(args.known_missing) - known_hits)
    for path in stale:
        print(f"internal-links: --known-missing {path} is not missing (or not "
              f"linked) any more: drop the exception", file=sys.stderr)
    if bad:
        print(f"internal-links: {len(set(bad))} broken of {checked} internal links", file=sys.stderr)
        return 1
    if stale:
        return 1
    if known_hits:
        print(f"internal-links: known missing, by exception: {', '.join(sorted(known_hits))}")
    print(f"internal-links: ok ({checked} internal links resolve)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
