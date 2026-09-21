#!/usr/bin/env python3
"""Collect every number this site quotes about itself into one file.

The site had the right instinct in two places and nowhere else. The gate's
record and the API reference are generated, and refuse hand-typed numbers.
Everything else was typed, and had drifted:

    the features index said 18 updates and 1 rollback
    the front page and the feature page said 26, which is what the board says
    About said 66 releases; the changelog adds up to 95
    About said 4 open faults; the known-faults page lists 5
    the roadmap said fifteen features; the index showed sixteen

None of those were wrong when written. They were written more than once, and
a fact written twice is a fact that will disagree with itself.

So: every number lives here, each with where it came from and when, and pages
quote it through the macros plugin -- `{{ gate.updates }}` rather than `26`.
`scripts/facts-lint.py` fails the build if a page types one of these numbers
instead of asking for it.

    just facts            # rebuild docs/data/facts.yaml
    just facts --offline  # keep what needs the network, refresh the rest

What comes from where:

    gate        scripts/refresh-gate-history.py, which reads a real board.
                Needs a route to one, so it is NOT refreshed here; this reads
                what that script last committed.
    releases    the changelog pages, which refresh-changelog.py writes from
                each repository's CHANGELOG.md.
    features    the feature pages on disk. A feature is a page; counting them
                is not a judgement call.
    faults      the headings under `## Open` in the known-faults page.
    roadmap     refresh-roadmap.py, from the Ideas discussions and their
                votes.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re

import yaml
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
OUT = DOCS / "data" / "facts.yaml"

TODAY = dt.date.today().isoformat()


def gate() -> dict:
    """Promotions, rollbacks and trips to the rack, as the board reported them.

    Read out of the page `refresh-gate-history.py` writes rather than off a
    board: CI has no route to one and must never be the thing that notices.
    """
    text = (DOCS / "reference" / "gate-history.md").read_text()
    when = re.search(r"As of \*\*(\d{4}-\d{2}-\d{2})\*\*", text)

    def row(label):
        m = re.search(r"^\|\s*" + label + r"\s*\|\s*(\d+)\s*\|", text, re.M)
        return int(m.group(1)) if m else None

    promoted, rolled = row("promoted"), row("rolled back")
    if promoted is None or rolled is None:
        raise SystemExit("gate-history.md no longer carries the counter table; "
                         "facts.py reads `| promoted | N |` out of it")
    return {
        "source": "reference/gate-history.md, written by "
                  "`just refresh-gate-history <board>` from the board's "
                  "own bmcd_firmware_promotion_total counter",
        "as_of": when.group(1) if when else None,
        # `promoted` is what the selling pages call "updates taken": images
        # the gate kept. `attempts` is every image it judged, which is the
        # denominator when the rollback is the interesting number.
        "promoted": promoted,
        "rolled_back": rolled,
        "attempts": promoted + rolled,
        # Not a counter: the claim is that no promotion has ever needed
        # somebody at the rack, and the rollback above is the evidence.
        "rack_trips": 0,
    }


def releases() -> dict:
    """Newest version and release count per component, from the changelog pages."""
    out = {"source": "docs/changelog/*.md, written by `just refresh-changelog` "
                     "from each repository's CHANGELOG.md"}
    total = 0
    for name, page in (("firmware", "firmware"), ("bmcd", "bmcd"),
                       ("ui", "bmc-ui"), ("tpi", "tpi")):
        f = DOCS / "changelog" / f"{page}.md"
        if not f.exists():
            continue
        text = f.read_text()
        newest = re.search(r"[Nn]ewest release \*\*(v?[0-9][^*]*)\*\*", text)
        # The page states its own count; counting collapsed blocks instead
        # counted the Unreleased one as a release, and said BMC-UI had 28
        # where the page it read said 27.
        count = re.search(r"(\d+) in total", text)
        if not count:
            raise SystemExit(f"{f.name} no longer states 'N in total'; "
                             f"facts.py reads the count out of it")
        n = int(count.group(1))
        total += n
        out[name] = {"newest": newest.group(1).strip() if newest else None,
                     "count": n}
    out["total"] = total
    return out


def features() -> dict:
    """How many features there are: how many feature pages there are."""
    pages = sorted(p.stem for p in (DOCS / "features").glob("*.md")
                   if p.stem != "index")
    return {"source": "docs/features/*.md -- a feature is a page",
            "count": len(pages), "pages": pages}


def boards() -> dict:
    """Which board revisions this firmware has been seen running on."""
    reports = yaml.safe_load((DOCS / "data" / "boards.yaml").read_text()) or []
    revisions = sorted({str(r.get("revision", "")) for r in reports if r.get("revision")})
    readers = sum(1 for r in reports if "reader" in str(r.get("source", "")))
    return {"source": "docs/data/boards.yaml -- one entry per report, rendered by board_reports()",
            "reports": len(reports), "from_readers": readers,
            "revisions": revisions}


def faults() -> dict:
    """Open faults: the headings under `## Open`."""
    text = (DOCS / "reference" / "known-faults.md").read_text()
    body = re.split(r"^##\s+", text, flags=re.M)
    open_section = next((s for s in body if s.lower().startswith("open")), "")
    names = re.findall(r"^###\s+(.+)$", open_section, re.M)
    return {"source": "reference/known-faults.md, the headings under `## Open`",
            "count": len(names), "names": names}


def roadmap() -> dict:
    """Planned features and their votes, as refresh-roadmap.py last recorded."""
    f = DOCS / "data" / "roadmap.json"
    if not f.exists():
        return {"source": "docs/data/roadmap.json, written by "
                          "`just refresh-roadmap`", "count": 0, "top": None}
    data = json.loads(f.read_text())
    items = sorted(data.get("items", []), key=lambda i: -i.get("votes", 0))
    # An idea whose status begins with "Shipped" is off the planned list on
    # the roadmap page (refresh-roadmap.py, SHIPPED); it keeps its votes in
    # the total, because they were cast, but it is not planned and not what
    # is "leading" -- the front page said the VLANs led the roadmap the
    # evening they shipped.
    planned = [i for i in items
               if not re.match(r"\s*shipped\b", i.get("status", ""), re.I)]
    return {"source": "docs/data/roadmap.json, written by `just refresh-roadmap` "
                      "from the Ideas discussions",
            "as_of": data.get("as_of"),
            "count": len(planned),
            "shipped": len(items) - len(planned),
            "votes": sum(i.get("votes", 0) for i in items),
            "top": planned[0]["title"] if planned else None}


def platform() -> dict:
    """The versions the comparison page proves, which the selling pages quote."""
    text = (DOCS / "reference" / "comparison.md").read_text()

    # Data rows of the upstream-vs-fork tables: a row whose first cell is a
    # label. Not the header rule, not the `route` header of the two-catalogue
    # table, and not that table's two rows, whose labels are links. About
    # quoted this as a typed 13, which happened to be right; it is read now
    # so it stays right. (A first draft excluded hyphens from the label and
    # so lost "Module power-on time" -- 12, not 13.)
    rows = []
    for label in re.findall(r"^\|\s*([^|]+?)\s*\|", text, re.M):
        label = label.strip()
        if not label or set(label) <= set("-: ") or label.lower() == "route":
            continue
        if label.startswith("["):
            continue
        rows.append(label)

    def row(label):
        m = re.search(r"^\|\s*" + label + r"\s*\|([^|]*)\|([^|]*)\|", text, re.M)
        if not m:
            return None, None
        strip = lambda s: re.sub(r"\*\*|`", "", s).strip()
        return strip(m.group(1)), strip(m.group(2))

    up_kernel, our_kernel = row("Kernel")
    up_br, our_br = row("Buildroot")
    return {"source": "reference/comparison.md, measured on a running board",
            "rows": len(rows),
            "kernel": {"upstream": up_kernel, "fork": our_kernel},
            "buildroot": {"upstream": up_br, "fork": our_br},
            "upstream_last_release": "2025-02-05",
            "upstream_last_version": "v2.1.0"}


def dump(data: dict) -> str:
    """Minimal YAML, so this file needs no writer dependency.

    Only the shapes this script produces: nested maps, lists of strings,
    numbers, and None.
    """
    lines = ["# GENERATED by scripts/facts.py -- do not edit.",
             "#",
             "# Every number this site quotes about itself, with where it came",
             "# from. Pages read it through the macros plugin: {{ gate.updates }},",
             "# never 26. scripts/facts-lint.py fails a build that types one.",
             f"generated: {TODAY}"]

    def scalar(v):
        if v is None:
            return "null"
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, (int, float)):
            return str(v)
        s = str(v)
        return json.dumps(s) if re.search(r"[:#\n\"']|^\s|\s$|^$", s) else s

    def walk(obj, indent):
        pad = " " * indent
        for k, v in obj.items():
            if isinstance(v, dict):
                lines.append(f"{pad}{k}:")
                walk(v, indent + 2)
            elif isinstance(v, list):
                if not v:
                    lines.append(f"{pad}{k}: []")
                else:
                    lines.append(f"{pad}{k}:")
                    for item in v:
                        lines.append(f"{pad}  - {scalar(item)}")
            else:
                lines.append(f"{pad}{k}: {scalar(v)}")

    walk(data, 0)
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="fail if the committed file is not what this produces")
    args = ap.parse_args()

    data = {
        "gate": gate(),
        "releases": releases(),
        "features": features(),
        "boards": boards(),
        "faults": faults(),
        "roadmap": roadmap(),
        "platform": platform(),
    }
    text = dump(data)

    if args.check:
        if not OUT.exists():
            print(f"{OUT} does not exist -- run `just facts`", file=sys.stderr)
            return 1
        have = OUT.read_text()
        # The generated-on date moves every day and means nothing on its own.
        strip = lambda s: re.sub(r"^generated: .*$", "", s, flags=re.M)
        if strip(have) != strip(text):
            print(f"{OUT.relative_to(ROOT)} is stale -- run `just facts` and "
                  f"commit the result", file=sys.stderr)
            subprocess.run(["diff", "-u", str(OUT), "-"], input=text,
                           text=True)
            return 1
        print(f"  {OUT.relative_to(ROOT)} matches its sources")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    g, r, f = data["gate"], data["releases"], data["features"]
    print(f"  gate: {g['promoted']} promoted, {g['rolled_back']} rolled back "
          f"(as of {g['as_of']})")
    print(f"  releases: {r['total']} across four components")
    print(f"  features: {f['count']} pages")
    print(f"  boards: {data['boards']['reports']} reports, "
          f"revisions {', '.join(data['boards']['revisions'])}")
    print(f"  faults: {data['faults']['count']} open")
    print(f"  roadmap: {data['roadmap']['count']} planned, "
          f"{data['roadmap'].get('votes', 0)} votes")
    print(f"  -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
