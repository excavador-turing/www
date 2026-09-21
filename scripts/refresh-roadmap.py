#!/usr/bin/env python3
"""Rewrite the roadmap from the Ideas discussions and their votes.

The roadmap page says, in its own first paragraph, that every row is a
discussion you can upvote and that "the ones with the most votes get done
first". Neither half was true of the page: the rows were typed in by hand,
carried no vote count at all, and were in no particular order. A reader had
to open seven discussions to find out what the ordering claim meant.

The votes are two API calls away, so the page is generated from them:
ordered by votes, with the count on every row.

    just refresh-roadmap          # rewrite docs/roadmap.md and the data
    just refresh-roadmap --check  # fail if the page is stale

Committed like the changelog and for the same reason. The hourly Pages job
runs it and commits when the numbers move, which is the only way a vote cast
today reaches the site without somebody remembering.

`Where it stands` is the one column a script cannot derive: it is a judgement
about how far along a thing is. It lives in the discussion, as a line reading
`Status: <text>` anywhere in the opening post, so it is edited where the rest
of the argument already is rather than here.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "docs" / "data" / "roadmap.json"
# Where a thing stands is a judgement, not a fact a script can read. It
# belongs in the discussion, as a `Status:` line in the opening post. These
# are the ones the hand-written page carried before it was generated, kept so
# that nothing was lost on the way -- delete an entry here once its
# discussion carries its own line.
STATUS_FALLBACK = ROOT / "docs" / "data" / "roadmap-status.yaml"
PAGE = ROOT / "docs" / "roadmap.md"
ORG = "excavador-turing"
REPO = "BMC-Firmware"

QUERY = """
query($owner:String!, $name:String!) {
  repository(owner:$owner, name:$name) {
    discussions(first:100, orderBy:{field:CREATED_AT, direction:DESC}) {
      nodes {
        number title url upvoteCount createdAt
        category { name }
        body
      }
    }
  }
}
"""

# `Status: Designed, not started` in the opening post, bare or in backticks
# -- the posted lines are in backticks, and the first version of this read
# every one of them as "Open". Anything else is prose.
STATUS = re.compile(r"^\s*`?Status:\s*(?P<text>.+?)`?\s*$", re.M | re.I)

# `Summary: one line` in the opening post, when the author wants to choose it.
SUMMARY = re.compile(r"^\s*Summary:\s*(?P<text>.+?)\s*$", re.M | re.I)

# How much of a "what it is" cell a reader will actually read. The first
# draft put the whole opening paragraph in, and the widest row ran to 400
# characters -- a wall of text in a table is a table nobody reads.
CELL = 200


def summary(body: str) -> str:
    """One sentence saying what the thing is.

    An explicit `Summary:` line wins. Otherwise the first sentence of the
    first real paragraph -- skipping headings, because one discussion opens
    with `## The problem` and the first draft printed exactly that as its
    summary.
    """
    body = re.sub(r"<!--.*?-->", "", body or "", flags=re.S)
    chosen = SUMMARY.search(body)
    if chosen:
        text = chosen.group("text")
    else:
        text = ""
        for para in re.split(r"\n\s*\n", body):
            para = para.strip()
            if not para or para.startswith("#") or para.startswith(">"):
                continue
            if re.match(r"^\s*(Status|Summary):", para, re.I):
                continue
            text = para
            break
    text = re.sub(r"\s+", " ", re.sub(r"^[#>\s]*", "", text)).strip()
    # First sentence, unless that is already longer than a cell should be.
    first = re.split(r"(?<=[.!?])\s+", text)
    out = first[0] if first else text
    if len(out) > CELL:
        out = out[:CELL].rsplit(" ", 1)[0].rstrip(" ,;:—-") + "…"
    return out


def statuses() -> dict[int, str]:
    if not STATUS_FALLBACK.exists():
        return {}
    out = {}
    for line in STATUS_FALLBACK.read_text().splitlines():
        m = re.match(r"^\s*(\d+)\s*:\s*(.+?)\s*$", line)
        if m:
            out[int(m.group(1))] = m.group(2).strip().strip('"')
    return out


def fetch() -> list[dict]:
    fallback = statuses()
    out = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={QUERY}",
         "-F", f"owner={ORG}", "-F", f"name={REPO}"],
        capture_output=True, text=True, check=True).stdout
    nodes = json.loads(out)["data"]["repository"]["discussions"]["nodes"]
    items = []
    for n in nodes:
        if (n.get("category") or {}).get("name") != "Ideas":
            continue
        st = STATUS.search(n.get("body") or "")
        items.append({
            "number": n["number"],
            "title": n["title"],
            "url": n["url"],
            "votes": n["upvoteCount"],
            "status": st.group("text") if st else fallback.get(n["number"], "Open"),
            "status_from": "discussion" if st else
                           ("fallback" if n["number"] in fallback else "default"),
            "summary": summary(n.get("body")),
        })
    # Votes first, then the older idea, so the order is stable between runs
    # when two things are level.
    items.sort(key=lambda i: (-i["votes"], i["number"]))
    return items


# A status that begins with "Shipped" moves the card off the planned list:
# a shipped thing still carries its votes and its discussion, but it is not
# something to vote on any more. "Listing shipped in v3.25.0; the rest is
# open" does not begin with it, and stays.
SHIPPED = re.compile(r"^\s*shipped\b", re.I)


def inline(text: str) -> str:
    """Escape a summary for raw HTML, keeping `code` as code."""
    out = html.escape(text, quote=True)
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", out)


def card(i: dict) -> str:
    st = i["status"]
    kind = ("shipped" if SHIPPED.match(st) else
            "started" if re.search(r"shipped|started|designed|in progress",
                                   st, re.I) else "open")
    return (
        f'<a class="tp-idea tp-idea--{kind}" href="{html.escape(i["url"])}">'
        f'<b class="tp-idea__votes">{i["votes"]}<small>'
        f'{"vote" if i["votes"] == 1 else "votes"}</small></b>'
        f'<span class="tp-idea__title">{inline(i["title"])}</span>'
        f'<span class="tp-idea__what">{inline(i["summary"])}</span>'
        f'<span class="tp-idea__status">{inline(st)}</span>'
        "</a>")


def render(items: list[dict], as_of: str) -> str:
    planned = [i for i in items if not SHIPPED.match(i["status"])]
    done = [i for i in items if SHIPPED.match(i["status"])]
    total = sum(i["votes"] for i in items)
    when = dt.date.fromisoformat(as_of).strftime("%-d %B %Y")
    propose = f"https://github.com/{ORG}/{REPO}/discussions/new?category=ideas"
    lines = [
        "---",
        "title: Roadmap",
        "hide:",
        "  - navigation",
        "  - toc",
        "---",
        "",
        # The page was a table: seven rows, four columns, the one number
        # that orders it in bold at the left edge and the status in prose at
        # the right. It carried the facts and read like a spreadsheet next
        # to every other page on the site. The cards carry the same four
        # facts in the site's own shape, and the vote is the thing you see.
        '<div class="tp-hero-band" markdown>',
        '<span class="tp-eyebrow">Roadmap</span>',
        f"# {len(planned)} things planned. Your vote orders them.",
        "",
        "<p>Every card is a GitHub Discussion. Upvote the ones you want and "
        "this page reorders itself: the votes are read every hour, so a vote "
        "cast now is on the page within one. Not on the list? "
        f'<a href="{propose}">Propose it</a> — a sentence about the problem is '
        "enough.</p>",
        "</div>",
        "",
        '<div class="tp-proof">',
        f"<div><b>{len(planned)}</b><span>planned, ordered by votes</span></div>",
        f"<div><b>{total}</b><span>votes cast, read hourly</span></div>",
        f"<div><b>{len(done)}</b><span>shipped from this list</span></div>",
        "</div>",
        "",
        '<div class="tp-ideas">',
        *[card(i) for i in planned],
        "</div>",
        "",
        "Something broken rather than missing? [Report it](feedback.md), "
        "and read [what is and isn't fixed](reference/known-faults.md) first, "
        "because it may already be there with a ticket.",
    ]
    if done:
        lines += [
            "",
            "## Shipped from this list",
            "",
            "Voted for, built, released. Each card still opens its discussion."
            "",
            '<div class="tp-ideas tp-ideas--done">',
            *[card(i) for i in done],
            "</div>",
        ]
    lines += [
        "",
        "## Recently shipped",
        "",
        "One post per firmware release, from the repositories' own "
        "changelogs — [all of them](news/index.md), or "
        "[by feed](feed.xml).",
        "",
        "{{ recent_releases }}",
        "",
        "## How a thing gets from here to there",
        "",
        "A feature is a ticket in the maintainer's tracker, a Discussion here, "
        "and then a page under [Features](features/index.md) with the numbers "
        "that prove it — in that order. The "
        "[known-faults page](reference/known-faults.md) is the other half of "
        "this one: what is wrong today, with the ticket that tracks it. A "
        "roadmap that lists only what is coming is advertising.",
        "",
        f"Votes read {when} by `just refresh-roadmap`, which runs every hour.",
        "",
        '<div class="tp-next">',
        '<a href="news/"><b>What shipped →</b><span>One post per firmware '
        "release, newest first.</span></a>",
        '<a href="feedback/"><b>Propose or report →</b><span>Ideas carry '
        "votes; faults carry tickets.</span></a>",
        '<a href="reference/known-faults/"><b>What is not fixed →</b>'
        "<span>The honest list, each with a ticket.</span></a>",
        '<a href="features/"><b>What it does today →</b><span>Every feature, '
        "with the measurement behind it.</span></a>",
        "</div>",
    ]
    return "\n".join(lines) + "\n"


def recent(n: int = 5) -> str:
    """The newest firmware releases, each linking to its news post."""
    page = ROOT / "docs" / "changelog" / "firmware.md"
    if not page.exists():
        return "_Run `just refresh-changelog` first._"
    rows = re.findall(r'^\?\?\?\+? note "([^"]+)"', page.read_text(), re.M)
    # A release covered by another's post links to that post.
    posts_map = ROOT / "docs" / "data" / "news-posts.json"
    slug_of = json.loads(posts_map.read_text()) if posts_map.exists() else {}
    out = ['<div class="tp-releases">']
    for row in rows[:n]:
        ver, _, when = row.partition(" — ")
        when = when.replace(" (not released)", "").replace(" (pre-release)", "")
        slug = slug_of.get(ver, ver)
        out.append(f'<a href="news/{html.escape(slug)}/"><b>{html.escape(ver)}'
                   f"</b><span>{html.escape(when)}</span></a>")
    out.append("</div>")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv[1:])

    items = fetch()
    as_of = dt.date.today().isoformat()
    text = render(items, as_of).replace("{{ recent_releases }}", recent())
    data = json.dumps({"as_of": as_of, "items": items}, indent=1) + "\n"

    if args.check:
        stale = []
        if not PAGE.exists() or PAGE.read_text() != text:
            stale.append(PAGE)
        if not DATA.exists() or DATA.read_text() != data:
            stale.append(DATA)
        if stale:
            print("stale, run `just refresh-roadmap` and commit:",
                  file=sys.stderr)
            for p in stale:
                print(f"  {p.relative_to(ROOT)}", file=sys.stderr)
            return 1
        print("  the roadmap matches the discussions")
        return 0

    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(data)
    PAGE.write_text(text)
    if items:
        print(f"  {len(items)} ideas, {sum(i['votes'] for i in items)} votes, "
              f"top: {items[0]['title'][:54]!r} ({items[0]['votes']})")
        borrowed = [i for i in items if i["status_from"] == "fallback"]
        if borrowed:
            # Say it every run: the fallback exists so nothing was lost when
            # the page became generated, not as a second place to keep facts.
            print(f"  {len(borrowed)} statuses still come from "
                  f"{STATUS_FALLBACK.name} rather than their discussion: "
                  f"{', '.join('#%d' % i['number'] for i in borrowed)}")
    else:
        print("  no ideas found")
    print(f"  -> {PAGE.relative_to(ROOT)}, {DATA.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
