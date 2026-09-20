#!/usr/bin/env python3
"""Prove every page reads correctly at every screen size.

This replaces `one-screen.py`, which asked one question -- does the document
scroll -- of seventeen pages at five viewports, and took 132 seconds of a
178-second deploy to do it. Three things were wrong with that:

  * It could not see the fault it existed to catch. The front page cuts its
    destination cards off mid-sentence -- 69px of text at 1280x720, 36px at
    1366x768 -- and gives their drawings a 501px box at 2560x1440 and a 90px
    one at 1280x720, because the picture is sized from whatever height the
    viewport had left. None of that scrolls, so all of it passed.
  * It measured whole documents. A page is allowed to scroll now; what must
    fit is each SCREEN, and a page says which of its parts are screens by
    marking them `data-screen`.
  * It was in the deploy path, where it was 132 of the 178 seconds a deploy
    took -- while building the site itself took 3. A layout regression should
    stop a merge, not a publish, so it runs in `checks.yml` on pull requests.

It is also about fifty times faster per measurement: 423 measurements in 10
seconds, against 85 in 132. The old one paid a page load and 1.5 seconds of
fixed sleeps every single time. This loads a page once, resizes it eight more
times, runs four tabs down one connection, and waits on real signals (`load`,
`document.fonts.ready`) rather than on the clock.

    just screens                 # every page in the built site
    just screens-baseline        # re-record the faults it is allowed to have
    scripts/screens.py --pages / '/#demo/fork'
    scripts/screens.py --no-baseline --json report.json

What it fails on, per page and viewport:

  fit       a `data-screen` section taller than the usable viewport
  clip      text cut off by an ancestor that hides its overflow
  aspect    an image box whose shape is not the picture's shape, which is how
            a picture sized from leftover height ends up as empty plate
  hscroll   the document wider than the window
"""
from __future__ import annotations

import argparse
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

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Nine, where there were five. The four that were missing are where the front
# page actually fails: it clips at 1280x720 and 1366x768, and hands a drawing
# a box over twice its own height at 2560x1440. The five the old list had --
# 1440x900 among them -- are all clean, which is how the fault survived.
# Height is what decides a fit, so the short ones are not optional.
VIEWPORTS = [
    ("laptop 1280x720", 1280, 720),
    ("laptop 1366x768", 1366, 768),
    ("laptop 1440x900", 1440, 900),
    ("laptop 1536x864", 1536, 864),
    ("desktop 1920x1080", 1920, 1080),
    ("desktop 2560x1440", 2560, 1440),
    ("tablet 768x1024", 768, 1024),
    ("phone 390x844", 390, 844),
    ("phone 375x667", 375, 667),
]

# Chrome rounds, Material's header carries a sub-pixel border, and a page one
# pixel over is not a page that scrolls.
SLOP = 4

# How far an image box may depart from the shape of the picture in it, in
# either direction. 1.5 is deliberately loose: it passes 1920x1080, where the
# front page's box is 242px around 223px of art and looks right, and catches
# 2560x1440, where the same box is 501px around 220px.
STRETCH = 1.5

# How many tabs measure at once. Four keeps a 2-core runner busy without the
# tabs contending for layout, which showed up as readings that moved between
# runs.
TABS = 4

