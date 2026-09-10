#!/usr/bin/env python3
"""Build the changelog pages from GitHub release notes.

The site had no history at all while four repositories carried 64 releases
between them. Anyone asking "what changed in v2.20.0" had to leave the site.

Release notes are written once, at release time, in the repository that
produced the thing. Copying them here by hand would mean writing them twice
and having them disagree by the third release. So this fetches them and the
result is committed, for the same reason the OpenAPI document is committed:
the site builds offline and reproducibly, and a change to the history arrives
as a reviewable diff rather than appearing silently the next time CI runs.

Usage:  ./scripts/refresh-changelog.py            # every component
        ./scripts/refresh-changelog.py bmcd       # just one
"""

from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUTDIR = ROOT / "docs" / "changelog"
ORG = "excavador-turing"

# Ordered as a reader meets them: the thing you flash, then what runs on it,
# then what you look at, then what you type.
COMPONENTS: list[tuple[str, str, str]] = [
    ("firmware", "BMC-Firmware", "The firmware image — what you flash onto the board."),
    ("bmcd", "bmcd", "The daemon: the API, the update logic, the metrics."),
    ("bmc-ui", "BMC-UI", "The web interface the board serves."),
    ("tpi", "tpi", "The command-line client."),
]

# Release notes are Markdown written for GitHub, where the page has no
# heading above them. Here they sit under an H2 per release, so their own
# headings have to move down or they break the page's outline -- and with it
# the table of contents that makes this page navigable at all.
HEADING = re.compile(r"^(#{1,4})(\s+)", re.MULTILINE)


def demote(body: str, by: int = 2) -> str:
    def sub(m: re.Match) -> str:
        return "#" * min(len(m.group(1)) + by, 6) + m.group(2)

    return HEADING.sub(sub, body)


def releases(repo: str) -> list[dict]:
    out = subprocess.run(
        ["gh", "release", "list", "--repo", f"{ORG}/{repo}", "--limit", "200",
         "--json", "tagName,name,publishedAt,isPrerelease,isDraft"],
        capture_output=True, text=True, check=True,
    ).stdout
    rels = [r for r in json.loads(out) if not r.get("isDraft")]
    rels.sort(key=lambda r: r.get("publishedAt") or "", reverse=True)
    return rels


def body_of(repo: str, tag: str) -> str:
    out = subprocess.run(
        ["gh", "release", "view", tag, "--repo", f"{ORG}/{repo}", "--json", "body"],
        capture_output=True, text=True, check=True,
    ).stdout
    return (json.loads(out).get("body") or "").strip()


def human_date(iso: str) -> str:
    if not iso:
        return "—"
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%d %B %Y")


def render(slug: str, repo: str, blurb: str) -> tuple[pathlib.Path, int, str]:
    rels = releases(repo)
    newest = rels[0]["tagName"] if rels else "—"

    lines = [
        f"# {repo}",
        "",
        blurb,
        "",
        f"Newest release **{newest}**, {len(rels)} in total. Every entry is the "
        f"release note as published on "
        f"[GitHub](https://github.com/{ORG}/{repo}/releases), fetched by "
        "`just refresh-changelog` — not written here, so the two cannot disagree.",
        "",
    ]

    # The newest release is open; the rest are collapsed. A page that expands
    # 24 releases at once is the API reference's old mistake in another costume.
    for i, r in enumerate(rels):
        tag = r["tagName"]
        title = f"{tag} — {human_date(r.get('publishedAt'))}"
        if r.get("isPrerelease"):
            title += " (pre-release)"
        body = demote(body_of(repo, tag)) or "_No release note._"
        marker = "???+" if i == 0 else "???"
        lines.append(f'{marker} note "{title}"')
        lines.append("")
        for ln in body.splitlines():
            lines.append(("    " + ln) if ln.strip() else "")
        lines.append("")

    page = OUTDIR / f"{slug}.md"
    page.write_text("\n".join(lines).rstrip() + "\n")
    return page, len(rels), newest


def main(argv: list[str]) -> int:
    wanted = set(argv[1:])
    chosen = [c for c in COMPONENTS if not wanted or c[0] in wanted or c[1] in wanted]
    if not chosen:
        print(f"no such component: {', '.join(sorted(wanted))}", file=sys.stderr)
        print(f"known: {', '.join(c[0] for c in COMPONENTS)}", file=sys.stderr)
        return 2

    OUTDIR.mkdir(parents=True, exist_ok=True)
    summary: list[tuple[str, str, int, str]] = []
    for slug, repo, blurb in chosen:
        page, n, newest = render(slug, repo, blurb)
        print(f"  {page.relative_to(ROOT)}: {n} releases, newest {newest}")
        summary.append((slug, repo, n, newest))

    # Only rewrite the index when every component was refreshed; a partial run
    # would otherwise publish a table that silently disagrees with the pages.
    if not wanted:
        idx = [
            "# Changelog",
            "",
            "What changed, per component, taken from the release notes themselves.",
            "",
            "| component | newest | releases | notes |",
            "|---|---|---|---|",
        ]
        for slug, repo, n, newest in summary:
            idx.append(f"| [{repo}]({slug}.md) | `{newest}` | {n} | "
                       f"[GitHub](https://github.com/{ORG}/{repo}/releases) |")
        idx += [
            "",
            "These four version together. The firmware image carries a `bmcd`, a "
            "`BMC-UI` and a `tpi`, and the board's About tab names all four — so "
            "a firmware version is the one to quote when reporting anything.",
            "",
            f"Refreshed {datetime.now(timezone.utc).strftime('%d %B %Y')} by "
            "`just refresh-changelog`.",
        ]
        (OUTDIR / "index.md").write_text("\n".join(idx) + "\n")
        print(f"  {(OUTDIR / 'index.md').relative_to(ROOT)}")
    else:
        print("  (index left alone: partial refresh)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
