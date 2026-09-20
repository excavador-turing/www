#!/usr/bin/env python3
"""Take the demo ribbon off a capture.

Every built demo bundle gets an exit ribbon injected into it
(`scripts/demo-ribbon.py`) so a reader who opens a pane full-size can get
back. It is the right thing on the live demo and the wrong thing in a
screenshot: five of the eleven feature captures were taken through it and
carried a lime bar reading "Demo of this fork" across the top, while the
other six did not. Side by side, the pages looked like two different sites.

    scripts/crop-ribbon.py                    # every capture that has one
    scripts/crop-ribbon.py --check            # fail if any still does

Pure Python, no Pillow: this repository has exactly one Python environment
and a compiled image library in it to crop a stripe off five files, once, is
not a trade worth making. PNG is a well-specified format and the encoder here
writes filter 0, which zlib compresses about as well as the original.
"""
from __future__ import annotations

import argparse
import pathlib
import struct
import sys
import zlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
CAPTURES = ROOT / "docs" / "assets" / "captures"

# The ribbon's own background, from scripts/demo-ribbon.py.
LIME = (220, 254, 142)
TOLERANCE = 12


def unfilter(raw: bytes, width: int, height: int, channels: int) -> list[bytearray]:
    stride = width * channels
    out, prev, i = [], bytearray(stride), 0
    for _ in range(height):
        f = raw[i]; i += 1
        line = bytearray(raw[i:i + stride]); i += stride
        if f:
            for x in range(stride):
                a = line[x - channels] if x >= channels else 0
                b = prev[x]
                c = prev[x - channels] if x >= channels else 0
                if f == 1:
                    line[x] = (line[x] + a) & 255
                elif f == 2:
                    line[x] = (line[x] + b) & 255
                elif f == 3:
                    line[x] = (line[x] + (a + b) // 2) & 255
                elif f == 4:
                    pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                    pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                    line[x] = (line[x] + pr) & 255
                else:
                    raise ValueError(f"filter {f}")
        out.append(line); prev = line
    return out


def read(path: pathlib.Path):
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path.name} is not a PNG")
    pos, idat, hdr = 8, b"", None
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        if kind == b"IHDR":
            hdr = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            idat += body
        elif kind == b"IEND":
            break
        pos += 12 + length
    w, h, depth, colour, comp, filt, interlace = hdr
    if depth != 8 or colour not in (2, 6) or interlace:
        raise ValueError(f"{path.name}: only 8-bit RGB/RGBA, non-interlaced")
    channels = 3 if colour == 2 else 4
    return w, h, colour, channels, unfilter(zlib.decompress(idat), w, h, channels)


def write(path: pathlib.Path, width, colour, channels, rows) -> None:
    raw = b"".join(b"\x00" + bytes(r) for r in rows)
    def chunk(kind, body):
        return (struct.pack(">I", len(body)) + kind + body
                + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF))
    out = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", width, len(rows), 8,
                                        colour, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 9))
           + chunk(b"IEND", b""))
    path.write_bytes(out)


def ribbon_height(width, channels, rows) -> int:
    """How many rows at the top are ribbon.

    Sampled across the middle of the row rather than at an edge: the ribbon
    spans the full width, so a row is ribbon when its centre is the ribbon's
    colour, and the first row that is not ends it.
    """
    def is_ribbon(row) -> bool:
        """Mostly lime, across the whole row.

        Sampled across the WHOLE row, and the bar is 63 rows tall, not 27.

        Two earlier versions got this wrong in the same way, from opposite
        ends. The first demanded three points be exactly the ribbon colour and
        stopped at the 27 rows of padding above the lettering. The second
        asked for 70% and stopped at row 0, because the rows carrying the
        ribbon's text measure 63-72% -- the glyphs are not lime.

        Measured on firmware.png: text rows 63-72%, the bar below them 97-100%,
        and the first row of the interface underneath 0%. Half is comfortably
        between the lettering and the page, which is the only boundary that
        matters.
        """
        hits = total = 0
        for x in range(0, width, 16):
            px = row[x * channels:x * channels + 3]
            total += 1
            if all(abs(px[i] - LIME[i]) <= TOLERANCE for i in range(3)):
                hits += 1
        return total and hits / total >= 0.5

    n = 0
    for row in rows:
        if not is_ribbon(row):
            break
        n += 1
    # A capture whose whole top third is lime is not a ribbon, it is a
    # screenshot of something lime, and cropping it would be vandalism.
    return n if n < len(rows) // 8 else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("files", nargs="*")
    args = ap.parse_args()

    paths = ([pathlib.Path(f) for f in args.files] if args.files
             else sorted(CAPTURES.glob("*.png")))
    found = []
    for p in paths:
        w, h, colour, channels, rows = read(p)
        n = ribbon_height(w, channels, rows)
        if not n:
            continue
        found.append((p, n, h))
        if not args.check:
            write(p, w, colour, channels, rows[n:])

    if args.check:
        if found:
            print("captures still carrying the demo ribbon:", file=sys.stderr)
            for p, n, h in found:
                print(f"  {p.name}: {n} rows", file=sys.stderr)
            print("run `just crop-ribbon`", file=sys.stderr)
            return 1
        print(f"  {len(paths)} captures, none carrying a ribbon")
        return 0

    for p, n, h in found:
        print(f"  {p.name}: {n} rows off the top, {h} -> {h - n}")
    if not found:
        print(f"  {len(paths)} captures, nothing to crop")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
