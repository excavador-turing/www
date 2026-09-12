#!/usr/bin/env python3
"""Rewrite the gate's record from a board's own counter.

The page it writes claims to come from the board. Until this existed it did
not: the numbers were typed in, and drifted from 14 to 17 in a day. The
script is the difference between that claim being true and being a slogan.
"""
import datetime
import re
import sys
import urllib.request

PAGE = "docs/reference/gate-history.md"


def counter(text, result):
    m = re.search(
        r'^bmcd_firmware_promotion_total\{result="%s"\}\s+(\d+)' % result,
        text,
        re.M,
    )
    if not m:
        sys.exit(f"the board did not report promotion_total for {result!r}")
    return int(m.group(1))


board = sys.argv[1]
url = f"http://{board}:9110/metrics"
with urllib.request.urlopen(url, timeout=10) as r:
    metrics = r.read().decode()

promoted = counter(metrics, "promoted")
rolled_back = counter(metrics, "rolled_back")
today = datetime.date.today().isoformat()

page = open(PAGE).read()
before = page

page, n = re.subn(
    r"(As of \*\*)\d{4}-\d{2}-\d{2}(\*\*:)", rf"\g<1>{today}\g<2>", page, count=1
)
if n != 1:
    sys.exit("could not find the 'As of' date")

page, n = re.subn(
    r"(\| promoted \| )\d+( \|\n\| rolled back \| )\d+( \|)",
    rf"\g<1>{promoted}\g<2>{rolled_back}\g<3>",
    page,
    count=1,
)
if n != 1:
    sys.exit("could not find the counts table")

page, n = re.subn(
    r'(bmcd_firmware_promotion_total\{result="promoted"\} )\d+'
    r'(\nbmcd_firmware_promotion_total\{result="rolled_back"\} )\d+',
    rf"\g<1>{promoted}\g<2>{rolled_back}",
    page,
    count=1,
)
if n != 1:
    sys.exit("could not find the console example")

open(PAGE, "w").write(page)

# The same two numbers are quoted on the front page and on the feature page
# that argues for the gate. They were typed in, and drifted -- 18 on the page
# while the board said 26 -- which is the exact failure this script exists to
# prevent, so they are rewritten from the same scrape. Anywhere else a count
# appears, it must be added here, not typed.
QUOTED = {
    "docs/index.md": [
        (r"On this board: \d+ updates, \d+ automatic rollback",
         f"On this board: {promoted} updates, {rolled_back} automatic rollback"),
    ],
    "docs/features/updates-that-undo-themselves.md": [
        (r"<div><b>\d+</b><span>updates taken on this board</span></div>",
         f"<div><b>{promoted}</b><span>updates taken on this board</span></div>"),
        (r"<div><b>\d+</b><span>rolled back by the board itself</span></div>",
         f"<div><b>{rolled_back}</b><span>rolled back by the board itself</span></div>"),
    ],
}
for path, edits in QUOTED.items():
    text = open(path).read()
    for pattern, replacement in edits:
        text, n = re.subn(pattern, replacement, text, count=1)
        if n != 1:
            sys.exit(f"{path}: could not find the quoted count for {pattern!r}")
    open(path, "w").write(text)
    print(f"{path}: quoted counts rewritten")
print(f"{board}: promoted {promoted}, rolled back {rolled_back}, as of {today}")
print("page unchanged" if page == before else "page rewritten")
