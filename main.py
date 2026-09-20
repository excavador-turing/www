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
import pathlib
import re

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


def define_env(env):
    """Hook for mkdocs-macros."""

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
