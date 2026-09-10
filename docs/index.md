---
hide:
  - navigation
  - toc
---

<div class="tp-hero" markdown>

# Firmware for the Turing Pi 2 that undoes its own mistakes

<p class="lede">Upstream's last release was <strong>February 2025</strong> and the maintainer moved on. A bad flash still meant a trip to the rack, an update still power-cycled all four compute modules, and the board's own temperature sensor was not in the device tree. This fork picks it up on a kernel that is still supported.</p>

<div class="tp-actions" markdown>
[Install it](guides/install.md){ .md-button .md-button--primary }
[Coming from stock firmware?](guides/upgrade-from-stock.md){ .md-button }
[What changed, row by row](reference/comparison.md){ .md-button }
</div>

</div>

<div class="tp-proof" markdown>
<div markdown><b>18 / 1</b><span>promotions / rollbacks — [read off the board](reference/gate-history.md). The rollback is the point: a firmware that has never had to undo itself has not been shown able to.</span></div>
<div markdown><b>6.12 LTS</b><span>kernel, on Buildroot 2025.02 LTS. Upstream ships 6.8 on an end-of-life Buildroot.</span></div>
<div markdown><b>0 modules</b><span>power-cycled by a firmware update. Upstream cuts all four.</span></div>
</div>

<div class="tp-plates grid cards" markdown>

-   [![Firmware slots: what is running and what it falls back to](assets/cards/card-firmware.png)](features/updates-that-undo-themselves.md)

    [A bad image undoes itself](features/updates-that-undo-themselves.md)

    Boots the new image *tentatively*; keeps it only if the daemon answers and every module's port is present.

-   [![Every candidate version, from every configured source, with its checksum state](assets/cards/card-versions.png)](features/pick-a-version.md)

    [Pick a version, from anywhere](features/pick-a-version.md)

    This fork, upstream's two catalogues, or the SD card — side by side, each checksum-verified or marked as not.

-   [![Board health: memory, NAND erase blocks, clock sources](assets/cards/card-thermal.png)](features/see-what-the-board-sees.md)

    [See what the board sees](features/see-what-the-board-sees.md)

    The temperature sensor upstream never described, which trip point set the fan, NAND wear, and what the clock is synced to.

-   [![A serial console in the browser showing a module's live kernel output](assets/cards/card-console.png)](features/a-console-to-every-module.md)

    [A console to every module](features/a-console-to-every-module.md)

    Four serial consoles in the browser, no header, no adapter — each opens on the module's recent output.

-   [![Per-module power and USB routing](assets/cards/card-nodes.png)](reference/cli.md)

    [Power and USB, per module](reference/cli.md)

    Power, reset, USB routing and flashing — and a flash that refuses a module it cannot positively identify.

-   [![The raw /metrics exposition, as a scraper sees it](assets/cards/card-metrics.png)](reference/metrics.md)

    [Metrics, on their own port](reference/metrics.md)

    Every family the board exposes, on a listener that serves nothing else — so a scraper never holds the root password.

-   [![Network interfaces and time](assets/cards/card-network.png)](reference/api/network.md)

    [Network and time](reference/api/network.md)

    Interfaces, addresses, and an NTP source you can set — and see whether it is actually synchronised.

-   [![Settings: hostname, configuration export](assets/cards/card-settings.png)](reference/api/board.md)

    [Name it, export it](reference/api/board.md)

    Hostname, clock and configuration are controls, not files on a shell — and `tpi` reaches every one from a terminal.

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
