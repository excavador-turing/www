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

    just urls
    scripts/served-urls.py [--site site/dist]
"""
from __future__ import annotations

import argparse
import html.parser
import json
import pathlib
import sys

from sitepage import ROOT, SITE

LIST = SITE / "served-urls.json"


class Ids(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids: set[str] = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])


# What Astro writes at a redirected address. Not any meta refresh: /demo/ is
# a page of its own that sends a reader on to the front page's demo.
REDIRECT = "<title>Redirecting to: "


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--site", default=str(SITE / "dist"),
                    help="the built site to judge (default: site/dist)")
    site = pathlib.Path(ap.parse_args().site)
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

    lost: list[str] = []
    anchors = redirected = 0
    for url, ids in pages.items():
        f = site / url.lstrip("/") / "index.html"
        if not f.is_file():
            lost.append(f"page {url}")
            continue
        text = f.read_text(errors="replace")
        if REDIRECT in text:
            redirected += 1
            continue
        p = Ids()
        p.feed(text)
        anchors += len(ids)
        lost += [f"anchor {url}#{i}" for i in ids if i not in p.ids]
    lost += [f"file {path}" for path in files if not (site / path.lstrip("/")).is_file()]

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
