#!/usr/bin/env python3
"""One file that tells a machine what this site holds, and in what order.

An assistant asked about this firmware does not read a nav. It fetches a page
or two and answers from them, and which two it picks decides whether the
answer is right. `llms.txt` is the convention for saying so: a title, one
paragraph, then the links that matter with one line each about what is in
them.

It is generated, for the reason everything else here is generated -- a
hand-kept index of 91 pages is an index that is wrong by the third release.
The nav supplies the order (it is already the order a person is meant to read
in), each page supplies its own one-line description, and
`scripts/description-lint.py` guarantees every page has one.

`llms-full.txt` -- the whole site as one document -- is deliberately NOT
written. These pages are full of components; the markdown on disk is not the
page a reader gets, and pouring built HTML back into markdown would publish a
third version of the text that nobody checks. If an index asks for it, build
it from the built pages, not from the source.

    just llms            # write site/src/data/llms.txt
    just llms --check    # fail if the committed file is stale
    scripts/llms.py --check --site site/dist   # and what a build serves

`--site` (with --check) also judges the file a BUILT site serves: it is
this script's output byte for byte, and every link in it on this site lands
on a built page or file. The Starlight build serves the curated file through
a route of its own, so "the committed file is right" no longer proves "the
served file is right". When the build serves starlight-llms-txt's index
instead (astro.config.mjs `llmsTxt = 'plugin'`, which writes llms-full.txt
beside it) only the links are judged.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

import yaml

from sitepage import CONTENT, DATA, SITE, ROOT

# Served at /llms.txt by src/routes/llms.txt.ts.
OUT = DATA / "llms.txt"
ORG = "excavador-turing"

# The one paragraph. It says what the thing IS and why it exists, because
# that is the question every other page assumes has been answered.
BLURB = (
    "A maintained fork of the Turing Pi 2 BMC firmware — the management "
    "computer on a Turing Pi 2 cluster board, which powers, flashes and "
    "consoles the four compute modules. Upstream's last release is v2.1.0 "
    "(February 2025) and its update mirror stops earlier still. This fork "
    "adds an update that takes itself back when the board does not come "
    "up right, VLANs on the board's own switch, a certificate a browser "
    "accepts, the board's own address from the interface, and metrics "
    "where there were none. Everything on this site was measured on real "
    "boards; every page says where and when."
)

# Not everything in the nav is a page an assistant should read. The demo is
# an application shell whose text is one board's captured data.
SKIP = {"/demo/"}


def config(name: str):
    return json.loads((SITE / "src" / "config" / name).read_text())


def site_url() -> str:
    return config("site.json")["site"].rstrip("/")


def nav() -> list:
    return config("sidebar.json")


def front_matter(path: pathlib.Path) -> dict:
    text = path.read_text()
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    try:
        return yaml.safe_load(text[3:end]) or {}
    except yaml.YAMLError:
        return {}


_pages: dict[str, dict] | None = None


def page_at(url: str) -> dict:
    """The front matter of the page served at a site path, by its slug."""
    global _pages
    if _pages is None:
        _pages = {}
        for p in CONTENT.rglob("*.md*"):
            fm = front_matter(p)
            slug = str(fm.get("slug", ""))
            _pages["/" if slug == "index" else f"/{slug}/"] = fm
    return _pages.get(url, {})


def walk(items: list, out: list[tuple[str, str, str]], group: str = "") -> None:
    """Flatten a sidebar subtree into (group, label, link), keeping its order.

    `group` is the nearest sub-heading inside the section -- "The arguments",
    "Reference", "Changelogs". Eleven feature pages and eleven argument pages
    share their titles, so without it the list reads as the same page twice.
    """
    for item in items:
        if "items" in item:
            walk(item["items"], out, item["label"])
        else:
            out.append((group, item["label"], item["link"]))


def recent_posts(base: str, limit: int = 10) -> list[str]:
    posts = []
    for p in (CONTENT / "news").glob("*.md"):
        fm = front_matter(p)
        if fm.get("date") and fm.get("slug"):
            posts.append((str(fm["date"]), fm["slug"], fm.get("title", ""),
                          fm.get("description", "")))
    posts.sort(reverse=True)
    return [f"- [{t}]({base}/{slug}/): {d}"
            for _when, slug, t, d in posts[:limit]]


def render() -> str:
    base = site_url()
    lines = [
        "# Turing Pi 2 BMC firmware (excavador-turing fork)",
        "",
        f"> {BLURB}",
        "",
        "Generated by `scripts/llms.py` from the site's own navigation and "
        "each page's description. Do not edit.",
        "",
    ]
    counted = 0
    for section in nav():
        heading = section["label"]
        pairs: list[tuple[str, str, str]] = []
        walk(section.get("items") or [section], pairs)
        rows, seen_urls = [], set()
        for group, title, link in pairs:
            if link in SKIP or not link.startswith("/"):
                continue
            fm = page_at(link)
            if ((fm.get("tp") or {}).get("robots") or "").startswith("noindex"):
                continue
            url = base + link
            # Two sources can claim one URL (a page and a directory index of
            # the same name). The nav shows both; an index must not.
            if url in seen_urls:
                continue
            seen_urls.add(url)
            desc = (fm.get("description") or "").strip()
            name = title or fm.get("title") or link
            if group and group != heading:
                name = f"{group}: {name}"
            rows.append(f"- [{name}]({url}): {desc}")
            counted += 1
        if heading == "News":
            rows += recent_posts(base)
            counted += len(rows) - 1
        if rows:
            lines += [f"## {heading}", ""] + rows + [""]

    lines += [
        "## Optional",
        "",
        "Sources this site is generated from, when the page is not enough.",
        "",
        f"- [Firmware CHANGELOG.md](https://raw.githubusercontent.com/{ORG}/"
        "BMC-Firmware/hive/CHANGELOG.md): every release of the image, with "
        "what it pins.",
        f"- [bmcd CHANGELOG.md](https://raw.githubusercontent.com/{ORG}/"
        "bmcd/hive/CHANGELOG.md): the daemon that serves the API.",
        f"- [BMC-UI CHANGELOG.md](https://raw.githubusercontent.com/{ORG}/"
        "BMC-UI/hive/CHANGELOG.md): the web interface and the fleet page.",
        f"- [tpi CHANGELOG.md](https://raw.githubusercontent.com/{ORG}/"
        "tpi/hive/CHANGELOG.md): the command line.",
        f"- [openapi.json]({base}/reference/openapi.json): the API as the "
        "board itself describes it.",
        f"- [feed.xml]({base}/feed.xml): new releases, as an Atom feed.",
        "",
    ]
    if counted < 20:
        sys.exit(f"llms: only {counted} pages found in the nav — refusing to "
                 f"write an index that thin")
    print(f"  {counted} entries from the nav")
    return "\n".join(lines)


def check_served(site: pathlib.Path, text: str) -> int:
    """The llms.txt a built site serves is this one, and its links land."""
    served = site / "llms.txt"
    if not served.is_file():
        print(f"llms: {site} serves no llms.txt", file=sys.stderr)
        return 1
    body = served.read_text()
    plugin = (site / "llms-full.txt").is_file()
    if not plugin and body != text:
        print(f"llms: {served} is not what scripts/llms.py writes",
              file=sys.stderr)
        return 1
    base = site_url()
    links = re.findall(r"\]\((" + re.escape(base) + r"/[^)\s]*)\)", body)
    missing = []
    for url in links:
        path = url[len(base):].split("#", 1)[0]
        target = site / path.lstrip("/")
        if not (target.is_file() or (target / "index.html").is_file()):
            missing.append(url)
    if not links:
        print(f"llms: no links to {base} in {served} -- refusing to pass",
              file=sys.stderr)
        return 1
    if missing:
        print(f"llms: {len(missing)} of {len(links)} links in {served} land "
              f"on nothing in the build:", file=sys.stderr)
        for url in missing:
            print(f"  {url}", file=sys.stderr)
        return 1
    mode = "starlight-llms-txt's" if plugin else "the curated one, byte for byte"
    print(f"  {served} is {mode}; all {len(links)} links on this site land")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="fail if the committed file is not what this writes")
    ap.add_argument("--site", help="with --check: also judge the llms.txt "
                    "this built site serves (e.g. site/dist)")
    args = ap.parse_args()
    if args.site and not args.check:
        ap.error("--site needs --check")
    text = render()
    if args.check:
        if not OUT.exists() or OUT.read_text() != text:
            print(f"llms: {OUT.relative_to(ROOT)} is stale — run `just llms`",
                  file=sys.stderr)
            return 1
        print(f"  {OUT.relative_to(ROOT)} matches the nav")
        if args.site:
            return check_served(pathlib.Path(args.site), text)
        return 0
    OUT.write_text(text)
    print(f"  -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
