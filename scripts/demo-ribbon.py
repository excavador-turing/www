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
    # A block in the normal flow, NOT position:fixed.
    #
    # It was fixed, with a 28px spacer below it to push the page down. That
    # holds on a desktop and breaks on a phone: the sentence wraps to two or
    # three lines, the ribbon grows to seventy pixels, the spacer stays at
    # twenty-eight, and the difference covers the top of the interface
    # underneath -- which on the stock firmware is exactly where its menu
    # button lives. A banner that hides the navigation of the thing it is
    # describing is worse than no banner.
    #
    # In the flow it occupies precisely its own height at every width, and
    # there is no second number to keep in agreement with the first.
    '<a id="tp-demo-ribbon" href="/#demo/{pane}" style="display:block;'
    'font:600 12px/1.45 system-ui,-apple-system,sans-serif;text-align:center;'
    'color:#2d3a00;background:#dcfe8e;text-decoration:none;padding:7px 12px;'
    'border-bottom:1px solid #b9dc5a">Demo of {what} \u2014 every reading is real, '
    'every control refuses and says why. \u2190 back to turingpi.xyz</a>'
    '<script>if(top!==self){{document.getElementById("tp-demo-ribbon").hidden=true}}</script>'
)

WHAT = {
    "fork": "this fork",
    "stock": "the stock firmware",
    "fleet": "the fleet interface",
}



def strip_ribbon(html: str) -> tuple[str, bool]:
    """Remove a previously inserted ribbon, including the spacer older
    versions added. Returns the html and whether anything was removed."""
    before = html
    html = re.sub(r'<a id="tp-demo-ribbon".*?</a>', "", html, flags=re.S)
    html = re.sub(r'<div id="tp-demo-ribbon-space".*?</div>', "", html, flags=re.S)
    html = re.sub(r'<script>if\(top!==self\).*?</script>', "", html, flags=re.S)
    return html, html != before

def main() -> int:
    for pane in ("fork", "stock", "fleet"):
        path = Path("docs/demo") / pane / "index.html"
        if not path.exists():
            print(f"  {path}: missing, skipped")
            continue
        html = path.read_text()
        # Replace an existing ribbon rather than skipping the file. Skipping
        # is what "idempotent" looked like, and it meant a change to the
        # ribbon could never reach a bundle that already carried one -- the
        # stock pane is committed WITH its ribbon, so it would have kept the
        # broken one forever.
        html, removed = strip_ribbon(html)
        if removed:
            print(f"  {path}: replacing the ribbon it already had")
        new, n = re.subn(r"(<body[^>]*>)", lambda m: m.group(1) + RIBBON.format(pane=pane, what=WHAT[pane]), html, count=1)
        if n != 1:
            print(f"  {path}: no <body> tag found", file=sys.stderr)
            return 1
        path.write_text(new)
        print(f"  {path}: ribbon added")
    return 0


if __name__ == "__main__":
    sys.exit(main())
