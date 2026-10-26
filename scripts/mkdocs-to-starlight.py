#!/usr/bin/env python3
"""Render the MkDocs sources in docs/ into the Starlight project in starlight/.

MkDocs stays the source of truth until the switch, so nothing here edits
docs/. This reads it the way MkDocs reads it -- mkdocs.yml's nav, the macros
module, the blog plugin's posts -- and writes what Starlight needs:

  starlight/src/content/docs/   one .md (or .mdx) page per MkDocs page
  starlight/public/             every non-Markdown file under docs/, byte for byte
  starlight/src/data/           docs/data/ and the curated llms.txt, which the
                                components and routes read at build time
  starlight/src/generated/      sidebar, footer and per-page SEO data, as JSON

All four are git-ignored and rewritten on every run: the output is a pure
function of docs/, mkdocs.yml and the git history (for the "last updated"
dates), so running it twice changes nothing. The one exception is OWN_PUBLIC:
files in starlight/public/ that belong to the Starlight build itself (the
favicon), committed there, never written or removed by this script.

The rules that matter, and why:

  * Every URL MkDocs serves is the URL Starlight serves. Links are rewritten
    to absolute paths so the links validator can check them, never to new
    places.
  * Pages that opt into macros (`render_macros: true`) are NOT rendered here.
    Each `{{ ... }}` becomes the Astro component that does what main.py's
    macro does (starlight/src/components/macros/), and the page becomes .mdx:
    the numbers and lists are read from src/data/ and the content collection
    when the site is built, so they are as fresh as the data, and after the
    switch the converted page is the source with no Python behind it. An
    expression with no component is an error.
  * A Markdown extension this script does not know is an error, not a
    silent pass-through: an admonition that renders as literal `!!!` text is
    a broken page that builds green.

usage: scripts/mkdocs-to-starlight.py [--out starlight]
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

# Front matter keys MkDocs pages carry, and what becomes of each. A key not
# listed here stops the conversion: it means a page grew a meaning this
# script does not carry yet.
KNOWN_META = {
    "title", "description", "hide", "render_macros", "search", "robots",
    # Feature pages: passed through for FeatureScreen and FeaturePlates.
    "feature", "since",
    # Blog posts: date, URL, and the Open Graph picture.
    "date", "slug", "image",
}

# Material admonition types -> Starlight aside variants. Starlight has four;
# Material's "warning" is Starlight's "caution". Every type the site uses is
# here; an unknown one is an error rather than a guess.
ASIDE = {"note": "note", "tip": "tip", "warning": "caution", "danger": "danger"}

# Files under docs/ that are not copied to public/ as they are, because a
# route serves them: astro.config.mjs's `llmsTxt` switch decides whether
# /llms.txt is this curated file (scripts/llms.py, what the live site serves)
# or starlight-llms-txt's. A public file at a route's address is served over
# the route with a [WARN], which the strict build refuses -- so the file goes
# to src/data/ and the route serves it.
ROUTED = {
    "llms.txt": "src/data/llms.txt",
}

# Files in starlight/public/ that are the Starlight build's own, committed
# there rather than rendered from docs/: Starlight links /favicon.svg from
# every page, and MkDocs serves Material's theme icon instead, so there is
# nothing in docs/ to copy. sync() leaves them alone, and a docs/ file at the
# same path is an error rather than a silent overwrite.
OWN_PUBLIC = {"favicon.svg"}

# The macros main.py defines, and the component that does each one's job.
# The flag: the component writes the page's H1 itself, so Starlight's is not
# printed (tp.hideTitle).
MACRO_COMPONENTS = {
    # The page's front matter goes in: `frontmatter` is MDX's own, so the
    # component renders wherever the page does, in a route or in a plugin
    # that renders entries on their own (starlight-llms-txt).
    "feature_screen": ("FeatureScreen page={frontmatter}", True),
    "feature_plates": ("FeaturePlates", False),
    "board_reports": ("BoardReports", False),
    "comparison_table": ("ComparisonTable", False),
    "news_lede": ("NewsLede", False),
}
# Jinja filters a fact may pass through; <Fact filters="..."> applies them
# in order (starlight/src/lib/facts.mjs). `.split()[0]` is the filter
# `first_word`.
FACT_FILTERS = {"title_number", "lower"}
# Where the components live, through the `~` alias in starlight/tsconfig.json.
MACROS_IMPORT = "~/components/macros"

# Elements HTML closes by itself and JSX does not: <img> is <img /> in MDX.
VOID_TAGS = ("img", "br", "hr", "source", "input", "wbr", "area", "col", "embed",
             "link", "meta", "track")

# Code fence languages Material's Pygments knows and Shiki does not.
LANG = {"promql": "txt"}

# python-markdown's block-level elements (markdown.util.BLOCK_LEVEL_ELEMENTS),
# which it passes through as raw HTML until the matching close tag, blank
# lines and all. CommonMark ends an HTML block at the first blank line, so
# these blocks lose their blank lines on the way over.
BLOCK_TAGS = set("""address article aside blockquote details div dl fieldset
figcaption figure footer form h1 h2 h3 h4 h5 h6 header hgroup hr main menu nav
ol p pre section table ul canvas colgroup dd body dt group html iframe li legend
math map noscript output object option progress script style summary tbody td
textarea tfoot th thead tr video center""".split())

FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})\s*([^`\s]*)(.*)$")
ADMON_RE = re.compile(r'^(\s*)(!!!|\?\?\?\+?)\s+([\w-]+)(?:\s+"(.*)")?\s*$')
TAB_RE = re.compile(r'^(\s*)===(\+?)\s+"(.*)"\s*$')
OPEN_RE = re.compile(r"^(\s*)<([a-zA-Z][\w-]*)(\s[^>]*)?>")
MD_ATTR_RE = re.compile(r'\s+markdown(?:="(?:1|block)")?(?=[\s>/])')


class ConvertError(Exception):
    pass


# --------------------------------------------------------------------------
# mkdocs.yml, the nav, and where each page lives
# --------------------------------------------------------------------------

def load_config() -> dict:
    return yaml.safe_load((ROOT / "mkdocs.yml").read_text())


def blog_config(conf: dict) -> dict:
    for p in conf.get("plugins", []):
        if isinstance(p, dict) and "blog" in p:
            return p["blog"] or {}
    return {}


def macros_config(conf: dict) -> dict:
    for p in conf.get("plugins", []):
        if isinstance(p, dict) and "macros" in p:
            return p["macros"] or {}
    return {}


def walk_sources() -> list[str]:
    """Every file under docs/, in the order MkDocs walks them."""
    out = []
    for d, dirnames, filenames in os.walk(DOCS):
        dirnames.sort()
        dirnames[:] = [x for x in dirnames if not x.startswith(".")]
        filenames.sort(key=lambda f: (os.path.splitext(f)[0] not in ("index", "README"), f))
        for f in filenames:
            if f.startswith("."):
                continue
            out.append(os.path.relpath(os.path.join(d, f), DOCS).replace(os.sep, "/"))
    return out


def page_url(src: str) -> str:
    """docs-relative source -> the directory URL MkDocs serves it at."""
    stem = src[:-3]
    if stem == "index" or stem.endswith("/index") or stem.endswith("/README"):
        stem = stem.rsplit("/", 1)[0] if "/" in stem else ""
    return "/" + (stem + "/" if stem else "")


def nav_titles(nav, out=None) -> dict:
    out = {} if out is None else out
    for item in nav:
        if isinstance(item, str):
            continue
        (label, target), = item.items()
        if isinstance(target, list):
            nav_titles(target, out)
        elif not re.match(r"^[a-z]+://", target):
            out.setdefault(target, label)
    return out


def sidebar(nav, urls: dict) -> list:
    out = []
    for item in nav:
        (label, target), = item.items()
        if isinstance(target, list):
            out.append({"label": label, "items": sidebar(target, urls)})
        elif re.match(r"^[a-z]+://", target):
            out.append({"label": label, "link": target})
        else:
            if target not in urls:
                raise ConvertError(f"nav names {target}, which is not a page")
            out.append({"label": label, "link": urls[target]})
    return out


# --------------------------------------------------------------------------
# Front matter
# --------------------------------------------------------------------------

def split_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    m = re.match(r"^---[ \t]*\n(.*?\n)?---[ \t]*\n?", text, re.S)
    if not m:
        return {}, text
    return yaml.safe_load(m.group(1) or "") or {}, text[m.end():]


# --------------------------------------------------------------------------
# Macros: each `{{ ... }}` becomes a component
# --------------------------------------------------------------------------

EXPR_RE = re.compile(r"\{\{-?\s*(.*?)\s*-?\}\}", re.S)
CALL_RE = re.compile(r"(\w+)\(\)(?:\s*\|\s*indent\(\s*\d+\s*\))?")
FACT_RE = re.compile(r"([a-z_]\w*(?:\.\w+)*?)(\.split\(\)\[0\])?((?:\s*\|\s*\w+)*)")


def load_facts(conf: dict) -> dict:
    """The include_yaml files mkdocs-macros puts at the top level of the
    template variables; facts.yaml is the only one."""
    facts: dict = {}
    for el in macros_config(conf).get("include_yaml", []):
        key, fname = next(iter(el.items())) if isinstance(el, dict) else (None, el)
        p = ROOT / fname
        if p.is_file():
            data = yaml.safe_load(p.read_text()) or {}
            facts.update({key: data} if key else data)
    return facts


class Componentize:
    """`{{ gate.promoted }}` -> <Fact of="gate.promoted" />, and
    `{{ feature_screen() }}` -> <FeatureScreen />.

    mkdocs-macros expands Jinja before Markdown, inside code spans too: a
    fact quoted as `{{ faults.count }}` prints the number in code type, so it
    becomes <code><Fact .../></code>. Inside a fenced block it would be
    expanded as well -- the reason macros are opt-in per page -- and no page
    does that on purpose, so it is an error here."""

    def __init__(self, where: str, facts: dict):
        self.where = where
        self.facts = facts
        self.used: set[str] = set()
        self.renders_h1 = False

    def fact(self, path: str) -> None:
        v = self.facts
        for key in path.split("."):
            if not isinstance(v, dict) or key not in v:
                raise ConvertError(f"{self.where}: {{{{ {path} }}}} names no fact in facts.yaml")
            v = v[key]
        if isinstance(v, (dict, list)):
            raise ConvertError(f"{self.where}: {{{{ {path} }}}} is not a single value")

    def expr(self, expr: str) -> str:
        m = CALL_RE.fullmatch(expr)
        if m:
            name = m.group(1)
            if name not in MACRO_COMPONENTS:
                raise ConvertError(f"{self.where}: macro {name}() has no component")
            comp, h1 = MACRO_COMPONENTS[name]
            self.used.add(comp.split()[0])
            self.renders_h1 |= h1
            return f"<{comp} />"
        m = FACT_RE.fullmatch(expr)
        if m:
            path, first, pipes = m.groups()
            filters = [f.strip() for f in pipes.split("|") if f.strip()]
            bad = [f for f in filters if f not in FACT_FILTERS]
            if bad:
                raise ConvertError(f"{self.where}: {{{{ {expr} }}}}: no filter {bad[0]}")
            if first:
                filters.insert(0, "first_word")
            self.fact(path)
            self.used.add("Fact")
            f = f' filters="{" ".join(filters)}"' if filters else ""
            return f'<Fact of="{path}"{f} />'
        raise ConvertError(f"{self.where}: {{{{ {expr} }}}} has no component")

    def __call__(self, body: str) -> str:
        if re.search(r"\{%", body):
            raise ConvertError(f"{self.where}: Jinja statements ({{% ... %}}) are not converted")
        lines, out, i = body.split("\n"), [], 0
        while i < len(lines):
            m = FENCE_RE.match(lines[i])
            if m:
                fence = m.group(2)
                j = i + 1
                while j < len(lines) and not re.match(
                        rf"^\s*{re.escape(fence[0])}{{{len(fence)},}}\s*$", lines[j]):
                    j += 1
                block = lines[i:j + 1]
                if any(EXPR_RE.search(l) for l in block):
                    raise ConvertError(f"{self.where}: a macro inside a fenced block")
                out.extend(block)
                i = j + 1
                continue
            line = lines[i]
            # `{{ x }}` in a code span: the value, in code type.
            line = re.sub(r"(?<!`)`(\{\{[^`]*?\}\})`(?!`)", r"<code>\1</code>", line)
            out.append(EXPR_RE.sub(lambda m: self.expr(m.group(1).strip()), line))
            i += 1
        return "\n".join(out)


# --------------------------------------------------------------------------
# Block structure: admonitions, details, tabs, md_in_html, raw HTML
# --------------------------------------------------------------------------

def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _dedent(lines: list[str], n: int) -> list[str]:
    return [l[n:] if l[:n].strip() == "" else l.lstrip(" ") for l in lines]


def _indented_body(lines: list[str], i: int, need: int) -> tuple[list[str], int]:
    """Lines from i that belong to a block indented at least `need` columns."""
    body = []
    while i < len(lines):
        l = lines[i]
        if l.strip() == "" or _indent(l) >= need:
            body.append(l)
            i += 1
        else:
            break
    while body and body[-1].strip() == "":
        body.pop()
        i -= 1
    return body, i


def _tag_balance(line: str, tag: str) -> int:
    opens = len(re.findall(rf"<{tag}(?=[\s>/])", line, re.I))
    selfc = len(re.findall(rf"<{tag}\b[^>]*/>", line, re.I))
    closes = len(re.findall(rf"</{tag}\s*>", line, re.I))
    return opens - selfc - closes


def _matching_close(lines: list[str], i: int, tag: str) -> int:
    """Index of the line that closes the element opened on lines[i]."""
    depth = 0
    for j in range(i, len(lines)):
        depth += _tag_balance(lines[j], tag)
        if depth <= 0:
            return j
    raise ConvertError(f"<{tag}> opened and never closed: {lines[i].strip()[:60]}")


class Blocks:
    def __init__(self, where: str):
        self.where = where
        self.mdx = False

    def convert(self, lines: list[str]) -> list[str]:
        out: list[str] = []
        i = 0
        while i < len(lines):
            line = lines[i]

            m = FENCE_RE.match(line)
            if m:
                ind, fence, lang, rest = m.groups()
                j = i + 1
                while j < len(lines) and not re.match(
                        rf"^\s*{re.escape(fence[0])}{{{len(fence)},}}\s*$", lines[j]):
                    j += 1
                lang = LANG.get(lang, lang)
                out.append(f"{ind}{fence}{lang}{rest}")
                out.extend(lines[i + 1:j + 1])
                i = j + 1
                continue

            m = ADMON_RE.match(line)
            if m:
                ind, kind, typ, title = m.groups()
                body, i = _indented_body(lines, i + 1, len(ind) + 4)
                inner = self.convert(_dedent(body, len(ind) + 4))
                out.extend(self._admonition(ind, kind, typ, title, inner))
                continue

            m = TAB_RE.match(line)
            if m:
                ind = m.group(1)
                tabs = []
                while i < len(lines):
                    t = TAB_RE.match(lines[i])
                    if not t or t.group(1) != ind:
                        break
                    body, i = _indented_body(lines, i + 1, len(ind) + 4)
                    tabs.append((t.group(3), self.convert(_dedent(body, len(ind) + 4))))
                    while i < len(lines) and lines[i].strip() == "" and \
                            i + 1 < len(lines) and TAB_RE.match(lines[i + 1] or "") and \
                            TAB_RE.match(lines[i + 1]).group(1) == ind:
                        i += 1
                out.extend(self._tabs(ind, tabs))
                continue

            m = OPEN_RE.match(line)
            if m and m.group(2).lower() in BLOCK_TAGS and _indent(line) <= 3 or \
                    (m and MD_ATTR_RE.search(line.split(">", 1)[0] + ">")):
                ind, tag = m.group(1), m.group(2).lower()
                head = line.split(">", 1)[0] + ">"
                if MD_ATTR_RE.search(head):
                    if line.strip() != head.strip():
                        raise ConvertError(f"{self.where}: content on the line of a "
                                           f"markdown element: {line.strip()[:60]}")
                    j = _matching_close(lines, i, tag)
                    if lines[j].strip() != f"</{tag}>":
                        raise ConvertError(f"{self.where}: </{tag}> shares a line: "
                                           f"{lines[j].strip()[:60]}")
                    inner = self.convert(lines[i + 1:j])
                    out.append(MD_ATTR_RE.sub("", head, count=1))
                    out.append("")
                    out.extend(inner)
                    out.append("")
                    out.append(lines[j])
                    i = j + 1
                    continue
                j = _matching_close(lines, i, tag)
                raw = lines[i:j + 1]
                if tag != "pre":
                    raw = [l for l in raw if l.strip() != ""]
                out.extend(raw)
                i = j + 1
                continue

            if re.match(r"^\s*-{2}8<-{2}", line):
                raise ConvertError(f"{self.where}: pymdownx.snippets include is not converted")
            out.append(line)
            i += 1
        return out

    def _admonition(self, ind, kind, typ, title, inner):
        if typ not in ASIDE:
            raise ConvertError(f"{self.where}: admonition type {typ!r} has no aside")
        title = typ.capitalize() if title is None else title
        if kind == "!!!":
            # A titled aside: :::caution[Title]. Material's title replaces
            # the type's word, and so does Starlight's label.
            label = f"[{title}]" if title else ""
            return ([f"{ind}:::{ASIDE[typ]}{label}"] + [ind + l if l else l for l in inner]
                    + [f"{ind}:::"])
        # ??? is a collapsible block (pymdownx.details) -- closed, unless ???+.
        # A Starlight aside cannot be closed, and three hundred and fifty of
        # these hold a whole changelog entry each, so they stay <details>.
        opened = " open" if kind.endswith("+") else ""
        return ([f'{ind}<details class="{typ}"{opened}>',
                 f"{ind}<summary>{html.escape(title, quote=False)}</summary>", ""]
                + [ind + l if l else l for l in inner]
                + ["", f"{ind}</details>"])

    def _tabs(self, ind, tabs):
        self.mdx = True
        out = [f"{ind}<Tabs>"]
        for label, body in tabs:
            out += [f"{ind}<TabItem label={json.dumps(label)}>", ""]
            out += [ind + l if l else l for l in body]
            out += ["", f"{ind}</TabItem>"]
        out.append(f"{ind}</Tabs>")
        return out


# --------------------------------------------------------------------------
# Inline: links, attr_list, raw HTML URLs -- with code kept out of reach
# --------------------------------------------------------------------------

class Masked:
    """Code (fenced and inline) swapped for placeholders while the text
    around it is rewritten, so a link-shaped string in a code sample stays
    exactly as written."""

    def __init__(self, text: str):
        self.saved: list[str] = []
        lines, out, i = text.split("\n"), [], 0
        while i < len(lines):
            m = FENCE_RE.match(lines[i])
            if m:
                fence = m.group(2)
                j = i + 1
                while j < len(lines) and not re.match(
                        rf"^\s*{re.escape(fence[0])}{{{len(fence)},}}\s*$", lines[j]):
                    j += 1
                out.append(self._save("\n".join(lines[i:j + 1])))
                i = j + 1
                continue
            out.append(lines[i])
            i += 1
        text = "\n".join(out)
        text = re.sub(r"(?<!`)(`+)(?!`)((?:(?!\n\s*\n).)+?)(?<!`)\1(?!`)",
                      lambda m: self._save(m.group(0)), text, flags=re.S)
        self.text = text

    def _save(self, s: str) -> str:
        self.saved.append(s)
        return f"\x00{len(self.saved) - 1}\x00"

    def restore(self, text: str) -> str:
        while "\x00" in text:
            text = re.sub(r"\x00(\d+)\x00", lambda m: self.saved[int(m.group(1))], text)
        return text


def _is_external(u: str) -> bool:
    return bool(re.match(r"^([a-z][a-z0-9+.-]*:|//|#|\{)", u, re.I)) or u == ""


def _join(base_dir: str, rel: str, clamp: bool = False) -> str:
    """posixpath.normpath of a docs-relative directory and a relative path.
    A browser resolving a URL stops at the root (clamp); MkDocs resolving a
    source path has nowhere above docs/ to go, so that is an error."""
    parts = [p for p in (base_dir + "/" + rel).split("/") if p not in ("", ".")]
    out: list[str] = []
    for p in parts:
        if p == "..":
            if not out:
                if clamp:
                    continue
                raise ConvertError(f"{rel} climbs out of docs/")
            out.pop()
        else:
            out.append(p)
    return "/".join(out)


class Links:
    def __init__(self, src_to_url: dict, where: str, src: str, url: str):
        self.src_to_url = src_to_url
        self.where = where
        self.src_dir = src.rsplit("/", 1)[0] if "/" in src else ""
        self.url = url

    def markdown_target(self, target: str) -> str:
        """MkDocs resolves a Markdown link against the SOURCE file."""
        if _is_external(target) or target.startswith("/"):
            return target
        path, frag = (target.split("#", 1) + [""])[:2]
        path, query = (path.split("?", 1) + [""])[:2]
        if path.endswith(".md"):
            resolved = _join(self.src_dir, path)
            if resolved not in self.src_to_url:
                raise ConvertError(f"{self.where}: link to {target}, which is not a page")
            out = self.src_to_url[resolved]
        elif path and (DOCS / _join(self.src_dir, path, clamp=True)).is_file():
            out = "/" + _join(self.src_dir, path)
        else:
            # Not a file MkDocs knows (a directory URL, say): it leaves the
            # link alone and the browser resolves it against the page.
            return self.html_target(target)
        return out + (f"?{query}" if query else "") + (f"#{frag}" if frag else "")

    def html_target(self, target: str) -> str:
        """Raw HTML is untouched by MkDocs, so the browser resolves it
        against the SERVED URL. The URLs are the same on both sites; making
        them absolute only lets the links validator see them."""
        if _is_external(target) or target.startswith("/"):
            return target
        base = self.url.strip("/")
        path, rest = re.match(r"^([^?#]*)(.*)$", target).groups()
        joined = _join(base, path, clamp=True) if path else base
        out = "/" + joined
        if (path.endswith("/") or path == "" or path.endswith("..")) and joined:
            out += "/"
        return out + rest


def _attr_list(spec: str) -> dict:
    attrs: dict = {"class": []}
    for tok in re.findall(r'[.#][\w-]+|[\w-]+=(?:"[^"]*"|\'[^\']*\'|\S+)', spec):
        if tok[0] == ".":
            attrs["class"].append(tok[1:])
        elif tok[0] == "#":
            attrs["id"] = tok[1:]
        else:
            k, v = tok.split("=", 1)
            attrs[k] = v.strip("\"'")
    rest = re.sub(r'[.#][\w-]+|[\w-]+=(?:"[^"]*"|\'[^\']*\'|\S+)', "", spec).strip()
    if rest:
        raise ConvertError(f"attr_list {{{spec}}} has a part this does not read: {rest}")
    return attrs


def _attrs_html(attrs: dict) -> str:
    out = []
    if attrs.get("id"):
        out.append(f'id="{html.escape(attrs["id"])}"')
    if attrs.get("class"):
        out.append(f'class="{html.escape(" ".join(attrs["class"]))}"')
    for k, v in attrs.items():
        if k not in ("id", "class"):
            out.append(f'{k}="{html.escape(v)}"')
    return " ".join(out)


LINK_RE = re.compile(
    r"(!?)\[((?:[^\[\]\x00]|\x00\d+\x00|\[[^\[\]]*\])*)\]\(\s*(<[^>]*>|[^\s()]+(?:\([^\s()]*\))?)"
    r"(\s+\"[^\"]*\")?\s*\)(\{\s*:?\s*([^{}]*?)\s*\})?")


def rewrite_inline(text: str, links: Links) -> str:
    masked = Masked(text)
    t = masked.text

    def link(m):
        bang, label, target, title, attr, spec = m.groups()
        target = target[1:-1] if target.startswith("<") else target
        href = links.markdown_target(target)
        if not attr:
            return f"{bang}[{label}]({href}{title or ''})"
        attrs = _attr_list(spec)
        if bang:
            alt = html.escape(masked.restore(label))
            # Self-closed, which HTML ignores and MDX requires.
            return f'<img src="{html.escape(href)}" alt="{alt}" {_attrs_html(attrs)} />'.replace("  ", " ")
        return f'<a href="{html.escape(href)}" {_attrs_html(attrs)}>{label}</a>'

    t = LINK_RE.sub(link, t)

    # Reference definitions: [id]: target
    t = re.sub(r"(?m)^(\s{0,3}\[[^\]]+\]:\s*)(\S+)",
               lambda m: m.group(1) + links.markdown_target(m.group(2)), t)

    # Raw HTML attributes that hold a URL.
    t = re.sub(r'(<[a-zA-Z][^<>]*?\s(?:href|src)=")([^"]*)(")',
               lambda m: m.group(1) + links.html_target(html.unescape(m.group(2))) + m.group(3), t)

    # Anything still shaped like attr_list after a link is a placement this
    # does not handle (a heading, a paragraph): stop rather than print it.
    stray = re.search(r"(?m)(^\{:.*\}\s*$|^#{1,6} .*\{\s*[#.][^}]*\}\s*$)", t)
    if stray:
        raise ConvertError(f"{links.where}: attr_list placement not converted: {stray.group(0)}")
    return masked.restore(t)


# --------------------------------------------------------------------------
# MDX: what a page needs before MDX will read it as the HTML it was
# --------------------------------------------------------------------------

def mdx_safe(where: str, text: str) -> str:
    """Raw HTML that python-markdown passes through and MDX parses as JSX.

    Three things differ, and each is rewritten: an HTML comment is a JSX
    comment, a void element is self-closed, and an inline <script> keeps its
    body as a string (`set:html`), because its braces are JavaScript, not MDX
    expressions. Anything else MDX would misread -- a stray brace, `<` that
    opens no tag, an autolink -- stops the conversion (check_mdx)."""
    masked = Masked(text)
    t = masked.text

    def comment(m):
        body = m.group(1)
        if "*/" in body:
            raise ConvertError(f"{where}: an HTML comment holds */")
        return "{/*" + body + "*/}"
    t = re.sub(r"<!--(.*?)-->", comment, t, flags=re.S)

    def script(m):
        attrs, body = m.group(1) or "", m.group(2)
        if re.search(r"\bsrc=", attrs):
            raise ConvertError(f"{where}: <script src> is not converted")
        return f"<script{attrs} set:html={{{json.dumps(masked.restore(body))}}} />"
    t = re.sub(r"<script(\s[^>]*)?>(.*?)</script>", script, t, flags=re.S)

    t = re.sub(rf"<({'|'.join(VOID_TAGS)})(\s[^<>]*?)?\s*(?<!/)>",
               lambda m: f"<{m.group(1)}{m.group(2) or ''} />", t)
    return masked.restore(t)


# --------------------------------------------------------------------------
# Headings
# --------------------------------------------------------------------------

def plain(md: str) -> str:
    s = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", md)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"[*_`]+", "", s)
    return html.unescape(s).strip()


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------

def git_date(src: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", f"docs/{src}"],
            cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    return out or None


def as_date(v) -> dt.date | None:
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    if isinstance(v, str) and v:
        return dt.date.fromisoformat(v[:10])
    return None


def yaml_front(fm: dict) -> str:
    return "---\n" + yaml.safe_dump(fm, sort_keys=False, allow_unicode=True,
                                    width=10_000) + "---\n"


class Site:
    def __init__(self, out: pathlib.Path):
        self.out = out
        self.conf = load_config()
        self.base = (self.conf.get("site_url") or "").rstrip("/")
        self.site_name = self.conf["site_name"]
        self.site_desc = self.conf.get("site_description", "")
        self.blog = blog_config(self.conf)
        self.blog_dir = self.blog.get("blog_dir", "blog").strip("/")
        self.nav_title = nav_titles(self.conf.get("nav", []))
        self.facts = load_facts(self.conf)
        self.files: dict[str, bytes | pathlib.Path] = {}
        self.seo: dict[str, dict] = {}
        self.notes: list[str] = []

    # -- inventory --------------------------------------------------------

    def inventory(self):
        self.pages: dict[str, dict] = {}
        self.assets: list[str] = []
        posts_prefix = f"{self.blog_dir}/posts/"
        for src in walk_sources():
            if not src.endswith(".md"):
                self.assets.append(src)
                continue
            meta, body = split_front_matter((DOCS / src).read_text())
            unknown = set(meta) - KNOWN_META
            if unknown:
                raise ConvertError(f"{src}: front matter key(s) {sorted(unknown)} "
                                   f"are not converted; add them to KNOWN_META deliberately")
            is_post = src.startswith(posts_prefix)
            if is_post:
                if "slug" not in meta or "date" not in meta:
                    raise ConvertError(f"{src}: a post needs slug and date")
                # The news index shows each post up to this marker
                # (starlight/src/components/macros/PostList.astro), as the
                # blog plugin does; `post_excerpt: required` makes it a must.
                if self.blog.get("post_excerpt") == "required" and "<!-- more -->" not in body:
                    raise ConvertError(f"{src}: no <!-- more --> excerpt marker")
                url = "/" + self.blog_dir + "/" + self.blog.get(
                    "post_url_format", "{date}/{slug}").format(slug=meta["slug"]).strip("/") + "/"
            else:
                url = page_url(src)
            self.pages[src] = {"src": src, "meta": meta, "body": body, "url": url,
                               "post": is_post}
        # Two sources, one URL: MkDocs writes both and the one it walks last
        # is what is served -- reference/api/index.md over reference/api.md.
        by_url: dict[str, str] = {}
        for src, p in self.pages.items():
            if p["url"] in by_url:
                lost = by_url[p["url"]]
                self.notes.append(f"{lost} is shadowed by {src} at {p['url']}, as in MkDocs")
                self.pages[lost]["shadowed"] = True
            by_url[p["url"]] = src
        self.src_to_url = {s: p["url"] for s, p in self.pages.items()}

    # -- one page ---------------------------------------------------------

    def page_title(self, p: dict, h1: str | None) -> str:
        """MkDocs' page.title: the nav's label, else the front matter's
        title, else the first H1. Open Graph and the breadcrumb use this one."""
        if p.get("src") in self.nav_title:
            return self.nav_title[p["src"]]
        if p["meta"].get("title"):
            return str(p["meta"]["title"])
        if h1:
            return h1
        stem = p["src"].rsplit("/", 1)[-1][:-3]
        return stem.replace("-", " ").replace("_", " ").capitalize()

    def html_title(self, p: dict, h1: str | None) -> str:
        """Material's <title>: the front matter's title first, then
        page.title. The two differ on five pages -- /changelog/ is
        "Changelogs" in the tab and "Every component" in a link preview."""
        if p["meta"].get("title"):
            return str(p["meta"]["title"])
        return self.page_title(p, h1)

    def render(self, p: dict) -> tuple[str, bool, Componentize | None]:
        meta, body = p["meta"], p["body"]
        comp = None
        if meta.get("render_macros") is True:
            comp = Componentize(p["src"], self.facts)
            body = comp(body)
        blocks = Blocks(p["src"])
        lines = blocks.convert(body.split("\n"))
        text = "\n".join(lines)
        text = rewrite_inline(text, Links(self.src_to_url, p["src"], p["src"], p["url"]))
        return text, blocks.mdx or bool(comp and comp.used), comp

    def check_mdx(self, src: str, text: str):
        """What MDX would read as code, or refuse, after mdx_safe(): a brace
        that is not a component's, a comment or a script's; `<` that opens
        no tag; an autolink."""
        masked = Masked(text).text
        masked = re.sub(r"\{/\*.*?\*/\}", "", masked, flags=re.S)
        masked = re.sub(r'set:html=\{"(?:[^"\\]|\\.)*"\}', "", masked)
        masked = masked.replace("={frontmatter}", "")
        masked = re.sub(r"^import \{[^}]*\} from '[^']*';$", "", masked, flags=re.M)
        bad = re.search(r"[{}]|<!--|<(?![a-zA-Z/])|<https?:", masked)
        if bad:
            raise ConvertError(f"{src}: is .mdx, and carries {bad.group(0)!r} "
                               f"that MDX would misread: {masked[max(0, bad.start() - 40):bad.end() + 20]!r}")

    def page(self, p: dict):
        meta = p["meta"]
        text, mdx, comp = self.render(p)
        is_index = p["src"] == f"{self.blog_dir}/index.md"

        # Starlight prints the title as the page's H1. Where the page opens
        # with its own H1, that H1 becomes the title and leaves the body;
        # where its H1 sits inside a layout block (the front page, Features,
        # News) or a component writes it (a feature page's FeatureScreen),
        # the page keeps it and Starlight's is not printed.
        m = re.match(r"^\s*# (.+?)\s*#*\s*(?:\n|$)", text)
        if m and "<" in m.group(1) and re.search(r"<[A-Z]", m.group(1)):
            raise ConvertError(f"{p['src']}: a component in the page's leading H1 is not converted")
        h1 = plain(m.group(1)) if m else None
        if m:
            text = text[m.end():]
        title = self.page_title(p, h1)
        # The visible heading: the page's own H1, or the one Material inserts
        # when there is none, which is page.title.
        shown = h1 or title
        own_h1 = not m and (bool(re.search(r"(?m)^\s*# |<h1[\s>]", text))
                            or bool(comp and comp.renders_h1))
        if "{{" in shown or "{%" in shown:
            raise ConvertError(f"{p['src']}: a macro in the title is not rendered")

        hide = set(meta.get("hide") or [])
        unknown_hide = hide - {"navigation", "toc"}
        if unknown_hide:
            raise ConvertError(f"{p['src']}: hide: {sorted(unknown_hide)} is not converted")

        fm: dict = {"title": shown}
        if meta.get("description"):
            fm["description"] = str(meta["description"])
        fm["slug"] = p["url"].strip("/") or "index"
        if "navigation" in hide:
            fm["template"] = "splash"
        if "toc" in hide:
            fm["tableOfContents"] = False
        if (meta.get("search") or {}).get("exclude"):
            fm["pagefind"] = False
        updated = git_date(p["src"])
        if updated:
            fm["lastUpdated"] = dt.date.fromisoformat(updated)
        # What the components read off the page itself: a post's date (the
        # news index, the post's own header), a feature page's `feature:`
        # block and `since:` (FeatureScreen, FeaturePlates).
        if p["post"]:
            fm["date"] = as_date(meta["date"])
        for key in ("feature", "since"):
            if key in meta:
                fm[key] = meta[key]
        if "feature" in meta and meta.get("title"):
            # The feature's own name, which its first screen and its plate
            # print (main.py: `meta.get("title") or page.title`). It can
            # differ from the nav's label, which is the page's `title` here.
            fm["feature"] = {"title": str(meta["title"]), **meta["feature"]}
        tp: dict = {}
        if own_h1:
            tp["hideTitle"] = True
        if tp:
            fm["tp"] = tp

        imports = set(comp.used) if comp else set()
        if is_index:
            # The news index: its own head, then the posts, newest first.
            text = text.rstrip() + "\n\n<PostList />\n"
            imports.add("PostList")
            mdx = True

        ext = ".mdx" if mdx else ".md"
        if mdx:
            text = mdx_safe(p["src"], text)
            head = []
            if "<Tabs>" in text:
                head.append("import { Tabs, TabItem } from '@astrojs/starlight/components';")
            if imports:
                head.append(f"import {{ {', '.join(sorted(imports))} }} from '{MACROS_IMPORT}';")
            text = "\n".join(head) + "\n\n" + text.lstrip("\n")
            self.check_mdx(p["src"], text)
        rel = "index" if p["url"] == "/" else p["url"].strip("/")
        if p["src"].endswith("index.md") and p["url"] != "/":
            rel += "/index"
        self.emit_page(rel + ext, fm, text)
        self.seo_for(p, title, self.html_title(p, h1))

    def emit_page(self, rel: str, fm: dict, text: str):
        self.files[f"src/content/docs/{rel}"] = (yaml_front(fm) + "\n" + text.strip("\n")
                                                 + "\n").encode()

    # -- the blog ----------------------------------------------------------
    #
    # The posts are pages (news/<slug>.md, with a `date`); the index and its
    # later pages are components that list them (PostList, and the route
    # src/pages/news/page/[page].astro), so a new post needs nothing here.
    # Only the later pages' <head> data is written, as for every page.

    def blog_pages(self):
        per = int(self.blog.get("pagination_per_page", 10))
        # PostList pages by its own constant; the two must agree, or the
        # later pages' <head> data below would be written for pages that
        # do not exist (or not written for ones that do).
        news_ts = (self.out / "src" / "lib" / "news.ts").read_text()
        m = re.search(r"POSTS_PER_PAGE = (\d+);", news_ts)
        if not m or int(m.group(1)) != per:
            raise ConvertError(f"mkdocs.yml pages the blog by {per}; starlight/src/lib/news.ts "
                               f"POSTS_PER_PAGE says {m and m.group(1)}")
        posts = sum(1 for p in self.pages.values() if p["post"])
        total = max(1, -(-posts // per))
        index = self.pages[f"{self.blog_dir}/index.md"]
        for n in range(2, total + 1):
            url = f"/{self.blog_dir}/page/{n}/"
            title = self.page_title(index, None)
            self.seo_for({"src": None, "meta": index["meta"], "url": url, "post": False},
                         title, self.html_title(index, None))

    # -- SEO: what overrides/main.html writes into <head> -------------------

    def seo_for(self, p: dict, title: str, html_title: str):
        meta = p["meta"]
        url = p["url"]
        home = url == "/"
        canonical = self.base + url
        og_title = self.site_name if home else plain(title)
        og_desc = meta.get("description") or self.site_desc
        image = meta.get("image") if p.get("post") or p.get("src") else None
        og_image = (f"{self.base}/assets/{image}" if image
                    else f"{self.base}/assets/captures/power-control.png")
        entry: dict = {
            "title": (f"{plain(html_title)} - {self.site_name}" if p["meta"].get("title") or not home
                      else self.site_name),
            "robots": meta.get("robots"),
            "ogType": "article" if p["post"] else "website",
            "ogTitle": og_title,
            "ogDescription": og_desc,
            "ogUrl": canonical,
            "ogImage": og_image,
            "published": str(as_date(meta["date"])) if p["post"] and meta.get("date") else None,
            "jsonld": [],
        }
        facts = self.facts
        if home:
            fw = ((facts.get("releases") or {}).get("firmware") or {}).get("newest", "")
            app = {
                "@context": "https://schema.org",
                "@type": "SoftwareApplication",
                "name": self.site_name,
                "alternateName": "Turing Pi 2 BMC firmware (excavador-turing fork)",
                "applicationCategory": "DeveloperApplication",
                "operatingSystem": "Turing Pi 2 BMC (Buildroot Linux, ARMv7)",
            }
            if fw:
                app["softwareVersion"] = fw
            app.update({
                "license": "https://github.com/excavador-turing/BMC-Firmware/blob/hive/LICENSE",
                "codeRepository": "https://github.com/excavador-turing/BMC-Firmware",
                "isAccessibleForFree": True,
                "url": f"{self.base}/",
                "description": og_desc,
                "image": og_image,
            })
            entry["jsonld"].append(app)
        elif p["post"]:
            post = {
                "@context": "https://schema.org",
                "@type": "BlogPosting",
                "headline": og_title,
                "description": og_desc,
                "image": og_image,
                "url": canonical,
                "mainEntityOfPage": canonical,
            }
            if meta.get("date"):
                post["datePublished"] = str(as_date(meta["date"]))
            post["isPartOf"] = {"@type": "Blog", "name": f"{self.site_name} news",
                                "url": f"{self.base}/{self.blog_dir}/"}
            about = {"@type": "SoftwareApplication", "name": self.site_name}
            if meta.get("slug"):
                about["softwareVersion"] = str(meta["slug"])
            about.update({"operatingSystem": "Turing Pi 2 BMC (Buildroot Linux, ARMv7)",
                          "applicationCategory": "DeveloperApplication"})
            post["about"] = about
            entry["jsonld"].append(post)
        elif p.get("src") == "faq.md":
            # The questions are read off the page when it is built
            # (starlight/src/lib/faq.ts, from the route middleware), so the
            # structured data follows the page with nothing to regenerate.
            entry["jsonld"].append({
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "url": canonical,
                "mainEntity": [],
            })
        if not home:
            # Material's ancestors: nav sections carry no URL and drop out,
            # so a page's trail is the site and itself -- except a post, whose
            # parent is the blog index. (The index's later pages have none.)
            crumbs = [{"@type": "ListItem", "position": 1, "name": self.site_name,
                       "item": f"{self.base}/"}]
            if p["post"]:
                index = self.pages[f"{self.blog_dir}/index.md"]
                crumbs.append({"@type": "ListItem", "position": 2,
                               "name": self.page_title(index, None),
                               "item": f"{self.base}/{self.blog_dir}/"})
            crumbs.append({"@type": "ListItem", "position": len(crumbs) + 1,
                           "name": og_title, "item": canonical})
            entry["jsonld"].append({"@context": "https://schema.org",
                                    "@type": "BreadcrumbList",
                                    "itemListElement": crumbs})
        self.seo[url] = {k: v for k, v in entry.items() if v not in (None, [])}

    # -- the rest ----------------------------------------------------------

    def footer(self) -> dict:
        extra = self.conf.get("extra") or {}

        def href(h: str) -> str:
            if re.match(r"^[a-z]+://|^#", h):
                return h
            return "/" + h.lstrip("/")
        return {
            "columns": [{"title": c["title"],
                         "links": [{"text": l["text"], "href": href(l["href"]),
                                    "external": l["href"].startswith("http")}
                                   for l in c["links"]]}
                        for c in extra.get("footer", [])],
            "social": [{"icon": s["icon"], "link": s["link"], "name": s.get("name", "")}
                       for s in extra.get("social", [])],
        }

    def run(self):
        self.inventory()
        for src, p in self.pages.items():
            if p.get("shadowed"):
                continue
            self.page(p)
        self.blog_pages()
        for src in self.assets:
            if src in OWN_PUBLIC:
                raise ConvertError(f"docs/{src} would overwrite starlight/public/{src}, "
                                   f"which the Starlight build owns (OWN_PUBLIC)")
            if src in ROUTED:
                self.files[ROUTED[src]] = DOCS / src
                continue
            if src.startswith("data/"):
                # The data the components read. Also still public, as on the
                # live site, which serves docs/data/ like any other file.
                self.files[f"src/{src}"] = DOCS / src
            self.files[f"public/{src}"] = DOCS / src
        urls = {s: p["url"] for s, p in self.pages.items() if not p.get("shadowed")}
        gen = {
            "sidebar.json": sidebar(self.conf.get("nav", []), urls),
            "footer.json": self.footer(),
            "seo.json": dict(sorted(self.seo.items())),
            "site.json": {"title": self.site_name, "description": self.site_desc,
                          "site": self.base, "blogDir": self.blog_dir},
        }
        for name, data in gen.items():
            self.files[f"src/generated/{name}"] = (
                json.dumps(data, indent=2, ensure_ascii=False, default=str) + "\n").encode()
        self.sync()

    def sync(self):
        """Write what changed, delete what is no longer generated: the dev
        server sees only real changes, and a page removed from docs/ goes."""
        roots = ["src/content/docs", "public", "src/generated", "src/data"]
        written = changed = 0
        for rel, data in sorted(self.files.items()):
            dest = self.out / rel
            new = data.read_bytes() if isinstance(data, pathlib.Path) else data
            if not dest.is_file() or dest.read_bytes() != new:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(new)
                changed += 1
            written += 1
        removed = 0
        for r in roots:
            base = self.out / r
            if not base.exists():
                continue
            for f in sorted(base.rglob("*"), reverse=True):
                rel = f.relative_to(self.out).as_posix()
                if rel.startswith("public/") and rel[len("public/"):] in OWN_PUBLIC:
                    continue
                if f.is_file() and rel not in self.files:
                    f.unlink()
                    removed += 1
                elif f.is_dir() and not any(f.iterdir()):
                    f.rmdir()
        pages = sum(1 for k in self.files if k.startswith("src/content/docs/"))
        print(f"mkdocs-to-starlight: {pages} pages, "
              f"{sum(1 for k in self.files if k.startswith('public/'))} files, "
              f"{changed} written, {removed} removed")
        for n in self.notes:
            print(f"mkdocs-to-starlight: note: {n}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=str(ROOT / "starlight"),
                    help="the Starlight project to write into (default: starlight/)")
    args = ap.parse_args()
    try:
        Site(pathlib.Path(args.out).resolve()).run()
    except ConvertError as e:
        print(f"mkdocs-to-starlight: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
