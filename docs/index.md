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
    described. The fan is now driven from it, the interface says *which trip
    point* put the fan where it is, and an Override switch can hold it
    somewhere else.

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

-   __[A console to every module](features/a-console-to-every-module.md)__

    ---

    Four serial consoles in the browser, one per compute module, without the
    header on the board and without a USB adapter on the desk. Each opens on
    the module's recent output rather than on a blank screen.

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
