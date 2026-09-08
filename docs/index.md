# A fork of the Turing Pi 2 BMC firmware

The Turing Pi 2 is a mini-ITX board that carries four compute modules. The
small SoC that powers them on, routes their USB and serves the web interface is
the **BMC**, and it runs its own Linux. This is a fork of that firmware — a
kernel and Buildroot that are still supported, an update that undoes itself
when it goes wrong, and the sensors the board always had but never exposed.

!!! info "Not a Turing Pi project"
    This is an independent fork by [excavador](https://github.com/excavador-turing),
    not affiliated with or endorsed by Turing Machines Inc. It runs on one
    person's hardware. Everything here was measured on that board.

<div class="grid cards" markdown>

-   __A bad image undoes itself__

    ---

    A new firmware boots *tentatively*. It is kept only if the daemon answers
    and every module's switch port is there; otherwise the board reboots onto
    the image it had. **Fifteen consecutive clean promotions**, over the air,
    with all four modules running throughout.

-   __Temperature, and a fan that uses it__

    ---

    The board ships a sensor that upstream's device tree never exposed, so the
    fan ran at a fixed speed against nothing. It now reads `thermal_zone0` and
    the kernel drives the fan from it.

-   __Pick a version, from anywhere__

    ---

    Sources are configurable — GitHub releases, an HTTP directory, or the SD
    card. Every candidate is listed with how it compares to what is running
    and how much is known about its integrity.

-   __Metrics, behind their own credential__

    ---

    31 Prometheus families, scraped with a token that **cannot touch
    `/api/bmc`**. Upstream had no metrics; adding them with the root password
    would have been worse than none.

-   __A console to every module__

    ---

    Four serial consoles in the browser, one per compute module, without the
    header on the board and without a USB adapter on the desk.

-   __And from a shell__

    ---

    [`tpi` 1.1.0](cli.md) reaches all of it from the command line — list
    versions, install one, rotate the metrics token — so none of it is
    click-only.

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
| Board temperature | none — no sensor in the device tree | **reads through `thermal_zone0`** |
| Fan | fixed persisted speed | **kernel-driven from that sensor** |
| Metrics | none | **31 Prometheus families** |
| Scrape credential | — | **a token that cannot touch `/api/bmc`** |
| Published checksums | none | **`SHA256SUMS` per release, verified on download** |
| Serial console | serial header on the board | **per module, in the browser** |
| Firmware sources | one, hard-coded | **configurable; GitHub, HTTP, or SD card** |
| Command line | upstream's `tpi`, unaware of any of this | **`tpi` reaches every endpoint above** |

## The one that matters most

**A bad image undoes itself.** A new firmware boots *tentatively*: it is kept
only if bmcd answers on `https://127.0.0.1/` and every compute module's switch
port exists. Otherwise the board reboots, which lands on the previous image
because nothing was renamed and the boot variable is one-shot.

That has now promoted cleanly **fifteen consecutive times**, over the air, with
all four modules running — and the modules never noticed: every uptime advanced
by exactly the wall-clock time each flash took.

!!! warning "What it does not cover"
    The gate only helps an image that boots far enough to run it. One that hangs
    earlier still needs power cut, which hard-cuts the compute modules. A
    hardware watchdog is the fix and is not built yet.

    It also checks that the daemon is *alive*, not that it is *correct*. A build
    with a broken `/metrics` passes both checks. This protects against a brick,
    never against a bug.

## Where to start

- **[Comparison](comparison.md)** — the same claims with the evidence
- **[Install](install.md)** — putting this on your own board
- **[Command line](cli.md)** — `tpi`, and what 1.1.0 added
- **[Developing](development.md)** — build it, and iterate without cutting a release
- **[Contributing](contributing.md)** — open a pull request
