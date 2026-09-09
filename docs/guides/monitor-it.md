# Monitor it

The board publishes [32 metric families](../reference/metrics.md). This page is
the shortest path from that to a screen you can look at, and a description of
what the screen is for.

<div class="grid" markdown>

[Download the dashboard :material-download:](https://raw.githubusercontent.com/excavador-turing/BMC-Firmware/hive/dashboards/turingpi-bmc.json){ .md-button .md-button--primary }

</div>

That link is the file itself, in the firmware repository. Releases from
**v2.12.0** onward also carry it as `turingpi-bmc-dashboard.json`, checksummed
in `SHA256SUMS`, so a dashboard and the firmware whose metrics it reads are
versioned together. Take the release copy if you pin firmware versions; take
the link above for the current one.

This page deliberately does not host its own copy. A dashboard duplicated into
a docs site is a dashboard that drifts from the daemon it describes, and the
drift is invisible: every panel still renders, just against metrics that have
moved.

## 1. Get the scrape credential

```console
$ tpi metrics show
username  metrics
token     <32 hex characters>
```

That token answers `/metrics` and is **rejected by `/api/bmc`**. Use it, not
the root password — a scrape config is a file on another machine, and it
should not be able to power off a node.

## 2. Scrape the board

The scrape config is on the [metrics reference](../reference/metrics.md#scraping-it).
Two things about it are easy to get wrong:

- The certificate on the board is expired, so `insecure_skip_verify` is
  required today. That is a [known fault](../reference/known-faults.md), not a
  design choice.
- Set the `instance` label deliberately. It follows the board's hostname, so
  renaming the board splits its history in two, and renaming back does not
  rejoin them.

## 3. Import the dashboard

In Grafana: **Dashboards → New → Import**, upload the file, and pick your
Prometheus-compatible datasource when it asks for `DS_PROMETHEUS`. It works
against Prometheus, VictoriaMetrics and Mimir; nothing in it is specific to
one of them.

## What it shows

Five rows, in the order you would ask the questions.

| row | the question it answers |
|---|---|
| **Board** | Is the BMC being scraped, is the daemon up, how hot is it, and what is the fan doing about it |
| **Compute modules** | Which rails are on, how long each module has been powered, and whether any module is islanded |
| **Switch** | Per-port carrier, traffic and errors |
| **BMC health** | Load, memory, and how far the clock has drifted |
| **Firmware** | What the promotion gate has decided, and when |

### Read the scrape panel first

*Scrape* is `up`. Every other panel on the page is meaningless when it is 0,
because a stalled series looks exactly like a flat one. This is the panel that
distinguishes *nothing is happening* from *nobody is watching*.

### The panel that draws nothing when healthy

*A node's switch port is down while its rail is ON* is the islanded-module
signal, and **an empty graph is the good outcome**. That is uncomfortable to
trust, so it was verified by inversion rather than by belief: the `== 1` form
of the same join returns exactly four series, which is what proves the `== 0`
form returning none means "no module is islanded" and not "the query is
broken".

If you adapt it, keep its port filter as `port=~"node.*"`. Only
`bmcd_switch_port_present` carries a `kind` label; filtering the link and byte
counters by `kind` silently matches nothing.

### The thermal loop

*Temperature against fan step* is the whole
[thermal argument](../features/see-what-the-board-sees.md) in one graph: the
governor raising the step as the board crosses a trip point, and the
temperature responding. A fan step with no visible reason is the thing this
fork set out to remove.

### Memory, and why there are four series

Three series come from the board — total, available, free. The fourth,
`bmcd (resident)`, is the daemon's own resident set, and it exists because of
a specific failure.

On **2026-09-09** a board left with a browser open on the firmware page lost
roughly 1 MB per minute and stopped answering four hours later, at about 70 MB
free of 116 MB. The board-level series could show that memory was being
consumed and **not by what**, so the diagnosis had to be argued from timing
rather than measured. One number closes that gap.

That fault is still open — it is [SQU-172](../reference/known-faults.md), and
the leak is not yet proven. If you run this fork unattended, this is the panel
to alert on.

### The gate's record

*Promotions* and *Rollbacks* count what the
[health gate](../features/updates-that-undo-themselves.md) decided at each
boot. Before these existed, that record lived only in
`/mnt/overlay/postupdate.log` — which is to say it was readable only on a
board that answers, and the case you most want it for is the one where the
board does not.

A rollback is not a fault. It is the gate working. But an unexpected step on
that graph is worth reading the log for, and the log survives the reboot it
describes.

!!! note "`promoted` is derived, not counted"
    The gate writes no single line meaning *kept*, so promotions are attempts
    minus rollbacks. A board whose power is cut mid-gate therefore counts as
    promoted. The alternative was a metric that undercounts silently, which is
    worse than one whose definition is written down.

## Alerting

Nothing here ships alert rules. Two conditions are worth writing yourself:

```promql
# The BMC stopped answering, but its modules did not.
up{job="turingpi-bmc"} == 0

# Memory heading for the floor: SQU-172's signature.
predict_linear(bmcd_memory_available_bytes[1h], 4*3600) < 40e6
```

The second is the one that would have paged before the board went quiet on
2026-09-09 rather than after.
