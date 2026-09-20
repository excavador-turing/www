---
hide:
  - toc
---

# Roadmap

7 things planned, ordered by votes, 15 cast so far. Every row is a GitHub Discussion: **upvote the ones you want**, and the order on this page changes.

Not on the list? [Propose it](https://github.com/excavador-turing/BMC-Firmware/discussions/new?category=ideas) — a sentence about the problem is enough. Something broken instead? [Report it](feedback.md), and read [what is and isn't fixed](reference/known-faults.md) first, because it may already be there with a ticket.

| votes | feature | what it is | where it stands |
|--:|---|---|---|
| **5** | [VLANs on the board's switch, with apply-then-confirm](https://github.com/excavador-turing/BMC-Firmware/discussions/25) | VLAN filtering and STP on the RTL8370MB-CG, first in the daemon, then in the interface. | Backlog |
| **3** | [A hardware watchdog, so a hung daemon does not mean a trip to the rack](https://github.com/excavador-turing/BMC-Firmware/discussions/24) | The SoC has a watchdog and this firmware does not arm it. | Open |
| **2** | [Remote syslog, and an audit line for every mutating API call](https://github.com/excavador-turing/BMC-Firmware/discussions/27) | Ship the board's logs somewhere that survives it, and write one line per call that changes state — who, what, from where. | Open |
| **2** | [Manage the BMC's SSH keys and change its password from the interface and the fleet](https://github.com/excavador-turing/BMC-Firmware/discussions/29) | The only way to put an SSH key on the BMC, or take one off, is to log in over SSH and edit `/root/.ssh/authorized_keys` by hand. | Open |
| **1** | [OpenTelemetry: traces, logs and metrics over OTLP, opt-in](https://github.com/excavador-turing/BMC-Firmware/discussions/22) | The board already exposes Prometheus metrics on their own credential-free listener, which is the right thing when the cluster is down. | Designed, not started |
| **1** | [SD card: checksums computed on the board, upload, rename and move](https://github.com/excavador-turing/BMC-Firmware/discussions/23) | The interface can now list what is on the card and say which files can be written to a module (v3.25.0). | Listing shipped in v3.25.0; the rest is open |
| **1** | [Choose the self-signed certificate's key type and validity](https://github.com/excavador-turing/BMC-Firmware/discussions/26) | When no operator certificate is installed the board issues its own: EC P-384, real names, 825 days, renewed 30 days out. | Open |

## Recently shipped

Every feature has a page with the measurement behind it, and every release has [its changelog entry](changelog/firmware.md).

| release | when |
|---|---|
| [v2.32.0](changelog/firmware.md) | 13 September 2026 |
| [v2.31.0](changelog/firmware.md) | 12 September 2026 |
| [v2.30.0](changelog/firmware.md) | 12 September 2026 |
| [v2.29.0](changelog/firmware.md) | 12 September 2026 |
| [v2.28.0](changelog/firmware.md) | 12 September 2026 |

## How a thing gets from here to there

A feature is a ticket in the maintainer's tracker, a Discussion here, and then a page under [Features](features/index.md) with the numbers that prove it — in that order. The [known-faults page](reference/known-faults.md) is the other half of this one: what is wrong today, with the ticket that tracks it. A roadmap that lists only what is coming is advertising.

Votes read 2026-09-20 by `just refresh-roadmap`.
