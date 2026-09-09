# Upstream, and this fork

Every number here was measured on a running board or read from a live server,
on **2026-09-08**. Where a claim could not be checked, it says so.

## The two upstreams disagree with each other

Turing Pi publishes firmware by two routes, and they do not agree:

| route | newest | checksums |
|---|---|---|
| [GitHub releases](https://github.com/turing-machines/BMC-Firmware/releases) | **v2.1.0** | — |
| [firmware.turingpi.com](https://firmware.turingpi.com/turing-pi2/) | **v2.0.5** | **none published** |

The mirror is what the stock web interface follows. On a board running anything
newer, following it walks the board *backwards*.

!!! note "No checksums at all"
    `SHA256SUMS`, `sha256sum.txt`, `sha256` and `checksums.txt` all return 404
    on the mirror. An image from there is trusted on TLS and nothing else —
    which is why this fork labels such a source **TLS only** rather than
    pretending it was verified.

Both routes ship as sources in this fork, precisely so the disagreement is
visible on one page rather than discovered later.

## Platform

| | upstream | fork |
|---|---|---|
| Kernel | 6.8 — not a longterm release | **6.12.109 LTS** |
| Buildroot | 2024.05.1 (EOL) | **2025.02.17 LTS** |
| Rust | 1.85.0 | **1.98.1** |
| Image size | — | 38.1 MB, 81 % of the UBI slot; build fails at 90 % |

## Updating

| | upstream | fork |
|---|---|---|
| Bad image | power cut, hard-cutting four modules | **reboots back by itself** |
| Modules during a flash | power-cycled | **untouched** |
| What is staged | not reported | **version, checksum, source** |
| Newer release available? | mirror that stops at v2.0.5 | **from any configured source** |
| Install a chosen version | — | **from the web interface** |

**The gate's record is a counter the board keeps**, not a number written here:
`bmcd_firmware_promotion_total{result}`, currently 14 promoted and 1 rolled
back — and the rollback was deliberate, to prove it could refuse. See
[the gate's record](gate-history.md).

Every time, each module's uptime advanced by exactly the wall-clock duration
of the flash, which is the evidence that nothing was reset.

*This paragraph used to say "fifteen consecutive times", and elsewhere this
site said nineteen. Both were counted by hand and both had drifted by the time
a metric existed to check them. That is why the number now lives in one place
and is generated.*

!!! warning "What the gate cannot see"
    It checks that the daemon answers and that the switch ports exist. An image
    whose *new feature* is broken passes both. This fork's own metrics
    endpoint could have shipped completely broken and been promoted happily —
    which is why release verification is explicit and written down, not left
    to the gate.

## Hardware the board could not see

| | upstream | fork |
|---|---|---|
| SoC temperature | **none** — no thermal node in any device tree | reads through `thermal_zone0` |
| Fan | fixed persisted speed | **kernel-driven** from that sensor, and holdable |
| Switch port state | not exposed | per-port link, speed, counters |
| Module power-on time | one shared bit, correct only for node 1 | **per node, as a duration** |

The temperature sensor is the clearest example. The driver was compiled in and
never probed, because mainline describes no thermal node for this SoC — so the
fan ran flat out with nothing to regulate against. Adding the node to the board
device tree is what made both work.

## Monitoring

A [catalogue of metric families](metrics.md), none of which existed
upstream. The credential
is the part worth noting: `/metrics` takes a **token that returns 401 against
`/api/bmc`**, so a scrape config cannot power-cycle a module or flash the board.

Upstream has no metrics endpoint, so it has no equivalent question.

## What is still missing

Honest gaps, not roadmap:

- **A hardware watchdog.** The gate cannot save an image that hangs before it
  runs. That still needs physical access.
- **A usable TLS certificate.** The daemon mints a self-signed one only when
  the files are *missing*; if it finds an expired one it uses it. The
  certificate on the reference board was issued June 2025 and **expired in
  July 2025** — RSA, no subject-alternative name, and on the overlay, so it
  has survived every upgrade this fork has shipped. There is no path to
  install a real one but `scp`.
- **A flash that targets the module you chose.** On v2.5 boards the daemon
  writes to whichever module is in maskrom *first* and reports success,
  whatever was selected. With one module in maskrom this is correct; with two
  it is a coin toss, and the interface now says so in red.
- **VLAN filtering and STP** on the switch: `br0` bridges all six ports flat.
