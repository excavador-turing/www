#!/usr/bin/env python3
"""Prove every page is a couple of clicks from the front page.

The selling pages hide the sidebar so the layout can use the full width, and
before the tabs and the footer existed that left them with no way onward but
the cards on the page. The changelog was three clicks from the front page --
Documentation, then the guides index, then a line in a reference list -- and a
returning reader looking for what changed went through the documentation hub
to find it. The tabs and the footer were added to fix that, and this is the
check that keeps it fixed: a page added to the nav that nobody linked from
anywhere near the front is a page that has quietly gone three clicks deep
again.

    just reach

A breadth-first walk over the BUILT site's internal links, starting at
index.html, counting clicks. Every page in the nav must be within two; the
changelog and the roadmap within one, because they are what a returning
reader comes back for.
"""
from __future__ import annotations

import collections
import html.parser
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

# Reachable in one click from the front page, by decision: the two pages a
# reader who already runs this firmware comes back for.
ONE_CLICK = {"changelog/", "roadmap/"}
MAX_CLICKS = 2


class Links(html.parser.HTMLParser):
    """Every href a READER can click.

    Not every href in the file. Material renders the whole sidebar nav into
    every page, and on the pages that hide it -- the front page, Features,
    About, each feature page -- the sidebar is still in the DOM under an
    element carrying `hidden`. The first version of this walk followed those
    and reported all 55 nav pages one click from the front, which was true
    of the markup and false of the site. A link under a hidden ancestor is
    not a click a reader can make.
    """

    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "source", "track", "wbr"}

    def __init__(self):
        super().__init__()
        self.hrefs: list[str] = []
        self._hidden: list[str] = []      # open tags with a hidden ancestor
        self._depth: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in self.VOID:
            return
        self._depth.append(tag)
        if "hidden" in a or self._hidden:
            self._hidden.append(tag)
        if tag == "a" and a.get("href") and not self._hidden:
            self.hrefs.append(a["href"])

    def handle_endtag(self, tag):
        # Pop to the matching open tag; HTML in the wild closes out of order.
        for i in range(len(self._depth) - 1, -1, -1):
            if self._depth[i] == tag:
                closed = len(self._depth) - i
                del self._depth[i:]
                if self._hidden:
                    del self._hidden[-closed:]
                break


def page_of(href: str, here: str) -> str | None:
    """A site-relative page path for an internal href, or None."""
    if href.startswith(("http://", "https://", "mailto:", "#", "javascript:")):
        return None
    href = href.split("#", 1)[0].split("?", 1)[0]
    if not href:
        return None
    base = pathlib.PurePosixPath("/" + here).parent
    target = (base / href) if not href.startswith("/") else pathlib.PurePosixPath(href)
    parts: list[str] = []
    for part in target.parts:
        if part in ("/", "."):
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    path = "/".join(parts)
    if path.endswith(".html"):
        path = path[:-len("index.html")] if path.endswith("index.html") else path
    elif path and not path.endswith("/"):
        path += "/"
    return path


def nav_pages() -> list[str]:
    cfg = yaml.safe_load(
        (ROOT / "mkdocs.yml").read_text().replace("!!python/name:", ""))
    out: list[str] = []

    def walk(node):
        if isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
        elif isinstance(node, str):
            p = node[:-3] if node.endswith(".md") else node
            p = "" if p == "index" else (p[:-len("/index")] + "/" if p.endswith("/index") else p + "/")
            out.append(p)

    walk(cfg["nav"])
    return out


def main() -> int:
    if not (SITE / "index.html").exists():
        print("no build in site/ -- run `just build` first", file=sys.stderr)
        return 1

    clicks: dict[str, int] = {"": 0}
    queue = collections.deque([""])
    while queue:
        here = queue.popleft()
        f = SITE / here / "index.html"
        if not f.exists():
            continue
        parser = Links()
        parser.feed(f.read_text(errors="replace"))
        for href in parser.hrefs:
            there = page_of(href, here + "index.html")
            if there is None or there in clicks:
                continue
            if not (SITE / there / "index.html").exists():
                continue
            clicks[there] = clicks[here] + 1
            queue.append(there)

    problems = []
    for page in nav_pages():
        d = clicks.get(page)
        limit = 1 if page in ONE_CLICK else MAX_CLICKS
        if d is None:
            problems.append(f"{page or '/'}: not reachable from the front page at all")
        elif d > limit:
            problems.append(f"{page or '/'}: {d} clicks from the front page, "
                            f"allowed {limit}")

    if problems:
        print(f"{len(problems)} pages too far from the front page:\n",
              file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        print("\nA page in the nav that nobody links from the front, the "
              "tabs or the footer has gone deep again. Add it where a reader "
              "will meet it.", file=sys.stderr)
        return 1

    deepest = max(clicks[p] for p in nav_pages() if p in clicks)
    print(f"  {len(nav_pages())} nav pages, every one within {deepest} clicks "
          f"of the front page; changelog and roadmap within one")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
