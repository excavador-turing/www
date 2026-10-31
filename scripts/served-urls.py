#!/usr/bin/env python3
"""Every URL turingpi.xyz has served still answers.

The site moved from MkDocs to Starlight on 2026-10-26 under one rule: no URL
changes without a redirect. A link in a forum post, a search result or a
bookmark is a promise the site made. site/served-urls.json is every page
MkDocs served, each with the heading anchors a deep link can name, and every
other file it published, frozen at the switch. This fails when one of them
stops answering:

  a page     the build has its index.html -- the page, or the redirect
             astro.config.mjs writes in its place
  an anchor  that page still carries an element with that id (a redirect
             page carries none, and is not judged on them)
  a file     the build has it

A URL leaves the list one way: into `retired`, with the reason, when nothing
anybody linked to is lost (a theme's own icon, a compressed copy of the
sitemap). Pages added since are not in the list and are not judged.

One kind of anchor is allowed to move, and only that kind: an entry of a
paginated list that a generator writes. The news index lists the posts newest
first, ten to a page, so every release pushes the oldest entry of each page
onto the next one -- /news/#x becomes /news/page/2/#x -- and nobody wrote that
move. `paginated` in the list names such a list by its first page; its
members are that page and /page/2/, /page/3/ ... after it, and an anchor
listed on any of them is served while ANY of them carries it as a heading the
generator marked `data-paginated`. Narrow on purpose:

  - the page itself, and every written anchor on it, is judged as for any
    page: an anchor carried by its own page needs no mark;
  - only a marked heading stands in for one that moved, so a written heading
    on a page of the list cannot be satisfied by another page;
  - a page named in `paginated` whose build carries no marked heading is not
    a generated list, and the gate fails -- the rule cannot swallow a page
    somebody writes by hand.

    just urls
    scripts/served-urls.py [--site site/dist]
    scripts/served-urls.py --self-test
"""
from __future__ import annotations

import argparse
import html.parser
import json
import pathlib
import sys
import tempfile

from sitepage import ROOT, SITE

LIST = SITE / "served-urls.json"


# The attribute a generator puts on each heading of a paginated list (the
# news index: src/components/macros/PostList.astro).
MARK = "data-paginated"


