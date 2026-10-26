#!/usr/bin/env python3
"""The structured data on every built page is valid, and says what is there.

`overrides/main.html` writes JSON-LD into the head: the front page as a piece
of software with a version, each release post as an article about that
version, the FAQ as its questions, and a breadcrumb everywhere. All of it is
assembled by a template out of page metadata, so a stray quote in a title or
a description breaks the JSON silently -- the page still renders, and the
only sign is that a search engine quietly stops reading it.

This parses what was actually built. It runs after `mkdocs build`, on `site/`.

    just build && just structured-data
    scripts/structured-data.py --site starlight/dist --strict

`--strict` also refuses two faults the MkDocs build ships, which the
Starlight build fixes on purpose: a template left unrendered in the data
(the FAQ's answers carry raw `{{ roadmap.count }}` on turingpi.xyz, because
main.py reads faq.md before the macros render it), and a post's JSON-LD
description that disagrees with the page's own `<meta name="description">`
(two posts are cut at an unescaped `"` in the meta tag). It is off by
default so `just structured-data` judges the MkDocs build as it always has.
"""
from __future__ import annotations

import argparse
import html
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
BLOCK = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
META_DESC = re.compile(r'<meta name="description" content="([^"]*)"')
TEMPLATE = re.compile(r"\{\{|\{%")

# What each kind must carry to be worth emitting at all.
REQUIRED = {
    "SoftwareApplication": ("name", "url", "license", "codeRepository"),
    "BlogPosting": ("headline", "url", "datePublished", "image"),
    "FAQPage": ("mainEntity",),
    "BreadcrumbList": ("itemListElement",),
}


def strings(node):
    """Every string in a JSON document, keys excepted."""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for v in node.values():
            yield from strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from strings(v)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--site", default=str(SITE),
                    help="the built site to read (default: site/, MkDocs's)")
    ap.add_argument("--strict", action="store_true",
                    help="also refuse unrendered templates in the data, and "
                         "a description that disagrees with the meta tag")
    args = ap.parse_args()
    site = pathlib.Path(args.site).resolve()
    name = site.relative_to(ROOT).as_posix() if site.is_relative_to(ROOT) else str(site)
    build = "just build" if site == SITE else "just site-build"
    if not site.exists():
        print(f"structured-data: no {name}/ -- run `{build}` first",
              file=sys.stderr)
        return 1

    pages = sorted(site.rglob("*.html"))
    faults: list[str] = []
    counts: dict[str, int] = {}
    checked = 0

    for page in pages:
        rel = page.relative_to(site)
        text = page.read_text()
        meta = META_DESC.search(text)
        for raw in BLOCK.findall(text):
            checked += 1
            try:
                doc = json.loads(raw)
            except json.JSONDecodeError as exc:
                faults.append(f"{rel}: not JSON ({exc})")
                continue
            kind = doc.get("@type", "")
            counts[kind] = counts.get(kind, 0) + 1
            if doc.get("@context") != "https://schema.org":
                faults.append(f"{rel}: {kind} has no schema.org context")
            for key in REQUIRED.get(kind, ()):
                if not doc.get(key):
                    faults.append(f"{rel}: {kind} is missing {key}")
            # A breadcrumb that does not start at the front page and end at
            # this page is worse than none: it tells a reader of the result
            # that the page lives somewhere it does not.
            if args.strict:
                for s in strings(doc):
                    if TEMPLATE.search(s):
                        faults.append(f"{rel}: {kind} carries an unrendered "
                                      f"template: {s[:80]!r}")
                        break
                # The same sentence twice, once per audience: if they
                # differ, one of them was mangled on the way out.
                if "description" in doc and meta and \
                        doc["description"] != html.unescape(meta.group(1)):
                    faults.append(f"{rel}: {kind} description is not the "
                                  f"meta description")
            if kind == "BreadcrumbList":
                items = doc.get("itemListElement", [])
                if [i.get("position") for i in items] != list(
                        range(1, len(items) + 1)):
                    faults.append(f"{rel}: breadcrumb positions are not 1..n")

    # A sweep that scanned nothing must not pass for a sweep that found
    # nothing wrong.
    if not checked:
        print(f"structured-data: no JSON-LD found in {name}/ -- the head "
              "template is not doing its job", file=sys.stderr)
        return 1

    if faults:
        print(f"structured-data: {len(faults)} faults in {checked} blocks",
              file=sys.stderr)
        for f in faults[:40]:
            print(f"  {f}", file=sys.stderr)
        return 1

    shape = ", ".join(f"{n} {k}" for k, n in sorted(counts.items()))
    print(f"  {checked} JSON-LD blocks across {len(pages)} pages: {shape}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
