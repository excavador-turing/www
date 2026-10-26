"""Where the site's sources live, and the shapes a generator writes them in.

The generators -- refresh-changelog, refresh-roadmap, the API pages, the
gate's record -- write pages Starlight reads as they are: front matter with
the page's title and URL, links rooted at the site, a collapsed block as
`<details>`, an aside as `:::note[...]`. The forms are here once, so every
generated page is the same shape as every written one.
"""
from __future__ import annotations

import html
import pathlib

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
# One page per file, at the path that is its URL: changelog/bmcd.md is
# /changelog/bmcd/.
CONTENT = SITE / "src" / "content" / "docs"
# What the components read when the site is built; also served at /data/.
DATA = SITE / "src" / "data"
# Served as it is: pictures, the feed, robots.txt.
PUBLIC = SITE / "public"


def front(fm: dict) -> str:
    """YAML front matter, keys in the order given."""
    return "---\n" + yaml.safe_dump(fm, sort_keys=False, allow_unicode=True,
                                    width=10_000) + "---\n"


def page(fm: dict, body: str | list[str]) -> str:
    """A whole page: front matter, a blank line, the body."""
    if isinstance(body, list):
        body = "\n".join(body)
    return front(fm) + "\n" + body.strip("\n") + "\n"


def details(title: str, body: list[str], *, opened: bool = False,
            indent: str = "") -> list[str]:
    """A collapsed block, open when `opened`. The blank lines around the body
    are what lets Markdown inside it render as Markdown; blank lines the body
    ends with go after the block, where they separate it from the next."""
    trailing = len(body) - len("\n".join(body).rstrip("\n ").split("\n")) if body else 0
    body = body[:len(body) - trailing]
    return ([f'{indent}<details class="note"{" open" if opened else ""}>',
             f"{indent}<summary>{html.escape(title, quote=False)}</summary>", ""]
            + [indent + l if l.strip() else "" for l in body]
            + ["", f"{indent}</details>"] + [""] * trailing)


def aside(kind: str, title: str, body: list[str]) -> list[str]:
    """A Starlight aside: note, tip, caution or danger, with its own label."""
    return [f":::{kind}[{title}]", *body, ":::"]
