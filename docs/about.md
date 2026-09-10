---
hide:
  - toc
---

# About this fork

## Why fork it

Upstream is dormant. Its firmware mirror stops at **v2.0.5**, while its GitHub
releases reach **v2.1.0** — the same publisher, two catalogues that disagree.
Following the documented update path would *downgrade* a board running anything
newer.

That mattered because the board had real problems: a firmware update
power-cycled the compute modules, there was no temperature sensor anywhere, the
fan ran flat out with nothing to regulate against, and a bad image meant a trip
to the rack.

## What changed

| | upstream | this fork |
|---|---|---|
| Kernel | 6.8, not a longterm release | **6.12.109 LTS** |
| Buildroot | 2024.05.1 (EOL) | **2025.02.17 LTS** |
| Bad image recovery | power cut | **health-gated A/B promotion** |
| Firmware update vs modules | power-cycles them | **rails untouched** |
| Board temperature | none — no sensor in the device tree | **read, with its trip points** |
| Fan | fixed persisted speed | **kernel-driven, and it says why** |
| Metrics | none | **[a documented catalogue](reference/metrics.md)** |
| Scrape endpoint | — | **its own port, which cannot reach `/api/bmc`** |
| Published checksums | none | **`SHA256SUMS` per release, verified on download** |
| Serial console | serial header on the board | **per module, in the browser** |
| Firmware sources | one, hard-coded | **configurable; GitHub, HTTP, or SD card** |
| API description | a prose page | **OpenAPI 3.1, served by the board itself** |
| Command line | upstream's `tpi`, unaware of any of this | **`tpi` reaches every endpoint above** |

The [full comparison](reference/comparison.md) carries the evidence for each
row, including the ones where upstream is ahead.

## Start here

- **[Install](guides/install.md)** — putting this on your own board
- **[Recover a bad flash](guides/recover-a-bad-flash.md)** — what to do when it goes wrong
- **[Developing](guides/development.md)** — build it, and iterate without cutting a release
- **[What is and isn't fixed](reference/known-faults.md)** — the honest list, with tickets

!!! warning "Read the fault list before you rely on this"
    The certificate on the board is expired. Anything running locally on the
    BMC is trusted without a credential, though since v2.14.0 it at least
    leaves an audit line saying so. Nothing shuts the board down if it
    overheats — there is no `critical` trip. And flashing a module on a v2.5
    board now refuses rather than guessing, but the port mapping behind that
    has not been proven against two modules in maskrom.

    All of them are [written down with their tickets](reference/known-faults.md),
    along with the mDNS responder that killed this board twice in one day
    before v2.13.0 fixed it. A fork that lists only its improvements is
    advertising.

## The demo

The [front page's demo](/#demo/fork) is two interfaces answering from data
captured off a real board. Nothing in it talks to hardware.

- **Readings are real.** Temperatures, fan steps, NAND wear, slot versions,
  uptimes — captured from the board by
  [a script](https://github.com/excavador-turing/BMC-UI/blob/hive/scripts/capture-fixtures.sh)
  that also refuses to publish the board's identity. Addresses, MAC and serial
  are replaced with documentation-range values.
- **Controls do nothing, and say so.** Power, flash, reboot: each answers with
  a message that this is a demo. A control that pretends to work is what this
  project keeps removing from the real interface.
- **The console replays.** It shows a module's recorded scrollback rather than
  a fake live stream, and the panel says it is a recording.
- **Stock is stock.** The stock pane is the vendor's own interface, unmodified
  apart from answering from fixtures — it is GPL-2.0, as is this fork, and its
  copyright notice is intact.

The fork pane is built from the tag the firmware pins, by `just refresh-demo`,
and names its version on the About tab. The stock pane was captured once and
does not change.