MEASURE = """
(() => {
  const slop = %(slop)d, stretch = %(stretch)s;
  const vh = window.innerHeight, vw = window.innerWidth;

  // A sticky or fixed header eats the top of every screen below it, so the
  // usable height is not the window height. Anything else positioned that
  // way is the page's business, not ours.
  let chrome = 0;
  for (const el of document.querySelectorAll('header, .md-header, .md-tabs')) {
    const p = getComputedStyle(el).position;
    if (p === 'fixed' || p === 'sticky') chrome += el.getBoundingClientRect().height;
  }
  const usable = Math.round(vh - chrome);

  const out = { usable, viewport: [vw, vh], fit: [], clip: [], stretch: [], hscroll: null };

  // A screen is a part of a page that must be taken in at once. A page with
  // none is not making that promise and is only checked for the faults.
  //
  // The promise is made by the STYLESHEET, not by the markup: a section is
  // claiming to be a screen at this viewport only while its computed
  // min-height is viewport-sized. That is what lets a phone off -- a chapter
  // with a screenshot, a heading, a paragraph and three numbers does not fit
  // 667px, and the honest thing is to stack and scroll rather than to hide
  // half of it, which is what the layout this replaced did. Where the CSS
  // releases the min-height, the page has stopped promising and the gate
  // stops asking.
  for (const el of document.querySelectorAll('[data-screen]')) {
    const claimed = parseFloat(getComputedStyle(el).minHeight) || 0;
    if (claimed < usable * 0.5) continue;
    const h = Math.round(el.getBoundingClientRect().height);
    out.fit.push({ name: el.getAttribute('data-screen') || '(unnamed)', height: h,
                   over: h - usable });
  }

  // Text that an ancestor has cut off. `overflow: hidden` is how the front
  // page's cards lost the ends of their sentences at 1366x768 while the
  // document still fitted, so the old gate called it green.
  //
  // Scoped to what this site writes. Material's chrome clips on purpose --
  // a collapsed search field, a nav list behind a drawer, the repository
  // facts in the header -- and an unscoped rule reported 2219 of those and
  // buried the eight that were ours.
  const text = el => (el.innerText || '').trim();
  const scope = [...document.querySelectorAll('.md-content, [data-screen]')];
  const mine = new Set(scope.flatMap(s => [s, ...s.querySelectorAll('*')]));
  for (const el of mine) {
    const cs = getComputedStyle(el);
    if (cs.overflow === 'visible' || cs.display === 'none') continue;
    if (!['hidden', 'clip'].includes(cs.overflowY) &&
        !['hidden', 'clip'].includes(cs.overflowX)) continue;
    const overY = el.scrollHeight - el.clientHeight;
    const overX = el.scrollWidth - el.clientWidth;
    if (overY <= slop && overX <= slop) continue;
    const t = text(el);
    if (!t) continue;                       // a clipped decoration is fine
    if (el.closest('[data-screen-ignore]')) continue;
    // Report the innermost offender only: a clipped child clips its parents.
    if ([...el.querySelectorAll('*')].some(k => {
          if (!mine.has(k)) return false;
          const kc = getComputedStyle(k);
          return (['hidden','clip'].includes(kc.overflowY) || ['hidden','clip'].includes(kc.overflowX))
                 && (k.scrollHeight - k.clientHeight > slop || k.scrollWidth - k.clientWidth > slop)
                 && text(k);
        })) continue;
    out.clip.push({
      sel: el.tagName.toLowerCase() + (el.className && typeof el.className === 'string'
            ? '.' + el.className.trim().split(/\\s+/).slice(0, 2).join('.') : ''),
      overY, overX, text: t.slice(0, 60)
    });
  }

  // An image box whose shape is not the picture's shape. Symmetric on
  // purpose: a box far TALLER than the art renders as plates of empty
  // background (2560x1440 gave a 501px box to 220px of drawing), and a box
  // far SHORTER scales the art down and leaves the empty space at the sides
  // instead (1280x720 gave the same drawing 90px). Both come from the same
  // mistake -- sizing a picture from whatever height was left over rather
  // than from the picture.
  for (const img of scope.flatMap(s => [...s.querySelectorAll('img')])) {
    const r = img.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    if (!img.naturalWidth || !img.naturalHeight) continue;
    if (img.closest('[data-screen-ignore]')) continue;
    const natural = r.width * (img.naturalHeight / img.naturalWidth);
    const skew = Math.max(r.height / natural, natural / r.height);
    if (skew > stretch) {
      out.stretch.push({ src: (img.currentSrc || img.src).split('/').pop(),
                         box: Math.round(r.height), art: Math.round(natural),
                         how: r.height > natural ? 'stretched' : 'squashed' });
    }
  }

  const sw = document.documentElement.scrollWidth;
  if (sw > vw + slop) out.hscroll = sw - vw;
  return JSON.stringify(out);
})()
""" % {"slop": SLOP, "stretch": STRETCH}


