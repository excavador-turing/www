#!/usr/bin/env python3
"""Prove the pages that promise one screen still fit on one.

The front page, the demo, the about page, the features index and every feature
page are all written to be seen WITHOUT SCROLLING: a claim, its numbers, where
to go next, and the argument behind a disclosure. That promise is one careless
paragraph away from being false on every one of them at once.

So it is measured rather than asserted. This renders each built page in
headless Chrome at five real viewports and compares the document height to the
window. The shortest screen in the list, a 375x667 phone, is the one that
actually fails first -- it was 143px over when the desktop layout had room to
spare, which is why the stylesheet has a height-keyed tier at all.

Run it against a build: `just one-screen` (which builds first). It exits
non-zero and names every page and viewport that overflows.
"""
import asyncio
import http.server
import json
import pathlib
import socketserver
import subprocess
import sys
import threading
import time
import urllib.request

import websockets

# Width, height, and why this one is in the list.
VIEWPORTS = [
    ("laptop 1440x900", 1440, 900),
    ("laptop 1366x768", 1366, 768),   # wide and SHORT; fails before 1440x900
    ("tablet 768x1024", 768, 1024),
    ("phone 390x844", 390, 844),      # a current handset
    ("phone 375x667", 375, 667),      # the smallest screen still in use
]

# Chrome rounds, mkdocs-material's header has a sub-pixel border, and a
# retina scale factor moves both. A page one pixel over is not a page that
# scrolls.
SLOP = 4

ROOT = pathlib.Path(__file__).resolve().parent.parent


class Quiet(http.server.SimpleHTTPRequestHandler):
    """Every request logged is a line between the reader and the verdict."""

    def log_message(self, *args):
        pass


def serve(directory):
    """A local server, because file:// URLs break the site's absolute links."""
    handler = lambda *a, **kw: Quiet(*a, directory=str(directory), **kw)
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


async def measure(ws_url, url, w, h):
    async with websockets.connect(ws_url, max_size=None) as ws:
        i = 0

        async def send(method, params=None):
            nonlocal i
            i += 1
            await ws.send(json.dumps({"id": i, "method": method,
                                      "params": params or {}}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get("id") == i:
                    return msg

        await send("Emulation.setDeviceMetricsOverride",
                   {"width": w, "height": h, "deviceScaleFactor": 1,
                    "mobile": w < 500})
        await send("Page.enable")
        await send("Page.navigate", {"url": url})
        await asyncio.sleep(1.0)
        # Wait for the web fonts. Measured against the fallback face a page
        # wraps differently from the one a reader sees, and that showed up
        # as 40px of run-to-run jitter -- enough to call a page fitting when
        # it is not.
        for _ in range(30):
            r = await send("Runtime.evaluate",
                           {"expression": "document.fonts.status",
                            "returnByValue": True})
            if r["result"]["result"]["value"] == "loaded":
                break
            await asyncio.sleep(0.2)
        await asyncio.sleep(0.5)
        r = await send("Runtime.evaluate", {
            "expression": "JSON.stringify([document.documentElement.scrollHeight,"
                          "window.innerHeight])",
            "returnByValue": True})
        return json.loads(r["result"]["result"]["value"])


async def run(pages, port):
    chrome = subprocess.Popen(
        ["google-chrome", "--headless=new", "--disable-gpu", "--no-sandbox",
         "--hide-scrollbars", "--remote-debugging-port=9222", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        ws_url = None
        for _ in range(40):
            try:
                tabs = json.load(urllib.request.urlopen(
                    "http://127.0.0.1:9222/json"))
                ws_url = next(t["webSocketDebuggerUrl"] for t in tabs
                              if t["type"] == "page")
                break
            except Exception:
                time.sleep(0.5)
        if ws_url is None:
            print("chrome did not come up", file=sys.stderr)
            return 1

        over = []
        for path in pages:
            name = path.rstrip("/") or "/"
            row = [f"  {name:<36}"]
            for label, w, h in VIEWPORTS:
                scroll, inner = await measure(
                    ws_url, f"http://127.0.0.1:{port}/{path}", w, h)
                excess = scroll - inner
                if excess > SLOP:
                    over.append((name, label, excess))
                    row.append(f"{label}: OVER by {excess}")
                else:
                    row.append(f"{label}: fits")
            print("   ".join(row))

        if over:
            print(f"\n{len(over)} page/viewport pairs scroll:", file=sys.stderr)
            for name, label, excess in over:
                print(f"  {name} at {label}: {excess}px too tall",
                      file=sys.stderr)
            print("\nA feature page must fit one screen. Shorten the lead, or "
                  "move the detail into the disclosure.", file=sys.stderr)
            return 1
        print(f"\n  {len(pages)} pages x {len(VIEWPORTS)} viewports: all fit")
        return 0
    finally:
        chrome.terminate()


def main():
    site = ROOT / "site"
    if not (site / "index.html").exists():
        print("no build in site/ -- run `just build` first", file=sys.stderr)
        return 1
    features = sorted(p.stem for p in (ROOT / "docs" / "features").glob("*.md")
                      if p.stem != "index")
    if not features:
        print("no feature pages found", file=sys.stderr)
        return 1
    # The front page is three pages in one: the hash picks the view, so each
    # view is measured. `/demo/` is the redirect stub, which lands on the same
    # fork pane a reader reaches from anywhere else.
    pages = ["", "#demo/fork", "#demo/stock", "#demo/fleet",
             "about/", "features/"] + [f"features/{name}/" for name in features]
    httpd, port = serve(site)
    try:
        return asyncio.run(run(pages, port))
    finally:
        httpd.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
