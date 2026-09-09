# The gate's record

Every count on this site comes from here, and this page comes from the board.

## What the board reports

`bmcd_firmware_promotion_total{result}` is read from the health gate's own log
at scrape time. As of **2026-09-09**:

| result | count |
|---|---|
| promoted | 17 |
| rolled back | 1 |

The one rollback was deliberate: a `v2.8.1-rc1` image with its staged note
tampered to claim `v0.0.1`, to prove the gate could refuse. It did, in about
35 seconds, and the board came back on the version it had.

## Why this page exists

An earlier draft of this site said *"fifteen consecutive clean promotions"*,
and a later one said nineteen. Both were counted by hand across working
sessions and written into prose, and by the time the metric existed to check
them the true figure was **fourteen**. A number that a person maintains is a
number that drifts.

This page then said it was generated from a counter while still being typed by
hand, and drifted from 14 to 17 within a day of being written — the same
failure, one level up. `just refresh-gate-history <board>` now reads the
board's `/metrics` and rewrites the date, the table and the example below. It
refuses rather than guesses if any of the three moves, so a silent no-op
cannot masquerade as a refresh. The articles link here; only this page carries
the figures.

If you are running this firmware, your own board answers the same question:

```console
$ curl -s http://<board>:9110/metrics | grep promotion_total
bmcd_firmware_promotion_total{result="promoted"} 17
bmcd_firmware_promotion_total{result="rolled_back"} 1
```

## How the count is derived

The gate has no single line meaning *kept*. It can finish through the metrics
check, skip that check on a board with no `curl`, or promote anyway when there
is no volume to fall back to. So `promoted` is **attempts minus rollbacks**,
where an attempt is one `tentative boot` line and a rollback is one
`rolling back to the volume` line.

That has one inaccuracy, stated here rather than hidden: a board cut off
mid-gate leaves an attempt with no verdict, and it counts as promoted. It
over-reports success by one, per interruption.

## What a promotion actually proves

Three checks, in order, before the volumes are renamed:

1. **bmcd answers** on `https://127.0.0.1/`, within 120 seconds.
2. **Every compute module's switch port exists** — the case that would leave
   the BMC reachable and all four modules cut off the network.
3. **The image is the one that was staged, and it serves metrics** — the
   version in `/etc/os-release` matches the staged note, and `/metrics`
   answers with `bmcd_build_info`.

A failure at any of them reboots, which lands on the previous image because
nothing has been renamed and the boot variable is one-shot.

!!! warning "What it does not prove"
    The gate only runs on an image that boots far enough to run it. One that
    hangs earlier still needs power cut, which hard-cuts the compute modules.
    A hardware watchdog is the fix and is not built yet.

    It also proves the daemon is *serving*, not that it is *correct in every
    respect*. On 2026-09-09 a board that had passed the gate cleanly went on
    to lose about a megabyte of memory a minute under sustained polling and
    stopped answering four hours later. The gate was not wrong; it was
    answering a question about the first ninety seconds.

## The modules do not notice

Across every promotion and the one rollback, each compute module's
`power_on_time` advanced by exactly the wall-clock time the reboot took. A
firmware update on this fork does not interrupt what the board is running —
which is the difference that made updating it something you can do on a
Tuesday.
