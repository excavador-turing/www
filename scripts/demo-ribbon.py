#!/usr/bin/env python3
"""Give a demo bundle a way back out.

A visitor who lands on /demo/fork/ directly -- a shared link, a search hit --
is inside an application with no navigation of its own, and the only exit
is the back button. This inserts one line under the <body>: what the page
is, and a link home. When the same bundle is framed by the front page's demo
view the ribbon hides itself, because the front page already has the switch.

Idempotent: a second run over an already-ribboned file changes nothing, so
`just refresh-demo` can call it unconditionally after every rebuild.
"""
import re
import sys
from pathlib import Path

RIBBON = (
    '<a id="tp-demo-ribbon" href="/#demo/{pane}" style="position:fixed;top:0;left:0;right:0;'
    'z-index:2147483647;display:block;font:600 12px/28px system-ui,-apple-system,sans-serif;'
    'text-align:center;color:#2d3a00;background:#dcfe8e;text-decoration:none;'
    'border-bottom:1px solid #b9dc5a">Demo of {what} — every reading is real, every control '
    'refuses and says why. ← back to turingpi.xyz</a>'
    '<div id="tp-demo-ribbon-space" style="height:28px"></div>'
    '<script>if(top!==self){{for(const i of["tp-demo-ribbon","tp-demo-ribbon-space"])'
    'document.getElementById(i).hidden=true}}</script>'
)

WHAT = {"fork": "this fork", "stock": "the stock firmware"}


def main() -> int:
    for pane in ("fork", "stock"):
        path = Path("docs/demo") / pane / "index.html"
        if not path.exists():
            print(f"  {path}: missing, skipped")
            continue
        html = path.read_text()
        if 'id="tp-demo-ribbon"' in html:
            print(f"  {path}: already has the ribbon")
            continue
        new, n = re.subn(r"(<body[^>]*>)", lambda m: m.group(1) + RIBBON.format(pane=pane, what=WHAT[pane]), html, count=1)
        if n != 1:
            print(f"  {path}: no <body> tag found", file=sys.stderr)
            return 1
        path.write_text(new)
        print(f"  {path}: ribbon added")
    return 0


if __name__ == "__main__":
    sys.exit(main())
