#!/usr/bin/env python3
"""Fail a build that types a number the facts file owns.

`scripts/facts.py` has claimed since it was written that this script exists,
in its own docstring and in the header it generates into
`docs/data/facts.yaml`. It did not. The claim shipped, was committed, and was
served on the site inside a generated file -- a promise nothing kept, which is
the exact failure the facts file exists to prevent, one level up.

So: every number in `docs/data/facts.yaml` is a number no page may type. A
page that wants it asks for it (`{{ gate.promoted }}`), and this refuses the
ones written out by hand.

    just facts-lint

What it does NOT do, on purpose:

  * It does not touch generated pages. The changelog, the roadmap and the API
    reference are written by scripts from their own sources; a number there is
    read, not typed, and forbidding it would forbid the changelog from naming
    a version.
  * It does not chase numbers the facts file has no opinion about. "Four
    compute modules" is a property of the board, not of this project, and
    putting it in a facts file would be ceremony.
  * It matches a number BESIDE ITS NOUN -- "107 releases", "sixteen features"
    -- not a bare number. The first draft scanned for bare values and found
    seven things, every one of them a false positive: the 11 inside
    `2026-09-11`, the 5 and 15 of a load-average column, the 5 of a
    thermal trip table, and an OpenAPI path count that happened to equal the
    board's promotion count. A number is only a claim when something says
    what it counts.
  * It ignores a number inside a link, a code span or a fenced block. A URL
    with 107 in it is not a claim, and neither is a shell transcript.
"""
from __future__ import annotations

import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
FACTS = DOCS / "data" / "facts.yaml"

# Written by a script from its own source. A number here is read, not typed.
GENERATED = ("changelog/", "reference/api/", "reference/api-history.md",
             "reference/gate-history.md", "roadmap.md", "data/")

# What each fact counts. A number is a claim only when a noun says what it
# counts, and these are the nouns the site has actually used -- including the
# ones it got wrong: "66 releases", "18 firmware updates", "4 faults still
# open", "Sixteen features".
# The PHRASES, not the nouns. A first pass matched bare nouns and called five
# things drift that were not: "six faults" meaning faults TAKEN OUT against
# five still open, "six releases" meaning a duration, "Five rows" meaning rows
# of a Grafana dashboard. A noun is ambiguous; the phrase the site uses to
# make the claim is not.
COUNTED = {
    "gate.promoted":    r"updates taken|firmware updates|promotions",
    "gate.rolled_back": r"rolled back by|automatic rollbacks?",
    "releases.total":   r"releases across",
    "features.count":   r"features, each|things this board does",
    "faults.count":     r"faults still open|open faults|faults are open",
    "roadmap.count":    r"things (?:are )?planned|planned features",
    "boards.from_readers": r"readers'? reports?|reports? from readers",
    "roadmap.votes":    r"votes (?:have been )?cast",
    "platform.rows":    r"rows where this fork differs|rows against upstream",
}

# Spelled out, because that is how the features index said sixteen while
# eleven pages existed.
WORDS = {n: w for n, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve "
    "thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty"
    .split())}


def owned(facts: dict) -> dict[str, tuple[int, str]]:
    """The facts this lint polices: a value, its noun, and its path."""
    out = {}
    for path, noun in COUNTED.items():
        node = facts
        for part in path.split("."):
            node = (node or {}).get(part) if isinstance(node, dict) else None
        if isinstance(node, int):
            out[path] = (node, noun)
    return out


def strip(text: str) -> str:
    """Remove what is not prose: code, links, front matter, macro calls."""
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S)
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`[^`]*`", " ", text)
    text = re.sub(r"\{\{.*?\}\}", " ", text)          # already asking
    text = re.sub(r"\]\([^)]*\)", "] ", text)          # link targets
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    return text


def main() -> int:
    if not FACTS.exists():
        print(f"{FACTS} does not exist -- run `just facts`", file=sys.stderr)
        return 1
    facts = yaml.safe_load(FACTS.read_text())
    policed = owned(facts)

    problems = []
    for page in sorted(DOCS.rglob("*.md")):
        rel = page.relative_to(DOCS).as_posix()
        if any(rel.startswith(g) for g in GENERATED):
            continue
        text = strip(page.read_text())
        for path, (value, noun) in policed.items():
            # Any number next to this fact's noun: the right one typed out is
            # drift waiting to happen, and a wrong one is drift that arrived.
            for m in re.finditer(r"(?<![\w.*])(\d{1,4}|[A-Za-z]+)\s+(?:" + noun
                                 + r")\b", text, re.I):
                written = m.group(1)
                n = (int(written) if written.isdigit()
                     else next((k for k, w in WORDS.items()
                                if w == written.lower()), None))
                if n is None or n < 2:
                    continue
                context = re.sub(r"\s+", " ",
                                 text[max(0, m.start() - 40):m.end() + 40]).strip()
                verdict = ("and that is what the facts file says"
                           if n == value else
                           f"and the facts file says {value}")
                problems.append(
                    f"{rel}: {m.group(0)!r} is typed, {verdict} -- "
                    f"write {{{{ {path} }}}}\n      ...{context}...")

    if problems:
        print(f"{len(problems)} typed numbers the facts file owns:\n",
              file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        print("\nA number written twice is a number that will disagree with "
              "itself. Ask the facts file, or -- if this really is a different "
              "number that happens to collide -- put it in a code span, which "
              "this ignores.", file=sys.stderr)
        return 1

    print(f"  {len(policed)} claims owned by facts.yaml, none typed in a page")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
