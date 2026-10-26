#!/usr/bin/env python3
"""Prove every internal link in the BUILT site lands on a file.

    just links-internal

`mkdocs build --strict` checks Markdown links and nothing else. A link written
as raw HTML -- the cards, the plates, the "next" blocks -- is passed through
untouched and resolved by the BROWSER against the served URL, so one written
for a page at a different depth is a 404 that nothing noticed: 62 of them were
live, among them every plate on the Features index (`../<slug>/` on
/features/ is /<slug>/). This resolves each href and src in site/ the way a
browser would and fails on a miss.

Skipped on purpose: external links (`just links` owns those), fragments (a
bare `#id` stays on the page; `/#demo/...` is a script route on the front
page), and the demo panes under /demo/fork/ and /demo/fleet/, which are
somebody else's bundle, built in the deploy and not here.
"""
from __future__ import annotations

import html.parser
import pathlib
import sys
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
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


def page_url(f: pathlib.Path) -> str:
    rel = f.relative_to(SITE).as_posix()
    return "/" + rel.removesuffix("index.html")


def exists(path: str) -> bool:
    target = SITE / path.lstrip("/")
    if path.endswith("/"):
        return (target / "index.html").is_file()
    return target.is_file() or (target / "index.html").is_file()


def main() -> int:
    if not SITE.is_dir():
        print("internal-links: no site/ -- run `just build` first", file=sys.stderr)
        return 1
    checked, bad = 0, []
    for f in sorted(SITE.rglob("*.html")):
        # The 404 page is served at any depth, so it has no depth to resolve
        # against; the demo bundles are not ours to judge.
        url = page_url(f)
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
            if not exists(urllib.parse.unquote(path)):
                bad.append(f"{url}  ->  {ref}  ({path})")
    for line in sorted(set(bad)):
        print(f"internal-links: 404: {line}", file=sys.stderr)
    if bad:
        print(f"internal-links: {len(set(bad))} broken of {checked} internal links", file=sys.stderr)
        return 1
    print(f"internal-links: ok ({checked} internal links resolve)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
