# A fork of the Turing Pi 2 BMC firmware

The Turing Pi 2 is a mini-ITX board that carries four compute modules. The
small SoC that powers them on, routes their USB and serves the web interface is
the **BMC**, and it runs its own Linux. This is a fork of that firmware — a
kernel and Buildroot that are still supported, an update that undoes itself
when it goes wrong, and the sensors the board always had but never exposed.

!!! info "Not a Turing Pi project"
    This is an independent fork by [excavador](https://github.com/excavador-turing),
    not affiliated with or endorsed by Turing Machines Inc. It runs on one
    person's hardware. Everything here was measured on that board, and where a
    measurement contradicted something written here, the writing changed.

<div class="grid cards" markdown>

-   __[A bad image undoes itself](features/updates-that-undo-themselves.md)__

    ---

    A new firmware boots *tentatively*. It is kept only if the daemon answers,
    every module's switch port is there, and the image is the one that was
    staged. Otherwise the board reboots onto what it had — as it has done,
    on purpose, to prove it can.

-   __[See what the board sees](features/see-what-the-board-sees.md)__

    ---

    The board ships a temperature sensor upstream's device tree never
    described. The fan is now driven from it, and the interface says *which
    trip point* put the fan where it is.

-   __[Pick a version, from anywhere](features/pick-a-version.md)__

    ---

    GitHub releases, an HTTP directory, or the SD card. Every candidate listed
    with how it compares to what is running and how much is known about its
    integrity.

-   __Metrics, behind their own credential__

    ---

    31 Prometheus families, scraped with a token that **cannot touch
    `/api/bmc`**. Upstream had no metrics; adding them with the root password
    would have been worse than none.

-   __A console to every module__

    ---

    Four serial consoles in the browser, one per compute module, without the
    header on the board and without a USB adapter on the desk.

-   __[And from a shell](reference/cli.md)__

    ---

    `tpi` reaches all of it from the command line — list versions, install
    one, set the board's name and its clock, export its configuration — so
    none of it is click-only.

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
| Metrics | none | **31 Prometheus families** |
| Scrape credential | — | **a token that cannot touch `/api/bmc`** |
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
    BMC is trusted without a credential. Flashing a module on a v2.5 board may
    target a different module than the one you chose. And on 2026-09-09 a board
    left with a browser open on the interface ran out of memory and had to be
    power-cycled by hand.

    All four are [written down with their tickets](reference/known-faults.md).
    A fork that lists only its improvements is advertising.