class Quiet(http.server.SimpleHTTPRequestHandler):
    """Every request logged is a line between the reader and the verdict."""

    def log_message(self, *args):
        pass


def serve(directory: pathlib.Path):
    """A local server: file:// URLs break the site's absolute links."""
    handler = lambda *a, **kw: Quiet(*a, directory=str(directory), **kw)
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


class Browser:
    """One websocket to Chrome, one session per tab.

    The old script opened a fresh connection for every single measurement --
    seventeen pages times five viewports, so eighty-five connections and
    eighty-five page loads. This attaches to each tab once and talks to all
    of them down one socket, which is what the flat protocol is for.
    """

    def __init__(self, ws):
        self.ws = ws
        self.n = 0
        self.replies: dict[int, asyncio.Future] = {}
        self.events: dict[tuple[str, str], asyncio.Future] = {}
        self.reader = asyncio.create_task(self._read())

    async def _read(self):
        try:
            async for raw in self.ws:
                msg = json.loads(raw)
                if "id" in msg:
                    fut = self.replies.pop(msg["id"], None)
                    if fut and not fut.done():
                        fut.set_result(msg)
                else:
                    key = (msg.get("sessionId", ""), msg.get("method", ""))
                    fut = self.events.pop(key, None)
                    if fut and not fut.done():
                        fut.set_result(msg)
        except Exception:
            pass

    async def send(self, method, params=None, session=None):
        self.n += 1
        i = self.n
        fut = asyncio.get_running_loop().create_future()
        self.replies[i] = fut
        payload = {"id": i, "method": method, "params": params or {}}
        if session:
            payload["sessionId"] = session
        await self.ws.send(json.dumps(payload))
        msg = await asyncio.wait_for(fut, timeout=60)
        if "error" in msg:
            raise RuntimeError(f"{method}: {msg['error']}")
        return msg.get("result", {})

    def expect(self, session, method):
        """Arm a one-shot wait BEFORE the command that triggers the event."""
        fut = asyncio.get_running_loop().create_future()
        self.events[(session, method)] = fut
        return fut

    async def tab(self):
        t = await self.send("Target.createTarget", {"url": "about:blank"})
        a = await self.send("Target.attachToTarget",
                            {"targetId": t["targetId"], "flatten": True})
        s = a["sessionId"]
        await self.send("Page.enable", session=s)
        await self.send("Runtime.enable", session=s)
        return s

    async def goto(self, session, url):
        # about:blank first, so a URL that differs only by its hash still
        # gets a real load event instead of hanging waiting for one.
        for target in ("about:blank", url):
            loaded = self.expect(session, "Page.loadEventFired")
            await self.send("Page.navigate", {"url": target}, session=session)
            try:
                await asyncio.wait_for(loaded, timeout=30)
            except asyncio.TimeoutError:
                pass
        # Measured against a fallback face, a page wraps differently from the
        # one a reader sees. That was 40px of jitter in the old script, which
        # it covered with a sleep.
        await self.send("Runtime.evaluate", {
            "expression": "document.fonts.ready.then(()=>true)",
            "awaitPromise": True, "returnByValue": True}, session=session)

    async def settle(self, session):
        """Let a resize reach the renderer, then force layout.

        NOT requestAnimationFrame. A tab made with Target.createTarget is
        never shown, and Chrome does not run animation frames for a tab it is
        not painting -- the first draft hung here for sixty seconds on the
        first viewport of the first page. Reading a layout property is
        synchronous and is what the measurement does anyway; the sleep is for
        the metrics override to arrive, which is a round trip to the renderer.
        """
        await asyncio.sleep(0.05)
        await self.send("Runtime.evaluate", {
            "expression": "document.documentElement.offsetHeight",
            "returnByValue": True}, session=session)

    async def measure(self, session, w, h):
        await self.send("Emulation.setDeviceMetricsOverride",
                        {"width": w, "height": h, "deviceScaleFactor": 1,
                         "mobile": w < 500}, session=session)
        await self.settle(session)
        r = await self.send("Runtime.evaluate",
                            {"expression": MEASURE, "returnByValue": True},
                            session=session)
        return json.loads(r["result"]["value"])


