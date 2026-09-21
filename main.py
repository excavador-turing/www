"""Macros for the site: one template for every feature page.

Loaded by mkdocs-macros (`module_name: main`). It exists because the eleven
feature pages shared a skeleton in eleven copies of the markup, and a
skeleton kept by copy drifts:

  * ledes ran from 22 to 48 words and took two voices, so the text column and
    the picture beside it lined up on no two pages;
  * the "three measurements" were about half measurements and half counts of
    design choices -- 2 ways in, 5 key types, 9 tabs -- and ten of the eleven
    strips ended on a zero, which reads as a formula once you have seen three;
  * eight different labels opened the same demo: "See the interface", "See it
    working", "See the Firmware tab", "Open a console now", "See the
    readings", "See the sources". One page linked the demo twice.

Now each page carries its data in front matter and this renders it, so the
shape is the same by construction and `scripts/feature-lint.py` can check the
content: lede length, three proofs each with a source and a date, four next
links in fixed roles, and a capture that exists.
"""
from __future__ import annotations

import html
import json
import pathlib
import re

import yaml

# The four things a reader wants next, in the order they want them. Fixed,
# because the labels were the loudest inconsistency between these pages and
# a reader clicking through all eleven met eight different words for "open
# the demo".
ROLES = [
    ("demo", "See it in the demo"),
    ("do", "Do it on your board"),
    ("evidence", "The evidence"),
    ("related", "A related feature"),
]

ROOT = pathlib.Path(__file__).resolve().parent


# Eleven reads better than 11 at the top of a page, and the count is still
# the facts file's to state.
NUMBER_WORDS = ("zero one two three four five six seven eight nine ten eleven "
                "twelve thirteen fourteen fifteen sixteen seventeen eighteen "
                "nineteen twenty").split()


