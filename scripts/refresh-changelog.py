#!/usr/bin/env python3
"""Build the changelog pages from each repository's CHANGELOG.md.

This used to read the GitHub release notes, and those say nothing. Every
firmware release note is the same fixed paragraph: v2.28.0 and v2.32.0, four
days and fourteen entries apart, published byte-identical bodies. So the page
a returning reader comes to for "what changed" carried twenty-eight copies of
how to run sha256sum.

Meanwhile every one of the four repositories keeps a real CHANGELOG.md in
Keep a Changelog form -- 40 KB of it for the firmware -- with Added, Changed
and Fixed per release and, for the firmware, what each release pins. That is
the source. (BMC-Firmware's release notes are composed from the same file
now, so the two agree by construction rather than by luck.)

Usage:  ./scripts/refresh-changelog.py            # every component
        ./scripts/refresh-changelog.py bmcd       # just one
        ./scripts/refresh-changelog.py --check    # fail if a page is stale

The result is committed, for the same reason the OpenAPI document is: the
site builds offline and reproducibly, and a change to the history arrives as
a reviewable diff instead of appearing the next time CI runs. The hourly
Pages job runs this and commits when it differs, so a release reaches the
site without anybody remembering.
"""
from __future__ import annotations

import argparse
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
    ("firmware", "BMC-Firmware",
     "The firmware image — what you flash onto the board. It carries a "
     "`bmcd`, a `BMC-UI` and a `tpi`, so this is the version to quote when "
     "reporting anything."),
    ("bmcd", "bmcd", "The daemon: the API, the update logic, the metrics."),
    ("bmc-ui", "BMC-UI", "The web interface the board serves."),
    ("tpi", "tpi", "The command-line client."),
]

# `## [v2.32.0] — 2026-09-13`, `## [2.36.3] — 2026-09-12`, `## [Unreleased]`.
# The repositories spell the version with and without its v and use an em
# dash or a hyphen, so the heading is matched loosely and normalised here.
RELEASE = re.compile(
    r"^##\s*\[(?P<ver>[^\]]+)\]\s*(?:[—–-]\s*(?P<date>\d{4}-\d{2}-\d{2}))?\s*$",
    re.M)

# Keep a Changelog's categories -- Added, Changed, Fixed, Removed -- are H3
# in the source. Demoting them put an H5 inside a collapsed block, which
# Material renders smaller than the body text under it, and which would put
# "Added" into the page's table of contents twenty-nine times. They are
# labels, so they become labels.
CATEGORY = re.compile(r"^###\s+(Added|Changed|Fixed|Removed|Deprecated|"
                      r"Security)\s*$", re.M)
HEADING = re.compile(r"^(#{1,4})(\s+)", re.M)


def demote(body: str, by: int = 2) -> str:
    body = CATEGORY.sub(lambda m: "**" + m.group(1) + "**\n", body)
    return HEADING.sub(
        lambda m: "#" * min(len(m.group(1)) + by, 6) + m.group(2), body)


def gh(*args: str) -> str:
    return subprocess.run(["gh", *args], capture_output=True, text=True,
                          check=True).stdout


def default_branch(repo: str) -> str:
    return json.loads(gh("api", f"repos/{ORG}/{repo}"))["default_branch"]


def changelog_of(repo: str) -> str:
    return gh("api", "-H", "Accept: application/vnd.github.raw",
              f"repos/{ORG}/{repo}/contents/CHANGELOG.md")


def released(repo: str) -> dict[str, dict]:
    """Published releases by bare version, so the page can say what shipped."""
    out = json.loads(gh("release", "list", "--repo", f"{ORG}/{repo}",
                        "--limit", "300", "--json",
                        "tagName,publishedAt,isPrerelease,isDraft"))
    return {r["tagName"].lstrip("v"): r for r in out if not r.get("isDraft")}


