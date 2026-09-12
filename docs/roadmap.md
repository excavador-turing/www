---
hide:
  - toc
---

# Roadmap

What is planned, what is being built, and where to say what you want. Every
row is a GitHub Discussion you can **upvote**; the ones with the most votes get
done first, and the argument for each is in the discussion rather than here.

Not on the list? [Propose it](https://github.com/excavador-turing/BMC-Firmware/discussions/new?category=ideas)
— a sentence about the problem is enough. Found something broken?
[Report it](https://github.com/excavador-turing/BMC-Firmware/issues/new/choose),
and read [what is and isn't fixed](reference/known-faults.md) first, because it
may already be there with a ticket.

## Planned

| Feature | What it is | Where it stands |
|---|---|---|
| [SD card: checksums computed on the board, upload, rename and move](https://github.com/excavador-turing/BMC-Firmware/discussions/23) | The card is where images already are; manage it from the interface, with a checksum of the bytes that will actually be written. | Listing shipped in v3.25.0; the rest is open |
| [OpenTelemetry: traces, logs and metrics over OTLP, opt-in](https://github.com/excavador-turing/BMC-Firmware/discussions/22) | Three signals to the backend you already run, with a trace that crosses from browser to gateway to daemon. | Designed, not started |
| [A hardware watchdog, so a hung daemon does not mean a trip to the rack](https://github.com/excavador-turing/BMC-Firmware/discussions/24) | The SoC has one; this firmware does not arm it yet. The last gap where recovery means walking to the hardware. | Open |
| [Choose the self-signed certificate's key type and validity](https://github.com/excavador-turing/BMC-Firmware/discussions/26) | Two settings with sane defaults, and a renamed board that reissues its own certificate. | Open |
| [Remote syslog, and an audit line for every mutating API call](https://github.com/excavador-turing/BMC-Firmware/discussions/27) | Logs that survive the board, and one line per call that changed something. | Open |
| [VLANs on the board's switch, with apply-then-confirm](https://github.com/excavador-turing/BMC-Firmware/discussions/25) | Segment the management network — with a change that reverts itself unless confirmed through the new configuration. | Backlog |

## Shipped, recently

The fifteen [features](features/index.md) each have a page with the
measurement behind them. The most recent, with the release that carried each:

| Feature | Release |
|---|---|
| [Flash a module from the card](features/flash-from-the-card.md) | BMC-UI 3.25.0, firmware v2.26.0 |
| Temperature on Board Health, with the trip that explains the fan | BMC-UI 3.26.0, firmware v2.27.0 |
| The firmware listing survives a reboot | bmcd 2.35.0, firmware v2.27.0 |
| [A certificate that does not rot](features/a-certificate-that-does-not-rot.md) | firmware v2.23.0 |
| [One page over every board](features/one-page-over-every-board.md) | BMC-UI 3.22.0 |

## How a thing gets from here to there

A feature is a ticket in the maintainer's tracker, a Discussion here, and then
a page under Features with the numbers that prove it — in that order. The
[known-faults page](reference/known-faults.md) is the other half of this one:
what is wrong today, with the ticket that tracks it. A roadmap that lists only
what is coming is advertising.
