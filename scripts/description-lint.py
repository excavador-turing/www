#!/usr/bin/env python3
"""Every page says what it is for, in one line of its own.

Material writes `<meta name="description">` from a page's front matter and
falls back to `site_description` when there is none. On 2026-09-21 not one of
the 91 pages had its own, so every page in the site -- the FAQ, the install
guide, each feature, each release post -- told a search engine, a link preview
and an AI summariser the same sentence: "A fork of the Turing Pi 2 BMC
firmware, and what it changes". True of the site, useless about the page.

A description is not a slogan. It is the sentence a reader sees under the
title in a result and decides on, so it says what the page lets them do or
decide, in the words they searched with.

Generated pages get theirs from their generator (`refresh-changelog.py`,
`refresh-roadmap.py`, `generate-api-pages.py`), so the hourly job keeps them
true. This holds every page -- generated or typed -- to the same three rules,
because a rule that only applies to the pages somebody remembered is not one.

    just description-lint
"""
from __future__ import annotations

import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

# Roughly where a result snippet is cut. Longer is not wrong, it is just not
# read -- and a description that ends mid-word reads as neglect.
LIMIT = 160

# Below this a description is a label, not a sentence, and says nothing a
# title did not.
FLOOR = 40


def site_description() -> str:
    """The tagline every page used to repeat."""
    text = (ROOT / "mkdocs.yml").read_text()
    for line in text.splitlines():
        if line.startswith("site_description:"):
            return line.split(":", 1)[1].strip().strip('"\'')
    return ""


def front_matter(path: pathlib.Path) -> dict:
    text = path.read_text()
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    try:
        return yaml.safe_load(text[3:end]) or {}
    except yaml.YAMLError:
        return {}


def main() -> int:
    tagline = site_description()
    pages = sorted(DOCS.rglob("*.md"))
    faults: list[str] = []

    for page in pages:
        rel = page.relative_to(ROOT)
        desc = (front_matter(page).get("description") or "").strip()
        if not desc:
            faults.append(f"{rel}: no description in the front matter")
        elif desc == tagline:
            faults.append(f"{rel}: repeats site_description; say what THIS "
                          f"page is for")
        elif len(desc) > LIMIT:
            faults.append(f"{rel}: {len(desc)} characters, over {LIMIT} -- "
                          f"a result snippet is cut around there")
        elif len(desc) < FLOOR:
            faults.append(f"{rel}: {len(desc)} characters, under {FLOOR} -- "
                          f"that is a label, not a sentence")

    # A sweep that scanned nothing must not pass for a sweep that found
    # nothing: a moved directory would otherwise turn this check green for
    # the wrong reason.
    if not pages:
        print("description-lint: no pages found under docs/ -- refusing to "
              "pass", file=sys.stderr)
        return 1

    if faults:
        print(f"description-lint: {len(faults)} of {len(pages)} pages",
              file=sys.stderr)
        for f in faults:
            print(f"  {f}", file=sys.stderr)
        return 1

    print(f"  {len(pages)} pages, every one with its own description")
    return 0


if __name__ == "__main__":
    sys.exit(main())
