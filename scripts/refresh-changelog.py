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
NEWS = ROOT / "docs" / "news" / "posts"
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

SLUG_OF = {repo: slug for slug, repo, _ in COMPONENTS}

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
    return {"slug": slug, "repo": repo, "page": page, "blurb": blurb,
            "count": len(shipped),
            "newest": newest["version"] if newest else None,
            "newest_date": newest["date"] if newest else None,
            "unreleased": bool(pending),
            "missing_release": missing_release,
            "missing_entry": missing_entry,
            "entries": shipped}


def write_index(summary: list[dict]) -> pathlib.Path:
    idx = [
        "---",
        "title: Changelogs",
        "hide:",
        "  - toc",
        "---",
        "",
        "# Every component's changelog",
        "",
        "What changed in each release, taken from each repository's own "
        "`CHANGELOG.md`. For the same history as one post per firmware "
        "release, newest first, read [the news](../news/index.md).",
        "",
        '<div class="tp-plates">',
    ]
    for s in summary:
        idx.append(
            f'<a class="tp-plate" href="../{s["slug"]}/"><b>{s["repo"]}</b>'
            f'<span>{s["blurb"]}</span>'
            f'<span class="tp-plate__meta">{s["newest"]} · '
            f'{human(s["newest_date"])} · {s["count"]} releases</span></a>')
    idx += [
        "</div>",
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


# `Pins **bmcd 2.37.0**, **BMC-UI 3.30.0** and **tpi 1.9.0**` -- what a firmware
# release carries, read from its own first paragraph. "bmcd stays at 2.36.3"
# does not match, and is not meant to: a release names what it changed.
PIN = re.compile(r"\b(?P<repo>bmcd|BMC-UI|tpi)\s+\*{0,2}v?(?P<ver>\d+\.\d+\.\d+)")

# What a post says that the changelog cannot: a headline, a summary, and a
# picture. Keyed by firmware tag; every key is optional and a release with no
# entry still gets a post, titled by its version. Written by a person at
# release time, so the hourly job never waits on it.
EDITORIAL = ROOT / "docs" / "data" / "news-editorial.yaml"

CATEGORY_ORDER = ["Added", "Changed", "Fixed", "Removed", "Deprecated",
                  "Security"]
CATEGORY_TITLE = {"Added": "New", "Changed": "Changed", "Fixed": "Fixed",
                  "Removed": "Removed", "Deprecated": "Deprecated",
                  "Security": "Security"}
CAT_HEAD = re.compile(r"^###\s+(Added|Changed|Fixed|Removed|Deprecated|"
                      r"Security)\s*$")
# `- **A renamed board reissues its own certificate.** The generator ...`
ITEM_LEAD = re.compile(r"^\*\*(?P<lead>.+?)\*\*[:.]?\s*", re.S)
# How much of an item the post shows before folding the rest away.
SHORT = 220


def vtuple(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3])


def editorial() -> dict[str, dict]:
    if not EDITORIAL.exists():
        return {}
    import yaml
    data = yaml.safe_load(EDITORIAL.read_text()) or {}
    return {str(k): (v or {}) for k, v in data.items()}


def dedent2(block: str) -> str:
    return "\n".join(ln[2:] if ln.startswith("  ") else ln
                     for ln in block.splitlines())


def parse_entry(body: str) -> tuple[list[str], dict[str, list[dict]]]:
    """A Keep-a-Changelog entry -> (notes before any category, items per category).

    An item is a top-level list entry; the indented paragraphs that follow it
    are its continuation. Anything under a category that is not a list is a
    note and is kept in order with the items.
    """
    notes: list[str] = []
    cats: dict[str, list[dict]] = {}
    cur = None
    for block in re.split(r"\n[ \t]*\n", body):
        b = block.strip("\n")
        if not b.strip():
            continue
        m = CAT_HEAD.match(b.strip())
        if m:
            cur = m.group(1)
            cats.setdefault(cur, [])
            continue
        if cur is None:
            notes.append(b)
            continue
        if b.lstrip().startswith(("- ", "* ")) and not b.startswith("  "):
            for item in re.split(r"\n(?=[-*] )", b):
                text = dedent2(re.sub(r"^[-*] ", "", item))
                cats[cur].append({"text": text, "more": []})
        elif cats[cur] and b.startswith("  "):
            cats[cur][-1]["more"].append(dedent2(b))
        else:
            cats[cur].append({"note": b})
    return notes, cats


def split_item(text: str) -> tuple[str, str, str]:
    """(lead, short, rest): the bold lead, the first sentence or two, the rest."""
    m = ITEM_LEAD.match(text)
    if m:
        lead, body = m.group("lead").strip().rstrip(".:"), text[m.end():].strip()
    else:
        parts = re.split(r"(?<=[.!?])\s+", text.strip(), 1)
        lead, body = parts[0].rstrip("."), (parts[1] if len(parts) > 1 else "")
    body = re.sub(r"\s*\n\s*", " ", body)
    # "**A Certificates section in the README**: what the board issues..."
    # -- the lead ends in a colon and the sentence continues in lower case,
    # which reads fine inline and wrong under a heading.
    if body[:1].islower():
        body = body[0].upper() + body[1:]
    short, rest = "", body
    for sent in re.split(r"(?<=[.!?])\s+", body):
        if short and len(short) + len(sent) > SHORT:
            break
        short = (short + " " + sent).strip()
    rest = body[len(short):].strip()
    return lead, short, rest


