#!/usr/bin/env python3
"""Every page says what it is for, in one line of its own.

A page's `<meta name="description">` comes from its front matter, and falls
back to the site's own description when there is none. On 2026-09-21 not one of
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
    scripts/description-lint.py --site site/dist   # and what was built

`--site` adds a second pass over a BUILT site: every page's
`<meta name="description">` is the one its source asks for, whole, and the
Open Graph and Twitter copies agree with it. The source rules cannot see the
template that writes the attribute -- and until 2026-10-26 MkDocs's template
cut two release posts short at an unescaped `"` (`/news/v2.39.0/`,
`/news/v2.9.2/`), with every source description passing.
"""
from __future__ import annotations

import argparse
import html.parser
import pathlib
import sys

import yaml

import json

from sitepage import CONTENT, ROOT, SITE

# Roughly where a result snippet is cut. Longer is not wrong, it is just not
# read -- and a description that ends mid-word reads as neglect.
LIMIT = 160

# Below this a description is a label, not a sentence, and says nothing a
# title did not.
FLOOR = 40


def site_description() -> str:
    """The tagline every page used to repeat."""
    return json.loads((SITE / "src" / "config" / "site.json").read_text())["description"]


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


def url_of(fm: dict) -> str:
    """The directory URL a page is served at: its slug."""
    slug = str(fm.get("slug", ""))
    return "/" if slug == "index" else f"/{slug}/"


class Meta(html.parser.HTMLParser):
    """The description tags of one built page, entities decoded."""

    KEYS = ("description", "og:description", "twitter:description")

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.found: dict[str, list[str]] = {k: [] for k in self.KEYS}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        key = a.get("name") or a.get("property")
        if tag == "meta" and key in self.KEYS:
            self.found[key].append(a.get("content") or "")


def built_faults(site: pathlib.Path, wanted: dict[str, str],
                 tagline: str) -> tuple[int, list[str]]:
    """Every built page against the description its source asks for."""
    faults: list[str] = []
    built = sorted(f for f in site.rglob("index.html")
                   if not f.relative_to(site).as_posix().startswith(
                       ("_astro/", "pagefind/", "demo/fork/", "demo/fleet/",
                        "demo/stock/")))
    seen = set()
    for f in built + [site / "404.html"]:
        if not f.is_file():
            continue
        rel = f.relative_to(site).as_posix()
        url = "/" + rel.removesuffix("index.html")
        seen.add(url)
        m = Meta()
        m.feed(f.read_text(errors="replace"))
        descs = m.found["description"]
        if len(descs) != 1:
            faults.append(f"{url}: {len(descs)} <meta name=description> tags, "
                          f"not one")
            continue
        desc = descs[0]
        if url in wanted and desc != wanted[url]:
            faults.append(f"{url}: built description is not the source's -- "
                          f"built {desc!r}, source {wanted[url]!r}")
        elif desc == tagline:
            faults.append(f"{url}: repeats site_description")
        elif not FLOOR <= len(desc) <= LIMIT:
            faults.append(f"{url}: {len(desc)} characters, outside "
                          f"{FLOOR}..{LIMIT}")
        for key in ("og:description", "twitter:description"):
            if m.found[key] and m.found[key] != [desc]:
                faults.append(f"{url}: {key} {m.found[key]!r} is not the "
                              f"description")
    for url in sorted(set(wanted) - seen):
        faults.append(f"{url}: a source page with no built page")
    return len(seen), faults


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--site", help="also check the descriptions a built "
                    "site carries (e.g. site/dist)")
    args = ap.parse_args()
    tagline = site_description()
    pages = sorted(CONTENT.rglob("*.md*"))
    faults: list[str] = []

    wanted: dict[str, str] = {}
    for page in pages:
        rel = page.relative_to(ROOT)
        fm = front_matter(page)
        desc = (fm.get("description") or "").strip()
        if desc:
            wanted[url_of(fm)] = desc
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
        print(f"description-lint: no pages found under {CONTENT.relative_to(ROOT)} "
              "-- refusing to pass", file=sys.stderr)
        return 1

    if faults:
        print(f"description-lint: {len(faults)} of {len(pages)} pages",
              file=sys.stderr)
        for f in faults:
            print(f"  {f}", file=sys.stderr)
        return 1

    print(f"  {len(pages)} pages, every one with its own description")

    if args.site:
        site = pathlib.Path(args.site)
        if not (site / "index.html").is_file():
            print(f"description-lint: no build in {site} -- build it first",
                  file=sys.stderr)
            return 1
        n, built = built_faults(site, wanted, tagline)
        if built:
            print(f"description-lint: {len(built)} faults in {n} built pages "
                  f"of {site}", file=sys.stderr)
            for f in built:
                print(f"  {f}", file=sys.stderr)
            return 1
        print(f"  {n} built pages in {site}: each carries its source's "
              f"description whole, and Open Graph and Twitter agree")
    return 0


if __name__ == "__main__":
    sys.exit(main())