def sections(text: str) -> list[dict]:
    """Split a CHANGELOG into its release sections, newest first."""
    marks = list(RELEASE.finditer(text))
    out = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        body = text[m.end():end].strip()
        # Keep a Changelog puts link definitions at the foot; they are not
        # part of the last release's notes.
        body = re.sub(r"\n\[[^\]]+\]:\s*\S+(?=\n|$)", "", body).strip()
        ver = m.group("ver").strip()
        out.append({"version": ver,
                    "bare": ver.lstrip("v"),
                    "unreleased": ver.lower().startswith("unreleased"),
                    "date": m.group("date"),
                    "body": body})
    return out


def human(iso: str | None) -> str:
    if not iso:
        return "—"
    d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return d.strftime("%-d %B %Y")


def body_of(repo: str, tag: str) -> str:
    out = json.loads(gh("release", "view", tag, "--repo", f"{ORG}/{repo}",
                        "--json", "body"))
    return (out.get("body") or "").strip()


def merge(repo: str, entries: list[dict], pub: dict[str, dict]) -> list[dict]:
    """One row per version, from whichever source has something to say.

    Neither source is complete on its own, and choosing one would lose real
    history either way:

      BMC-UI's CHANGELOG.md stops at 3.19.0 while the repository has released
      3.29.0 -- ten releases with no entry. Reading only the changelog would
      have dropped them off the page.

      bmcd's changelog carries 2.36.2, 2.8.0 and three more that never got a
      GitHub release of their own, because a daemon version reaches a board
      inside a firmware image. Reading only the releases would have dropped
      those.

    So: every version either source knows about, the changelog's text where it
    exists, the release note where it does not, and each row says which.
    """
    by_ver = {e["bare"]: dict(e, source="changelog") for e in entries
              if not e["unreleased"]}
    for bare, rel in pub.items():
        if bare in by_ver:
            by_ver[bare]["released"] = rel
            continue
        by_ver[bare] = {
            "version": rel["tagName"], "bare": bare, "unreleased": False,
            "date": (rel.get("publishedAt") or "")[:10] or None,
            "body": demote(body_of(repo, rel["tagName"])),
            "source": "release-note", "released": rel,
        }
    rows = list(by_ver.values())

    def order(r):
        rel = r.get("released") or {}
        return (rel.get("publishedAt") or "")[:10] or r.get("date") or ""

    rows.sort(key=order, reverse=True)
    return rows


