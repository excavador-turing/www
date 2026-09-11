# Features

Eight things the board does now that it did not before. Each section says
what changed, why it mattered on a real board, and where the evidence is; the
longer articles are linked where one exists. The
[comparison](../reference/comparison.md) carries the same ground row by row,
including the rows where upstream is ahead.

## A bad image undoes itself

Upstream's firmware update promotes a new image unconditionally: reaching the
end of boot is taken as proof that the board works. Two images this fork built
would have passed that bar while being broken. One could not link the daemon,
so the web interface never came up. The other had silently lost the switch
driver from its kernel, which leaves the BMC perfectly reachable and **all four
compute modules cut off the network**. Once promoted, either needs a trip to
the rack.

Here a new image boots *tentatively*, and is kept only if the board comes back
right; otherwise the next boot is the previous image, with nobody's hands on
it. On this board that has meant 18 updates, 1 automatic rollback, 0 trips.

[How the gate decides →](updates-that-undo-themselves.md) ·
[what it has decided so far](../reference/gate-history.md) ·
[recovering when it cannot](../guides/recover-a-bad-flash.md)

## Pick a version, from anywhere

Upstream's board has one firmware source, hard-coded, and it disagrees with
itself: the mirror stops at v2.0.5 while the GitHub releases reach v2.1.0, so
following the documented update path can *downgrade* a board. This fork makes
the sources a setting — GitHub releases, an HTTP directory, or a path on the
SD card — and lists every candidate with two independent facts: how it
compares to what is running (numerically, because `"2.10.0" < "2.9.0"` as
text), and whether its published checksum was verified on download.

[Sources, candidates and checksums →](pick-a-version.md) ·
[upgrading from the stock firmware](../guides/upgrade-from-stock.md)

## See what the board sees

The Turing Pi 2 has a temperature sensor. Upstream's device tree never
described it, so nothing could read it, and the fan — with nothing to regulate
against — ran at a fixed speed somebody once wrote down. This fork adds the
sensor to the device tree and lets the kernel's `step_wise` thermal governor
drive the fan across five declared trip points. The interface shows the
temperature, the trip the board is in, and therefore *why* the fan is where it
is.

[The sensor, the governor and the fan →](see-what-the-board-sees.md) ·
[what is still not covered: no critical trip](../reference/known-faults.md)

## A console to every module

Every compute module has a serial console, and reaching it used to mean a USB
adapter and three jumper wires on the board's header. The BMC is already wired
to all four; this fork puts them in the browser, one tab per module. The
daemon keeps a 16 KiB ring buffer per module, so a console opened at nine
still shows the panic from three in the morning, and the panel says whether
what it shows is live.

[Four consoles, and what they replay →](a-console-to-every-module.md)

## Power and USB, per module

Power, reset, USB routing and flashing, per module, from the interface, the
API and the command line alike — `tpi` reaches every endpoint this fork added,
which until 1.1.0 were reachable only from the browser. A flash that cannot
tell which module it is about to write, as on a v2.5 board with two modules in
maskrom, refuses rather than guesses.

[The command line →](../reference/cli.md) ·
[the node operations](../reference/api/nodes.md)

## Metrics, on their own port

Upstream exposes no metrics. This fork serves every family the board can
measure in Prometheus text format, on a listener of its own that cannot reach
the control API — so a scraper holds no credential, and a scraper's mistake
cannot reboot anything. The catalogue on this site is generated from the
daemon's source, so it cannot describe a metric the daemon does not emit.

[The metrics catalogue →](../reference/metrics.md) ·
[a scrape config and a dashboard](../guides/monitor-it.md)

## Network and time

Interfaces and switch ports, per module, with link state and speed; an NTP
source you can set; and whether the clock actually synchronised — the source,
its stratum and the measured offset, not a checkbox. Upstream's interface shows
an address and stops.

[Network and time in the API →](../reference/api/network.md)

## Name it, export it

The hostname is a control — API, `tpi hostname`, a card on the Settings tab —
and so is the clock. The board's configuration exports and imports, so a
second board starts from the first instead of from a checklist. All of it is
described by an OpenAPI 3.1 document the board serves itself, which is what
this site's API reference is generated from.

[The board in the API →](../reference/api/board.md) ·
[every operation on one page](../reference/api/index.md)
