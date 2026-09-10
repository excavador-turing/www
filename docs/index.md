---
hide:
  - toc
---

# Firmware for the Turing Pi 2 that undoes its own mistakes

Upstream's firmware stopped. The last release was **v2.1.0, in February 2025**;
the maintainer said in June 2026 that he had moved on. Meanwhile a bad flash
still meant a trip to the rack, a firmware update still power-cycled all four
compute modules, and the board's own temperature sensor was not in the device
tree at all.

This fork picks it up: a kernel and a Buildroot that are still supported, an
update that boots *tentatively* and reverts itself if the board does not come
back right, and the sensors the hardware always had.

[Install it](guides/install.md){ .md-button .md-button--primary }
[Coming from stock firmware?](guides/upgrade-from-stock.md){ .md-button }
[What changed, row by row](reference/comparison.md){ .md-button }

!!! quote "**18 promotions. 1 rollback.**"
    That rollback is the point. A firmware that has never had to undo itself
    has not been shown to be able to. The counter is
    [read off the board](reference/gate-history.md), not typed here, and the
    [known-fault list](reference/known-faults.md) is on this page too — a fork
    that publishes only its improvements is advertising.

!!! info "Not a Turing Pi project"
    This is an independent fork by [excavador](https://github.com/excavador-turing),
    not affiliated with or endorsed by Turing Machines Inc. It runs on one
    person's hardware. Everything here was measured on that board, and where a
    measurement contradicted something written here, the writing changed.

<div class="grid cards" markdown>

-   [![Firmware slots: what is running, what it can fall back to](assets/cards/card-firmware.png)](features/updates-that-undo-themselves.md)

    __[A bad image undoes itself](features/updates-that-undo-themselves.md)__

    ---

    A new firmware boots *tentatively*. It is kept only if the daemon answers,
    every module's switch port is there, and the image is the one that was
    staged. Otherwise the board reboots onto what it had — as it has done,
    on purpose, to prove it can.

-   [![Board health: uptime, memory, NAND erase blocks, clock sources](assets/cards/card-thermal.png)](features/see-what-the-board-sees.md)

    __[See what the board sees](features/see-what-the-board-sees.md)__

    ---

    A temperature sensor upstream's device tree never described, the fan driven
    from it, and the interface saying *which trip point* put it there. Plus the
    things a board should admit: erase blocks left in its NAND, whether its
    clock is actually synchronised, and to what.

-   [![A serial console in the browser, showing a module's live kernel output](assets/cards/card-console.png)](features/a-console-to-every-module.md)

    __[A console to every module](features/a-console-to-every-module.md)__

    ---

    Four serial consoles in the browser, one per compute module, without the
    header on the board and without a USB adapter on the desk. Each opens on
    the module's recent output rather than on a blank screen — the screenshot
    is a real node booting.

-   [![Per-module power and USB routing](assets/cards/card-nodes.png)](reference/cli.md)

    __Every module, from either end__

    ---

    Power, reset, USB routing and flashing, per module — and
    [`tpi`](reference/cli.md) reaches all of it from a shell, so none of it is
    click-only. A flash now refuses a module it cannot positively identify
    instead of guessing.

-   __[Pick a version, from anywhere](features/pick-a-version.md)__

    ---

    GitHub releases, an HTTP directory, or the SD card. Every candidate listed
    with how it compares to what is running and how much is known about its
    integrity.

-   __Metrics, on a port that reaches nothing else__

    ---

    [Every family the board exposes](reference/metrics.md), on its own
    listener that serves nothing but `/metrics`, and
    [a dashboard over all of them](guides/monitor-it.md). Upstream had no
    metrics; adding them behind the root password would have been worse than
    none.

</div>

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