def render(slug: str, repo: str, blurb: str) -> dict:
    entries = sections(changelog_of(repo))
    pub = released(repo)

    shipped = merge(repo, entries, pub)
    pending = next((e for e in entries if e["unreleased"] and e["body"]), None)
    newest = next((e for e in shipped if e.get("released")), None)

    # A changelog entry with no release behind it, or a release with no
    # entry, is worth saying out loud rather than papering over.
    missing_release = [e["version"] for e in shipped if not e.get("released")]
    missing_entry = [e["version"] for e in shipped
                     if e["source"] == "release-note"]

    # No table of contents: the page is a list of collapsed releases, and the
    # only headings it has are the ones inside a release body -- so the
    # contents read "Note, Confirmed" and named nothing a reader wanted.
    lines = ["---", "hide:", "  - toc", "---", "",
             f"# {repo}", "", blurb, ""]
    if newest:
        lines += [
            f"Newest release **{newest['version']}**, "
            f"{human((newest.get('released') or {}).get('publishedAt', '')[:10] or newest['date'])}. "
            f"{len(shipped)} in total. Each entry is this repository's own "
            f"[CHANGELOG.md](https://github.com/{ORG}/{repo}/blob/"
            f"{default_branch(repo)}/CHANGELOG.md) where it has one, and the "
            "release note where it does not — fetched by "
            "`just refresh-changelog`, so this page and the repository cannot "
            "disagree.",
            "",
        ]
    if slug == "firmware":
        lines += [
            f"[Every release on GitHub](https://github.com/{ORG}/{repo}/releases) "
            "carries a `.tpu` OTA package, an `.img` recovery image and a "
            "`SHA256SUMS` to check them against. New ones come through "
            "[the feed](../feed.xml).",
            "",
            '!!! note "Checking what you downloaded"',
            "",
            "    ```console",
            "    $ sha256sum -c SHA256SUMS",
            "    ```",
            "",
            "    `SHA256SUMS` lists bare filenames, so run it from the "
            "directory holding the files. Upstream publishes no checksums at "
            "all, on either of its two catalogues — see [upstream vs this "
            "fork](../reference/comparison.md).",
            "",
        ]

    if pending:
        lines += ['???+ note "Unreleased — merged, not yet on a board"', ""]
        lines += ["    " + ln if ln.strip() else ""
                  for ln in demote(pending["body"]).splitlines()]
        lines.append("")

    for i, e in enumerate(shipped):
        rel = e.get("released")
        when = (rel.get("publishedAt", "")[:10] if rel else None) or e["date"]
        title = f"{e['version']} — {human(when)}"
        if rel and rel.get("isPrerelease"):
            title += " (pre-release)"
        if not rel:
            # Normal for the three components that reach a board inside a
            # firmware image, and a gap worth seeing for the firmware itself.
            title += (" (no release of its own)" if slug != "firmware"
                      else " (not released)")
        # The newest is open unless an Unreleased block already took that
        # spot: two open blocks at the top is two things shouting.
        marker = "???+" if (i == 0 and not pending) else "???"
        lines.append(f'{marker} note "{title}"')
        lines.append("")
        body = (demote(e["body"]) if e["source"] == "changelog"
                else e["body"]) or "_No entry._"
        lines += ["    " + ln if ln.strip() else "" for ln in body.splitlines()]
        if e["source"] == "release-note":
            lines += ["", "    *No entry in `CHANGELOG.md` for this release; "
                          "the text above is its release note.*"]
        lines.append("")

    page = OUTDIR / f"{slug}.md"
    page.write_text("\n".join(lines).rstrip() + "\n")
    return {"slug": slug, "repo": repo, "page": page,
            "count": len(shipped),
            "newest": newest["version"] if newest else None,
            "newest_date": newest["date"] if newest else None,
            "unreleased": bool(pending),
            "missing_release": missing_release,
            "missing_entry": missing_entry,
            "entries": shipped}


def write_index(summary: list[dict]) -> pathlib.Path:
    idx = [
        "# Changelog",
        "",
        "What changed in each release, taken from each repository's own "
        "`CHANGELOG.md`.",
        "",
        "| component | newest | when | releases |",
        "|---|---|---|---|",
    ]
    for s in summary:
        idx.append(f"| [{s['repo']}]({s['slug']}.md) | `{s['newest']}` | "
                   f"{human(s['newest_date'])} | {s['count']} |")
    idx += [
        "",
        "These four version together. The firmware image carries a `bmcd`, a "
        "`BMC-UI` and a `tpi`, and the board's About tab names all four — so a "
        "firmware version is the one to quote when reporting anything.",
        "",
        "New firmware releases come through [the feed](../feed.xml). What is "
        "planned rather than done is on the [roadmap](../roadmap.md), ordered "
        "by votes.",
        "",
        f"Refreshed {datetime.now(timezone.utc).strftime('%-d %B %Y')} by "
        "`just refresh-changelog`.",
    ]
    p = OUTDIR / "index.md"
    p.write_text("\n".join(idx) + "\n")
    return p