def render_item(item: dict, tag: str | None) -> list[str]:
    if "note" in item:
        return [demote(item["note"]), ""]
    lead, short, rest = split_item(item["text"])
    out = [f"### {lead}"]
    if tag:
        out.append(f'<small class="tp-tag">{tag}</small>')
    out.append("")
    if short:
        out += [short, ""]
    more = ([rest] if rest else []) + item["more"]
    if more:
        out.append('??? note "The whole entry"')
        out.append("")
        for para in more:
            out += ["    " + ln if ln.strip() else "" for ln in para.splitlines()]
            out.append("")
    return out


def render_fix(item: dict, tag: str | None) -> list[str]:
    if "note" in item:
        return [demote(item["note"]), ""]
    lead, short, rest = split_item(item["text"])
    line = f"- **{lead}.**"
    if short:
        line += f" {short}"
    if tag:
        line += f' <small class="tp-tag">{tag}</small>'
    out = [line]
    more = ([rest] if rest else []) + item["more"]
    if more:
        out += ["", '    ??? note "The whole entry"', ""]
        for para in more:
            out += ["        " + ln if ln.strip() else "" for ln in para.splitlines()]
            out.append("")
    return out


def carried(fw_entries: list[dict], idx: int, by_repo: dict) -> list[tuple[str, str, dict]]:
    """(repo, version, entry) for every component version this image is the
    first to carry: each version named in its lede, and the ones between it
    and the version the previous image that named that component carried."""
    entries = fw_entries                      # newest first
    lede = (entries[idx]["body"] or "").split("\n\n", 1)[0]
    out = []
    for m in PIN.finditer(lede):
        repo, ver = m.group("repo"), m.group("ver")
        prev = None
        for older in entries[idx + 1:]:
            older_lede = (older["body"] or "").split("\n\n", 1)[0]
            hits = [n.group("ver") for n in PIN.finditer(older_lede)
                    if n.group("repo") == repo]
            if hits:
                prev = max(hits, key=vtuple)
                break
        versions = [v for v in by_repo.get(repo, {})
                    if vtuple(v) <= vtuple(ver)
                    and (prev is None and v == ver or prev is not None and vtuple(v) > vtuple(prev))]
        for v in sorted(versions, key=vtuple, reverse=True):
            e = by_repo[repo][v]
            if e["body"] and (repo, v) not in [(r, x) for r, x, _ in out]:
                out.append((repo, v, e))
    return out