class Ids(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids: set[str] = set()
        # Of those, the ids of headings a generator marked as list entries.
        self.listed: set[str] = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
            if MARK in a:
                self.listed.add(a["id"])


# What Astro writes at a redirected address. Not any meta refresh: /demo/ is
# a page of its own that sends a reader on to the front page's demo.
REDIRECT = "<title>Redirecting to: "


def read(f: pathlib.Path) -> tuple[bool, Ids]:
    """Is the built page a redirect, and which ids does it carry."""
    text = f.read_text(errors="replace")
    p = Ids()
    if REDIRECT in text:
        return True, p
    p.feed(text)
    return False, p


def members(site: pathlib.Path, first: str) -> list[str]:
    """The pages of a paginated list: its first and /page/2/ onward, as built."""
    urls, n = [first], 2
    while (site / first.lstrip("/") / "page" / str(n) / "index.html").is_file():
        urls.append(f"{first}page/{n}/")
        n += 1
    return urls


def judge(site: pathlib.Path, served: dict) -> tuple[list[str], int, int]:
    """What no longer answers in the built site; how many anchors and redirects held."""
    pages, files = served["pages"], served["files"]
    lost: list[str] = []
    anchors = redirected = 0

    # The entries a paginated list marks, wherever the build put them.
    moved: dict[str, set[str]] = {}
    family: dict[str, str] = {}
    for first, why in served.get("paginated", {}).items():
        if not why or not why.strip():
            lost.append(f"paginated {first}: no reason given")
        if first not in pages:
            lost.append(f"paginated {first}: not a page in `pages`")
            continue
        if not first.endswith("/"):
            lost.append(f"paginated {first}: name the first page, with its trailing slash")
            continue
        listed: set[str] = set()
        for url in members(site, first):
            family[url] = first
            _, p = read(site / url.lstrip("/") / "index.html")
            listed |= p.listed
        if not listed:
            lost.append(f"paginated {first}: no heading in the build carries {MARK} -- "
                        f"this is not a generated list, so its anchors are not allowed to move")
        moved[first] = listed

    for url, ids in pages.items():
        f = site / url.lstrip("/") / "index.html"
        if not f.is_file():
            lost.append(f"page {url}")
            continue
        redirect, p = read(f)
        if redirect:
            redirected += 1
            continue
        anchors += len(ids)
        elsewhere = moved.get(family.get(url, ""), set())
        lost += [f"anchor {url}#{i}" for i in ids if i not in p.ids and i not in elsewhere]
    lost += [f"file {path}" for path in files if not (site / path.lstrip("/")).is_file()]
    return lost, anchors, redirected


def self_test() -> int:
    """judge() against a small built site, for each way it must pass or fail."""

    def build(root: pathlib.Path, pages: dict[str, str]) -> None:
        for url, body in pages.items():
            d = root / url.lstrip("/")
            d.mkdir(parents=True, exist_ok=True)
            (d / "index.html").write_text(f"<html><body>{body}</body></html>")

    def h(i: str, marked: bool = False) -> str:
        return f'<h2 id="{i}" {MARK if marked else ""}>x</h2>'

    base = {"files": [], "pages": {"/a/": ["w"], "/n/": ["p1"], "/n/page/2/": ["p2"]},
            "paginated": {"/n/": "newest first, ten to a page"}}
    cases = [
        # (name, built pages, list changes, anchors expected lost)
        ("an entry moved to the next page is still served",
         {"/a/": h("w"), "/n/": h("p2", True), "/n/page/2/": h("p1", True)}, {}, []),
        ("an entry that left the list is lost",
         {"/a/": h("w"), "/n/": h("p1", True), "/n/page/2/": h("other", True)}, {}, ["/n/page/2/#p2"]),
        ("a written heading cannot be stood in for by a marked one elsewhere",
         {"/a/": h("w"), "/n/": h("p1", True) + h("p2", True), "/n/page/2/": h("x", True)},
         {"pages": {"/a/": ["w"], "/n/": ["intro"], "/n/page/2/": []}}, ["/n/#intro"]),
        ("an unmarked heading on another page is not a list entry",
         {"/a/": h("w"), "/n/": h("p1", True) + h("p2"), "/n/page/2/": h("p3", True)}, {}, ["/n/page/2/#p2"]),
        ("a written page cannot be declared paginated",
         {"/a/": h("w"), "/n/": h("p1"), "/n/page/2/": h("p2")}, {}, ["paginated /n/"]),
        ("a page outside the list gets no allowance",
         {"/a/": h("other", True), "/n/": h("p1", True), "/n/page/2/": h("p2", True)}, {}, ["/a/#w"]),
        ("a reason is required",
         {"/a/": h("w"), "/n/": h("p1", True), "/n/page/2/": h("p2", True)},
         {"paginated": {"/n/": " "}}, ["paginated /n/"]),
        ("a list that is not a page is refused",
         {"/a/": h("w"), "/n/": h("p1", True), "/n/page/2/": h("p2", True)},
         {"paginated": {"/zz/": "x"}}, ["paginated /zz/"]),
        ("a lost page stays lost",
         {"/a/": h("w"), "/n/": h("p1", True)}, {}, ["page /n/page/2/"]),
    ]
    bad = 0
    for name, built, change, want in cases:
        with tempfile.TemporaryDirectory() as t:
            root = pathlib.Path(t)
            build(root, built)
            lost, _, _ = judge(root, {**base, **change})
        ok = len(lost) == len(want) and all(any(w in l for l in lost) for w in want)
        if not ok:
            bad += 1
            print(f"  FAIL {name}: wanted {want}, got {lost}", file=sys.stderr)
    if bad:
        print(f"served-urls: {bad} of {len(cases)} self-tests failed", file=sys.stderr)
        return 1
    print(f"  served-urls: {len(cases)} self-tests pass")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--site", default=str(SITE / "dist"),
                    help="the built site to judge (default: site/dist)")
    ap.add_argument("--self-test", action="store_true",
                    help="test the judge on a small site written for the purpose; no build needed")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    site = pathlib.Path(args.site)
    if not (site / "index.html").is_file():
        print(f"served-urls: no build in {site} -- run `just build` first", file=sys.stderr)
        return 1
    served = json.loads(LIST.read_text())
    pages, files = served["pages"], served["files"]
    # A list that names nothing must not pass for a site that lost nothing.
    if len(pages) < 50 or not files:
        print(f"served-urls: {LIST.relative_to(ROOT)} names {len(pages)} pages and "
              f"{len(files)} files -- refusing to pass", file=sys.stderr)
        return 1

    lost, anchors, redirected = judge(site, served)
    if lost:
        print(f"served-urls: {len(lost)} URLs turingpi.xyz served no longer answer "
              f"in {site}:", file=sys.stderr)
        for l in lost:
            print(f"  {l}", file=sys.stderr)
        print("Put a redirect in astro.config.mjs, or -- if nothing anybody "
              "linked to is lost -- move the URL to `retired` in "
              f"{LIST.relative_to(ROOT)} with the reason.", file=sys.stderr)
        return 1
    print(f"  {len(pages)} pages ({redirected} redirected), {anchors} anchors and "
          f"{len(files)} files MkDocs served all answer in {site}; "
          f"{len(served['retired'])} retired with a reason")
    return 0


if __name__ == "__main__":
    sys.exit(main())