def write_feed(firmware: dict) -> pathlib.Path:
    """An Atom feed of firmware releases.

    The site had no way to follow it. GitHub serves a releases feed per
    repository and nothing here ever linked one, so the only way to learn a
    release existed was to come back and look -- and the thing you found when
    you did was twenty-eight identical paragraphs.
    """
    def esc(s: str) -> str:
        return (s.replace("&", "&amp;").replace("<", "&lt;")
                 .replace(">", "&gt;").replace('"', "&quot;"))

    site = "https://turingpi.xyz"
    updated = (f"{firmware['newest_date']}T00:00:00Z" if firmware["newest_date"]
               else datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    out = ['<?xml version="1.0" encoding="utf-8"?>',
           '<feed xmlns="http://www.w3.org/2005/Atom">',
           "  <title>Turing Pi 2 BMC firmware releases</title>",
           "  <subtitle>Every release of this fork's firmware, with what "
           "changed in it.</subtitle>",
           f'  <link href="{site}/feed.xml" rel="self"/>',
           f'  <link href="{site}/changelog/firmware/"/>',
           f"  <id>{site}/feed.xml</id>",
           f"  <updated>{updated}</updated>",
           "  <author><name>excavador-turing</name></author>"]
    for e in firmware["entries"][:40]:
        when = f"{e['date']}T00:00:00Z" if e["date"] else updated
        out += ["  <entry>",
                f"    <title>Firmware {esc(e['version'])}</title>",
                f'    <link href="{site}/changelog/firmware/"/>',
                f"    <id>tag:turingpi.xyz,{e['date'] or '1970-01-01'}:"
                f"firmware/{esc(e['bare'])}</id>",
                f"    <updated>{when}</updated>",
                f'    <content type="text">{esc(e["body"])}</content>',
                "  </entry>"]
    out.append("</feed>")
    p = ROOT / "docs" / "feed.xml"
    p.write_text("\n".join(out) + "\n")
    return p


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("components", nargs="*")
    ap.add_argument("--check", action="store_true",
                    help="fail if the committed pages are not what this writes")
    args = ap.parse_args(argv[1:])

    wanted = set(args.components)
    chosen = [c for c in COMPONENTS
              if not wanted or c[0] in wanted or c[1] in wanted]
    if not chosen:
        print(f"no such component: {', '.join(sorted(wanted))}", file=sys.stderr)
        print(f"known: {', '.join(c[0] for c in COMPONENTS)}", file=sys.stderr)
        return 2

    feed = ROOT / "docs" / "feed.xml"
    before = {p: p.read_text() for p in OUTDIR.glob("*.md")}
    if feed.exists():
        before[feed] = feed.read_text()

    OUTDIR.mkdir(parents=True, exist_ok=True)
    summary = []
    for slug, repo, blurb in chosen:
        s = render(slug, repo, blurb)
        summary.append(s)
        print(f"  {s['page'].relative_to(ROOT)}: {s['count']} versions, "
              f"newest {s['newest']}")
        if s["missing_entry"]:
            # Not a failure here -- this page's job is to show what exists --
            # but it is the one place anybody would notice, so say it plainly.
            print(f"      {len(s['missing_entry'])} released with NO entry in "
                  f"CHANGELOG.md, falling back to the release note: "
                  f"{', '.join(s['missing_entry'])}")
        if s["missing_release"]:
            print(f"      {len(s['missing_release'])} in CHANGELOG.md with no "
                  f"release of their own: {', '.join(s['missing_release'])}")

    # Only rewrite the index and the feed on a full run: a partial one would
    # publish a table that silently disagrees with the pages.
    if not wanted:
        print(f"  {write_index(summary).relative_to(ROOT)}")
        fw = next(s for s in summary if s["slug"] == "firmware")
        print(f"  {write_feed(fw).relative_to(ROOT)}: "
              f"{min(len(fw['entries']), 40)} entries")

    if args.check:
        after = {p: p.read_text() for p in OUTDIR.glob("*.md")}
        if feed.exists():
            after[feed] = feed.read_text()
        stale = sorted(p for p in after if before.get(p) != after[p])
        for p, text in before.items():
            p.write_text(text)          # --check writes nothing
        if stale:
            print("\nstale, run `just refresh-changelog` and commit:",
                  file=sys.stderr)
            for p in stale:
                print(f"  {p.relative_to(ROOT)}", file=sys.stderr)
            return 1
        print("  every changelog page matches its repository")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
