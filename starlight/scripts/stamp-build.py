#!/usr/bin/env python3
"""Write /build.json into the built site: which commit, which run, when, and
which BMC-UI release the demo panes came from.

It is how the publish workflow's `published` job tells that turingpi.xyz
serves THIS build and not the one before it: a green deploy job says the
upload was accepted, not that the edge serves it. `run` is there because two
runs can build one commit (the hourly job rebuilds when BMC-UI releases).

The BMC-UI tag is read from what was built, dist/demo/{fork,fleet}/VERSION,
not from an argument: it is what the site serves. Without the panes (a
local build, a pull request) it is null.

usage: starlight/scripts/stamp-build.py [dist]   (from anywhere)
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]


def main() -> int:
    dist = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "starlight/dist")
    if not (dist / "index.html").is_file():
        print(f"stamp-build: {dist} has no index.html; build first", file=sys.stderr)
        return 1
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                            check=True, capture_output=True, text=True).stdout.strip()
    tags = {}
    for pane in ("fork", "fleet"):
        v = dist / "demo" / pane / "VERSION"
        if v.is_file():
            tags[pane] = v.read_text().strip()
    if len(set(tags.values())) > 1:
        print(f"stamp-build: the demo panes disagree on their BMC-UI release: {tags}",
              file=sys.stderr)
        return 1
    run = os.environ.get("GITHUB_RUN_ID")
    stamp = {
        "commit": commit,
        "run": f"{run}-{os.environ.get('GITHUB_RUN_ATTEMPT', '1')}" if run else "local",
        "built_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "bmc_ui": next(iter(tags.values()), None),
    }
    (dist / "build.json").write_text(json.dumps(stamp, indent=2) + "\n")
    print(f"stamp-build: {json.dumps(stamp)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