def define_env(env):
    """Hook for mkdocs-macros."""

    # The theme's templates render outside this plugin and cannot see its
    # variables, but `config.extra` they can. Two things are put there for
    # `overrides/main.html`, which writes the page's structured data:
    #
    #   facts  -- so the front page can state the CURRENT firmware version
    #             without anyone typing it. facts.yaml is the only place that
    #             number is allowed to live.
    #   faq    -- the FAQ's questions and answers, so the page can be marked
    #             up as what it is. Parsed from the page, not kept beside it,
    #             because a copy is a copy that goes stale.
    extra = env.conf.setdefault("extra", {})
    facts_file = ROOT / "docs" / "data" / "facts.yaml"
    if facts_file.exists():
        extra["facts"] = yaml.safe_load(facts_file.read_text()) or {}
    extra["faq"] = _faq_entities(ROOT / "docs" / "faq.md")


    @env.filter
    def title_number(n):
        """A small number spelled out, for a headline."""
        n = int(n)
        word = NUMBER_WORDS[n] if 0 <= n < len(NUMBER_WORDS) else str(n)
        return word.capitalize()

    @env.macro
    def feature_screen():
        """Screen one of a feature page: the claim, its numbers, the picture."""
        meta = env.page.meta or {}
        f = meta.get("feature")
        if not f:
            return ('<p><strong>This page has no <code>feature:</code> block '
                    'in its front matter.</strong></p>')
        title = meta.get("title") or env.page.title
        esc = html.escape

        proofs = "".join(
            f'<div><b>{esc(str(p["n"]))}</b>'
            f'<span>{esc(p["of"])}</span></div>'
            for p in f.get("proofs", []))

        nxt = ""
        for role, _ in ROLES:
            link = (f.get("next") or {}).get(role)
            if not link:
                continue
            nxt += (f'<a href="{esc(link["href"])}"><b>{esc(link["text"])} →</b>'
                    f'<span>{esc(link["note"])}</span></a>')

        capture = f.get("capture", "")
        caption = f.get("caption", "")
        alt = f.get("alt") or caption

        # The proof strip's provenance, once, under the numbers rather than
        # three times inside them. Every proof carries a source and a date in
        # the front matter; where they agree -- they usually do -- this is one
        # line instead of three.
        sources = {(p.get("source", ""), str(p.get("as_of", "")))
                   for p in f.get("proofs", [])}
        if len(sources) == 1:
            src, when = next(iter(sources))
            provenance = f'<p class="tp-provenance">{esc(src)}, {esc(when)}.</p>'
        else:
            provenance = '<p class="tp-provenance">' + " ".join(
                f'{esc(p["of"])}: {esc(p.get("source", ""))}, '
                f'{esc(str(p.get("as_of", "")))}.'
                for p in f.get("proofs", [])) + "</p>"

        return f"""
<section class="tp-feature" data-screen="feature">
<div class="tp-feature__say">
<span class="tp-eyebrow">Feature</span>
<h1>{esc(title)}</h1>
<p class="lede">{esc(f.get("lede", ""))}</p>
<div class="tp-proof">{proofs}</div>
{provenance}
<div class="tp-next">{nxt}</div>
</div>
<figure class="tp-feature__show">
<img src="../../assets/captures/{esc(capture)}" alt="{esc(alt)}">
<figcaption>{esc(caption)}</figcaption>
</figure>
</section>
""".strip()

    @env.macro
    def comparison_table():
        """About's "what changed", rendered from the page that measures it."""
        rows = comparison_rows()
        stated = (env.variables.get("platform") or {}).get("rows")
        if stated is not None and stated != len(rows):
            raise RuntimeError(
                f"comparison.md has {len(rows)} rows and facts.yaml says "
                f"{stated}: run `just facts` and commit the result")
        out = ['<div class="tp-vs">']
        for label, them, us in rows:
            out.append(
                '<div class="tp-vs__row">'
                f'<div class="tp-vs__what">{_md_inline(label)}</div>'
                f'<div class="tp-vs__them">{_md_inline(them) or "—"}</div>'
                f'<div class="tp-vs__us">{_md_inline(us) or "—"}</div>'
                "</div>")
        out.append("</div>")
        return "\n".join(out)

    @env.macro
    def news_lede():
        """The newest firmware release, in its own first sentence.

        The front page's What's-new column carried a sentence typed by hand,
        and it was two releases old on the day this replaced it. The post the
        changelog generator writes opens with the release's own lede, so the
        front page now says what the newest post says, by construction.
        """
        newest = None
        for path in (ROOT / "docs" / "news" / "posts").glob("*.md"):
            meta = _front_matter(path)
            key = (str(meta.get("date", "")),
                   [int(x) for x in re.findall(r"\d+", path.stem)])
            if newest is None or key > newest[0]:
                newest = (key, path, meta)
        if newest is None:
            return ""
        _, path, meta = newest
        text = path.read_text().split("---", 2)[2]
        text = text.split("<!-- more -->", 1)[0]
        text = re.sub(r"\s+", " ", re.sub(r"\*\*|`", "", text)).strip()
        # An entry with no lede opens with its label and first item:
        # "Fixed - A renamed board reissues its own certificate."
        text = re.sub(r"^(Added|Changed|Fixed|Removed|Deprecated|Security)"
                      r"\s*[-*]\s*", "", text)
        first = re.split(r"(?<=[.!?])\s+", text)[0]
        # The version is the post's slug. Its title is editorial when someone
        # wrote one -- the day this read the version out of the title, the
        # front page said "Firmware The switch gets VLANs..." -- and an
        # editorial title is the better sentence, so it wins over the lede.
        ver = html.escape(str(meta.get("slug", path.stem)))
        title = str(meta.get("title", ""))
        if title and not title.startswith("Firmware "):
            return f"Firmware <b>{ver}</b>: {html.escape(title.rstrip('.'))}."
        if first.startswith("Pins "):
            return f"Firmware <b>{ver}</b> pins {html.escape(first[5:])}"
        return f"Firmware <b>{ver}</b>: {html.escape(first)}"

    @env.macro
    def feature_plates():
        """The features index, from the pages themselves.

        The index was sixteen hand-written plates for eleven pages -- five of
        them jumping into Reference, two of those to the same page -- and
        every plate's sentence was truncated at every viewport, which was 307
        of the site's 439 measured faults. Now there is one plate per page,
        by construction, and the sentence is the page's own summary.
        """
        pages = []
        for path in sorted((ROOT / "docs" / "features").glob("*.md")):
            if path.stem == "index":
                continue
            meta = _front_matter(path)
            f = meta.get("feature") or {}
            pages.append({
                "slug": path.stem,
                "title": meta.get("title") or path.stem,
                "summary": f.get("summary", ""),
                "icon": f.get("icon", ""),
                "order": f.get("order", 99),
            })
        pages.sort(key=lambda p: (p["order"], p["title"]))
        out = ['<div class="tp-plates">']
        for p in pages:
            icon = (f'<img src="../assets/icons/{html.escape(p["icon"])}" alt="">'
                    if p["icon"] else "")
            out.append(
                f'<a class="tp-plate" href="../{html.escape(p["slug"])}/">'
                f'{icon}<b>{html.escape(p["title"])}</b>'
                f'<span>{html.escape(p["summary"])}</span></a>')
        out.append("</div>")
        return "\n".join(out)


