#!/usr/bin/env python3
"""Keep the eleven feature pages the same page eleven times.

They shared a skeleton in eleven copies of the markup, and it had drifted in
every direction a skeleton can. Side by side the pages looked like different
sites:

    ledes                22 to 48 words, in two voices
    proof strips         about half of them measurements, the rest counts of
                         design choices, and ten of eleven ending on a zero
    next links           eight different labels opening the same demo, and one
                         page linking it twice
    captures             six full interfaces, four cropped cards, one a
                         screenshot of THIS SITE; five with the demo's ribbon
                         across the top and six without

`main.py` renders the shape now, so the markup cannot drift. This checks the
things a template cannot: that the content in the front matter is the right
length, that every number has a source and a date, that the four links are
the four roles pointing at four different places, and that the capture exists.

    just feature-lint
"""
from __future__ import annotations

import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
FEATURES = ROOT / "docs" / "features"
CAPTURES = ROOT / "docs" / "assets" / "captures"
ICONS = ROOT / "docs" / "assets" / "icons"
WHY = ROOT / "docs" / "why"

# A lede is the one paragraph beside the picture. Below 25 words it does not
# say what upstream does AND what this does instead; above 35 the text column
# outgrows the picture and the two stop lining up.
LEDE = (25, 35)
SUMMARY_MAX = 22          # the plate on the index; longer wraps to four lines
ROLES = ["demo", "do", "evidence", "related"]
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def front_matter(path: pathlib.Path) -> dict:
    text = path.read_text()
    if not text.startswith("---"):
        return {}
    return yaml.safe_load(text[3:text.index("\n---", 3)]) or {}


# The one section every argument must end with. It was the most useful thing
# on the two pages that had it and was missing from seven of eleven, under
# five different names where it existed at all: "What this does not do",
# "What a source cannot do", "What this does not give you", "What is next".
LIMITS = "What it does not cover"


def check_argument(path: pathlib.Path, feature: pathlib.Path, bad) -> None:
    """The argument page behind a feature: same opening, same closing."""
    text = path.read_text()
    here = lambda msg: bad(path, msg)

    if "is the argument behind" not in text:
        here("does not open with the standing line naming the feature it "
             "argues for")
    if f"\n## {LIMITS}\n" not in text:
        here(f"has no `## {LIMITS}` section -- the honest half, and the part "
             f"a reader came for once they are past the claim")
    else:
        # It must be the LAST section: a limit buried in the middle reads as
        # an aside rather than as the conclusion.
        heads = re.findall(r"^## (.+)$", text, re.M)
        if heads and heads[-1] != LIMITS:
            here(f"`## {LIMITS}` is not the last section (followed by "
                 f"{heads[-1]!r})")
    if 'class="tp-next"' not in text:
        here("has no way onward -- an argument page that ends in prose is a "
             "dead end, and these are the deepest pages on the site")
    elif "Back to the feature" not in text:
        here("its next block does not link back to the feature page")


def main() -> int:
    pages = sorted(p for p in FEATURES.glob("*.md") if p.stem != "index")
    problems: list[str] = []

    def bad(page, msg):
        problems.append(f"{page.relative_to(ROOT)}: {msg}")

    orders: dict[int, str] = {}
    for page in pages:
        meta = front_matter(page)
        body = page.read_text()
        f = meta.get("feature")
        if not f:
            bad(page, "no `feature:` block in the front matter")
            continue
        if not meta.get("render_macros"):
            bad(page, "front matter is missing `render_macros: true`, so the "
                      "template will render as literal text")
        if "{{ feature_screen() }}" not in body:
            bad(page, "body does not call `{{ feature_screen() }}`")

        n = len((f.get("lede") or "").split())
        if not LEDE[0] <= n <= LEDE[1]:
            bad(page, f"lede is {n} words, wanted {LEDE[0]}-{LEDE[1]}")
        s = len((f.get("summary") or "").split())
        if not 1 <= s <= SUMMARY_MAX:
            bad(page, f"index summary is {s} words, wanted 1-{SUMMARY_MAX}")

        order = f.get("order")
        if order is None:
            bad(page, "no `order:`, so its place on the index is arbitrary")
        elif order in orders:
            bad(page, f"order {order} is already {orders[order]}")
        else:
            orders[order] = page.stem

        proofs = f.get("proofs") or []
        if len(proofs) != 3:
            bad(page, f"{len(proofs)} proofs, wanted 3")
        for i, p in enumerate(proofs, 1):
            for key in ("n", "of", "source", "as_of"):
                if not p.get(key):
                    bad(page, f"proof {i} has no `{key}` -- a number without a "
                              f"source and a date is a claim, not a measurement")
            if p.get("as_of") and not ISO.match(str(p["as_of"])):
                bad(page, f"proof {i} as_of {p['as_of']!r} is not YYYY-MM-DD")

        nxt = f.get("next") or {}
        missing = [r for r in ROLES if r not in nxt]
        if missing:
            bad(page, f"next is missing {', '.join(missing)}")
        seen: dict[str, str] = {}
        for role in ROLES:
            link = nxt.get(role)
            if not link:
                continue
            for key in ("href", "text", "note"):
                if not link.get(key):
                    bad(page, f"next.{role} has no `{key}`")
            href = link.get("href", "")
            if href in seen:
                bad(page, f"next.{role} and next.{seen[href]} both point at "
                          f"{href} -- four links should reach four places")
            seen[href] = role
        demo = (nxt.get("demo") or {}).get("href", "")
        if demo and "#demo/" not in demo:
            bad(page, f"next.demo points at {demo}, which is not the demo")

        capture = f.get("capture")
        if not capture:
            bad(page, "no `capture:`")
        elif not (CAPTURES / capture).exists():
            bad(page, f"capture {capture} does not exist")
        if not f.get("caption"):
            bad(page, "no `caption:` -- a picture with no caption makes the "
                      "reader guess what they are looking at")
        icon = f.get("icon")
        if not icon:
            bad(page, "no `icon:` for its plate on the index")
        elif not (ICONS / icon).exists():
            bad(page, f"icon {icon} does not exist")

        argument = WHY / f"{page.stem}.md"
        if not argument.exists():
            bad(page, f"no argument page at why/{page.stem}.md")
        elif f"../why/{page.stem}.md" not in body:
            bad(page, "does not link its argument page")
        else:
            check_argument(argument, page, bad)

    index = FEATURES / "index.md"
    if "{{ feature_plates() }}" not in index.read_text():
        problems.append(f"{index.relative_to(ROOT)}: does not call "
                        f"`{{{{ feature_plates() }}}}` -- the plates would be "
                        f"hand-written again, which is how it came to list "
                        f"sixteen for eleven pages")

    if problems:
        print(f"{len(problems)} problems across {len(pages)} feature pages:\n",
              file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1
    print(f"  {len(pages)} feature pages: one shape, {len(pages) * 3} proofs "
          f"each with a source and a date, {len(pages) * 4} links in four roles")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