def write_news(summary: list[dict]) -> list[pathlib.Path]:
    """One post per firmware release, for the blog plugin.

    The changelog pages are a reference: thirty collapsed releases per
    component, and four components. Nobody reads a reference to find out what
    is new, and the first cut of this -- the firmware entry pasted whole,
    followed by each component's entry pasted whole -- was a reference with a
    date on it. A post is built from the same entries taken apart: every item
    becomes a heading with its lead, one or two sentences, and the rest folded
    away; items are grouped as New, Changed and Fixed across the image and the
    component versions it is the first to carry; and a headline, a summary and
    a picture come from docs/data/news-editorial.yaml when someone has written
    them, and from the entry itself when nobody has.
    """
    fw = next(s for s in summary if s["slug"] == "firmware")
    by_repo = {s["repo"]: {e["bare"]: e for e in s["entries"]} for s in summary}
    ed = editorial()
    NEWS.mkdir(parents=True, exist_ok=True)
    written = []
    for idx, e in enumerate(fw["entries"]):
        rel = e.get("released")
        when = (rel.get("publishedAt", "")[:10] if rel else None) or e["date"]
        if not when:
            continue                      # a post has a date, or it is not one
        meta = ed.get(e["version"], {})
        title = meta.get("title") or f"Firmware {e['version']}"
        if rel and rel.get("isPrerelease"):
            title += " (pre-release)"
        elif not rel:
            title += " (not released)"
        lines = ["---", f"title: {json.dumps(title)}", f"date: {when}",
                 f"slug: {e['version']}", "---", ""]

        raw = e["body"] or ""
        parsed = e["source"] == "changelog"
        notes, cats = parse_entry(raw) if parsed else ([raw], {})
        lede = notes[0] if notes and not notes[0].lstrip().startswith(">") else ""
        # No lede: the entry opens with a label and a list. The first item's
        # lead is what the release did, so it is the summary rather than a
        # bare version number.
        first_lead = ""
        for cat in cats:                  # in the entry's own order
            for it in cats.get(cat, []):
                if "text" in it:
                    first_lead = split_item(it["text"])[0] + "."
                    break
            if first_lead:
                break
        summary_text = (meta.get("summary") or lede or first_lead
                        or f"Firmware {e['version']}.")
        lines += [summary_text.strip(), ""]

        # The picture sits above the fold on purpose: the news index shows
        # the excerpt, and a list of releases with a picture each reads as
        # news where a list of version numbers reads as a changelog.
        if meta.get("capture"):
            cap = meta["capture"]
            caption = meta.get("caption", "")
            lines += ['<figure class="tp-post-figure" markdown>',
                      f"![{caption}](../../assets/{cap})",
                      f"<figcaption>{caption}</figcaption>" if caption else "",
                      "</figure>", ""]
        lines += ["<!-- more -->", ""]

        comps = carried(fw["entries"], idx, by_repo) if parsed else []
        pins = [f"[{r} {v}](../../changelog/{SLUG_OF[r]}.md)" for r, v, _ in comps]
        lines += [f"**Firmware {e['version']}**, {human(when)}"
                  + (" — the first image to carry " + ", ".join(pins) + "."
                     if pins else ".")
                  + " Every item below is the repository's own changelog "
                  "entry, taken apart; the whole entry is a click away under "
                  "each one.", ""]

        # Notes that are not the lede -- a blockquote warning, a paragraph
        # about what the release is -- keep their place before the items.
        for n in notes[1:] if lede else notes:
            if n.strip():
                lines += [demote(n), ""]

        # Category by category, the image's own items first and then each
        # carried component's, newest component version first.
        sources = [(None, cats)] + [(f"{r} {v}", parse_entry(c["body"])[1]
                                     if c["source"] == "changelog" else {})
                                    for r, v, c in comps]
        seen: set[str] = set()
        for cat in CATEGORY_ORDER:
            items = []
            for tag, cs in sources:
                for it in cs.get(cat, []):
                    key = (re.sub(r"[^a-z0-9]+", " ", split_item(it["text"])[0].lower()).strip()
                           if "text" in it else "")
                    # The image's entry restates a component's headline change
                    # in its own words often enough that one post carried the
                    # same heading twice. First writer keeps it.
                    if key and key in seen:
                        continue
                    if key:
                        seen.add(key)
                    items.append((tag, it))
            if not items:
                continue
            lines += [f"## {CATEGORY_TITLE[cat]}", ""]
            for tag, it in items:
                # New (and Security) items are the post: a heading each, so
                # the table of contents lists them. Changed and Fixed are a
                # compact list -- twenty headings for twenty adjustments
                # made the contents a wall and the features invisible in it.
                lines += (render_item(it, tag) if cat in ("Added", "Security")
                          else render_fix(it, tag))
            lines.append("")
        for r, v, c in comps:
            if c["source"] != "changelog":
                lines += [f"## {r} {v}", "", c["body"], ""]
        if not parsed:
            lines += [raw, ""]

        lines += ["---", "",
                  "[Every release of the firmware](../../changelog/firmware.md) · "
                  "[the roadmap](../../roadmap.md) · "
                  "[follow by feed](../../feed.xml)"]
        p = NEWS / f"{e['bare']}.md"
        p.write_text("\n".join(lines).rstrip() + "\n")
        written.append(p)
    # A release that vanished from the changelog takes its post with it.
    for stale in NEWS.glob("*.md"):
        if stale not in written:
            stale.unlink()
    return written


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

    ed = editorial()
    site = "https://turingpi.xyz"
    updated = (f"{firmware['newest_date']}T00:00:00Z" if firmware["newest_date"]
               else datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    out = ['<?xml version="1.0" encoding="utf-8"?>',
           '<feed xmlns="http://www.w3.org/2005/Atom">',
           "  <title>Turing Pi 2 BMC firmware releases</title>",
           "  <subtitle>Every release of this fork's firmware, with what "
           "changed in it.</subtitle>",
           f'  <link href="{site}/feed.xml" rel="self"/>',
           f'  <link href="{site}/news/"/>',
           f"  <id>{site}/feed.xml</id>",
           f"  <updated>{updated}</updated>",
           "  <author><name>excavador-turing</name></author>"]
    for e in firmware["entries"][:40]:
        when = f"{e['date']}T00:00:00Z" if e["date"] else updated
        title = ed.get(e["version"], {}).get("title")
        title = (f"Firmware {e['version']}: {title}" if title
                 else f"Firmware {e['version']}")
        out += ["  <entry>",
                f"    <title>{esc(title)}</title>",
                f'    <link href="{site}/news/{esc(e["version"])}/"/>',
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
    before = {p: p.read_text() for p in (*OUTDIR.glob("*.md"), *NEWS.glob("*.md"))}
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
        posts = write_news(summary)
        print(f"  {NEWS.relative_to(ROOT)}/: {len(posts)} posts")

    if args.check:
        after = {p: p.read_text() for p in (*OUTDIR.glob("*.md"), *NEWS.glob("*.md"))}
        if feed.exists():
            after[feed] = feed.read_text()
        stale = sorted(p for p in after if before.get(p) != after[p])
        stale += sorted(p for p in before if p not in after)
        for p in after:
            if p not in before:
                p.unlink()              # --check writes nothing
        for p, text in before.items():
            p.write_text(text)
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