def comparison_rows() -> list[tuple[str, str, str]]:
    """The upstream-vs-fork rows of reference/comparison.md.

    About carried its own thirteen-row table of "what changed" -- a
    DIFFERENT thirteen from the comparison page's, sharing five rows and
    diverging on eight, under a sentence promising that every row was backed
    by a measurement there. It was not: Metrics, Checksums, Serial consoles,
    Firmware sources, Several boards, The API and Command line have no row on
    the comparison page at all. Two hand-kept tables of the same claim, and a
    count above them that matched only by coincidence.

    Same parse as scripts/facts.py: a labelled row, skipping the header rule,
    the `route` header and the two-catalogue table's linked rows. The macro
    asserts its count against the facts file at build time, so the two
    cannot drift silently.
    """
    text = (ROOT / "docs" / "reference" / "comparison.md").read_text()
    rows = []
    for m in re.finditer(r"^\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|", text, re.M):
        label = m.group(1).strip()
        if not label or set(label) <= set("-: ") or label.lower() == "route":
            continue
        if label.startswith("["):
            continue
        rows.append((label, m.group(2).strip(), m.group(3).strip()))
    return rows


def _md_inline(s: str) -> str:
    """Bold and code, which is all the comparison cells use."""
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s


def _front_matter(path: pathlib.Path) -> dict:
    import yaml
    text = path.read_text()
    if not text.startswith("---"):
        return {}
    end = text.index("\n---", 3)
    return yaml.safe_load(text[3:end]) or {}


# Structured data for the FAQ: every "## question" with the prose under it.
#
# Capped, because an answer here can run to a screen and a rich result shows
# two lines of it. An answer that is a table or a code block is left out
# rather than flattened into something that reads as nonsense.
FAQ_ANSWER_CAP = 600


def _faq_entities(path: pathlib.Path) -> list[dict]:
    if not path.exists():
        return []
    text = path.read_text()
    out: list[dict] = []
    for m in re.finditer(r"^## +(.+?)\s*$", text, re.M):
        question = m.group(1).strip()
        body = text[m.end():]
        nxt = re.search(r"^## ", body, re.M)
        body = body[:nxt.start()] if nxt else body
        answer = []
        for line in body.splitlines():
            s = line.strip()
            if not s:
                if answer:
                    break                 # the first paragraph is the answer
                continue
            if s.startswith(("#", "|", "```", "!!!", "???", "<", "{", "- ",
                             "* ", ":")):
                break
            answer.append(s)
        a = " ".join(answer)
        a = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", a)
        a = re.sub(r"[*`]+", "", a)
        a = " ".join(a.split())
        if len(a) < 40:
            continue                      # not an answer, whatever it is
        if len(a) > FAQ_ANSWER_CAP:
            a = a[:FAQ_ANSWER_CAP].rsplit(" ", 1)[0] + "\u2026"
        out.append({"q": question, "a": a})
    return out
