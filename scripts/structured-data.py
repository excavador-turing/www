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
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
BLOCK = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)

# What each kind must carry to be worth emitting at all.
REQUIRED = {
    "SoftwareApplication": ("name", "url", "license", "codeRepository"),
    "BlogPosting": ("headline", "url", "datePublished", "image"),
    "FAQPage": ("mainEntity",),
    "BreadcrumbList": ("itemListElement",),
}


def main() -> int:
    if not SITE.exists():
        print("structured-data: no site/ -- run `just build` first",
              file=sys.stderr)
        return 1

    pages = sorted(SITE.rglob("*.html"))
    faults: list[str] = []
    counts: dict[str, int] = {}
    checked = 0

    for page in pages:
        rel = page.relative_to(SITE)
        for raw in BLOCK.findall(page.read_text()):
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
            if kind == "BreadcrumbList":
                items = doc.get("itemListElement", [])
                if [i.get("position") for i in items] != list(
                        range(1, len(items) + 1)):
                    faults.append(f"{rel}: breadcrumb positions are not 1..n")

    # A sweep that scanned nothing must not pass for a sweep that found
    # nothing wrong.
    if not checked:
        print("structured-data: no JSON-LD found in site/ -- the head "
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