def pages_of(site: pathlib.Path) -> list[str]:
    """Every built page, plus the front page's three demo views.

    The old script named its pages in a list, so a page added to the site was
    not checked until somebody remembered to add it here.
    """
    found = []
    for p in sorted(site.rglob("index.html")):
        rel = p.relative_to(site).parent.as_posix()
        if rel.startswith("demo/fork") or rel.startswith("demo/fleet") \
           or rel.startswith("demo/stock"):
            continue                      # the panes are somebody else's build
        found.append("" if rel == "." else rel + "/")
    return found + ["#demo/fork", "#demo/stock", "#demo/fleet"]


async def run(pages, port, quiet=False):
    chrome = subprocess.Popen(
        ["google-chrome", "--headless=new", "--disable-gpu", "--no-sandbox",
         "--hide-scrollbars", "--disable-dev-shm-usage",
         "--remote-debugging-port=0", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    ws_url = None
    for _ in range(80):
        line = chrome.stderr.readline().decode(errors="replace")
        if "ws://" in line:
            ws_url = line.strip().split("ws://", 1)[1]
            ws_url = "ws://" + ws_url
            break
        if chrome.poll() is not None:
            break
    if not ws_url:
        for _ in range(40):
            try:
                v = json.load(urllib.request.urlopen(
                    "http://127.0.0.1:9222/json/version"))
                ws_url = v["webSocketDebuggerUrl"]
                break
            except Exception:
                time.sleep(0.25)
    if not ws_url:
        print("chrome did not come up", file=sys.stderr)
        return 1, {}

    results: dict[str, dict] = {}
    try:
        async with websockets.connect(ws_url, max_size=None) as ws:
            b = Browser(ws)
            queue = asyncio.Queue()
            for p in pages:
                queue.put_nowait(p)

            async def worker():
                s = await b.tab()
                while True:
                    try:
                        page = queue.get_nowait()
                    except asyncio.QueueEmpty:
                        return
                    url = f"http://127.0.0.1:{port}/{page}"
                    await b.goto(s, url)
                    per = {}
                    for label, w, h in VIEWPORTS:
                        per[label] = await b.measure(s, w, h)
                    results[page] = per
                    if not quiet:
                        name = page or "/"
                        bad = sum(1 for v in per.values()
                                  if v["clip"] or v["stretch"] or v["hscroll"]
                                  or any(f["over"] > SLOP for f in v["fit"]))
                        mark = "ok  " if not bad else f"FAIL"
                        print(f"  {mark} {name:<44} {len(per)} viewports", flush=True)

            await asyncio.gather(*[worker() for _ in range(min(TABS, len(pages)))])
    finally:
        chrome.terminate()
        try:
            chrome.wait(timeout=10)
        except subprocess.TimeoutExpired:
            chrome.kill()

    return 0, results


def faults_of(results) -> dict[str, str]:
    """Every fault, keyed by something that survives a pixel moving.

    The key holds the page, the viewport, the kind and what it is about -- not
    the size of the overflow, which changes with a font metric and would make
    the baseline churn on every unrelated edit.
    """
    out: dict[str, str] = {}
    for page, per in sorted(results.items()):
        for label, m in per.items():
            where = f"{page or '/'} at {label}"
            for f in m["fit"]:
                if f["over"] > SLOP:
                    out[f"fit|{page}|{label}|{f['name']}"] = (
                        f"fit      {where}: screen {f['name']!r} is "
                        f"{f['height']}px in {m['usable']}px, over by {f['over']}")
            for c in m["clip"]:
                out[f"clip|{page}|{label}|{c['sel']}|{c['text'][:40]}"] = (
                    f"clip     {where}: {c['sel']} hides "
                    f"{max(c['overY'], c['overX'])}px of its text -- {c['text']!r}")
            for s in m["stretch"]:
                out[f"aspect|{page}|{label}|{s['src']}"] = (
                    f"aspect   {where}: {s['src']} is {s['how']} -- a {s['box']}px "
                    f"box around {s['art']}px of picture")
            if m["hscroll"]:
                out[f"hscroll|{page}|{label}"] = (
                    f"hscroll  {where}: document is {m['hscroll']}px wider "
                    f"than the window")
    return out


def report(results, baseline: pathlib.Path | None, update: bool) -> int:
    faults = faults_of(results)

    # The site had 467 of these the day the gate could first see them: 307 on
    # the features index alone, where all sixteen plates end in an ellipsis at
    # every viewport, 28 on the front page, and the rest spread over the
    # feature pages. They are what the restructure is for.
    #
    # A baseline lets the gate block a NEW fault today rather than waiting for
    # the last old one to go. It is checked in BOTH directions: a fault that
    # gets fixed must leave the file, so the number in it only ever goes down
    # and nobody can quietly re-baseline a regression.
    known: dict[str, str] = {}
    if baseline and baseline.exists():
        known = json.loads(baseline.read_text())["faults"]

    if update:
        if not baseline:
            print("--update-baseline needs --baseline", file=sys.stderr)
            return 2
        baseline.parent.mkdir(parents=True, exist_ok=True)
        baseline.write_text(json.dumps(
            {"_": "GENERATED by scripts/screens.py --update-baseline. Faults "
                  "this site is known to have. It may only ever get smaller; "
                  "the gate fails if an entry here no longer happens.",
             "faults": faults}, indent=1, sort_keys=True) + "\n")
        print(f"  baseline: {len(faults)} known faults -> {baseline}")
        return 0

    new = {k: v for k, v in faults.items() if k not in known}
    fixed = sorted(k for k in known if k not in faults)

    if new:
        print(f"\n{len(new)} NEW faults:\n", file=sys.stderr)
        for k in sorted(new):
            print(f"  {new[k]}", file=sys.stderr)
        print("\nA screen must be readable whole. Shorten it, or split it into "
              "two screens -- do not clip it and do not stretch a picture to "
              "fill leftover height.", file=sys.stderr)
        return 1

    if fixed:
        print(f"\n{len(fixed)} baselined faults no longer happen:\n",
              file=sys.stderr)
        for k in fixed[:20]:
            print(f"  {known[k]}", file=sys.stderr)
        if len(fixed) > 20:
            print(f"  ... and {len(fixed) - 20} more", file=sys.stderr)
        print("\nGood -- now take them out of the baseline, so they cannot "
              "come back: `just screens-baseline`.", file=sys.stderr)
        return 1

    print(f"\n  {len(results)} pages x {len(VIEWPORTS)} viewports: no new faults")
    if known:
        print(f"  {len(known)} known faults remain, listed in "
              f"{baseline.name if baseline else '?'}")
    else:
        print("  every screen fits, nothing clipped, nothing stretched")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default=str(ROOT / "site"))
    ap.add_argument("--pages", nargs="*", help="check only these paths")
    ap.add_argument("--json", help="write the full measurements here")
    ap.add_argument("--baseline", default=str(ROOT / "docs" / "data" /
                                              "screens-baseline.json"),
                    help="faults this site is known to have")
    ap.add_argument("--no-baseline", action="store_true",
                    help="judge every fault, ignoring the baseline")
    ap.add_argument("--update-baseline", action="store_true",
                    help="record today's faults as the baseline")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    site = pathlib.Path(args.site)
    if not (site / "index.html").exists():
        print(f"no build in {site} -- run `just build` first", file=sys.stderr)
        return 1

    pages = args.pages if args.pages else pages_of(site)
    pages = [p.lstrip("/") if not p.startswith("#") else p for p in pages]

    started = time.time()
    httpd, port = serve(site)
    try:
        code, results = asyncio.run(run(pages, port, args.quiet))
    finally:
        httpd.shutdown()
    if code:
        return code

    if args.json:
        pathlib.Path(args.json).write_text(json.dumps(results, indent=1))
    baseline = None if args.no_baseline else pathlib.Path(args.baseline)
    rc = report(results, baseline, args.update_baseline)
    print(f"  {time.time() - started:.1f}s")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
