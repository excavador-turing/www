---
hide:
  - navigation
  - toc
---

<div class="tp-hero tp-hero--center" markdown>

# Firmware for the Turing Pi 2 that undoes its own mistakes

<p class="lede">Upstream stopped in February 2025. This fork keeps the board on a supported kernel, makes a bad flash undo itself, and reads the sensors the hardware always had.</p>

<div class="tp-actions" markdown>
[Try it, live](demo/index.md){ .md-button .md-button--primary }
[Install it](guides/install.md){ .md-button }
[Coming from stock?](guides/upgrade-from-stock.md){ .md-button }
</div>

</div>

<div class="tp-claims" markdown>
<div markdown><b>Flash it wrong and lose nothing.</b><span>A new image boots on trial and is kept only if the board comes back right. On this board: 18 updates, 1 automatic rollback, 0 trips to the rack — [read off the board](reference/gate-history.md).</span></div>
<div markdown><b>Update the BMC without touching your nodes.</b><span>Upstream power-cycles all four compute modules during a firmware update. This fork leaves their rails alone.</span></div>
<div markdown><b>Software that is still maintained.</b><span>Kernel 6.12 LTS on Buildroot 2025.02 LTS. Upstream ships 6.8 on an end-of-life Buildroot, and its last release was February 2025.</span></div>
</div>

<div class="tp-plates grid cards" markdown>

-   [![](assets/icons/undo.svg)](features/updates-that-undo-themselves.md)

    [A bad image undoes itself](features/updates-that-undo-themselves.md)

    Boots on trial; reverts by itself if the board does not come back right.

-   [![](assets/icons/versions.svg)](features/pick-a-version.md)

    [Pick a version, from anywhere](features/pick-a-version.md)

    This fork, upstream, or the SD card — every candidate checksum-verified.

-   [![](assets/icons/sensors.svg)](features/see-what-the-board-sees.md)

    [See what the board sees](features/see-what-the-board-sees.md)

    The sensor upstream never exposed, and a fan that says why it is where it is.

-   [![](assets/icons/console.svg)](features/a-console-to-every-module.md)

    [A console to every module](features/a-console-to-every-module.md)

    Four serial consoles in the browser. No header, no adapter.

-   [![](assets/icons/power.svg)](reference/cli.md)

    [Power and USB, per module](reference/cli.md)

    Power, reset, USB routing and flashing — and a flash that refuses to guess.

-   [![](assets/icons/metrics.svg)](reference/metrics.md)

    [Metrics, on their own port](reference/metrics.md)

    Every family the board exposes, on a listener that reaches nothing else.

-   [![](assets/icons/network.svg)](reference/api/network.md)

    [Network and time](reference/api/network.md)

    Addresses, an NTP source you can set, and whether the clock actually synced.

-   [![](assets/icons/name.svg)](reference/api/board.md)

    [Name it, export it](reference/api/board.md)

    Hostname, clock and configuration are controls, and `tpi` reaches every one.

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
