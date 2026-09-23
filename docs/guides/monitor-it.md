---
description: "Scrape the Turing Pi 2 BMC's own metrics into Prometheus and get a dashboard of temperature, fan, power and update history."
---

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

## 1. Point a scrape at port 9110

There is no credential to fetch. `/metrics` is served on its own listener,
plain HTTP, and that listener serves nothing else — so a scrape config
pointed at it cannot reach `/api/bmc` and cannot power off a node, which is
the property the old token was there to provide.

On a board older than **v2.15.0** the endpoint is on `:443` and wants a token
from `tpi metrics show`. Both are gone.

## 2. Scrape the board

The scrape config is on the [metrics reference](../reference/metrics.md#scraping-it).
Two things about it are easy to get wrong:

- It is plain HTTP on port 9110 — no `scheme: https`, no `tls_config`, no
  token. An earlier version of this page said the board's expired certificate
  forced `insecure_skip_verify`; that was the old `:443` endpoint, gone since
  v2.15.0, and the sentence outlived it.
- Set the `instance` label deliberately. It follows the board's hostname, so
  renaming the board splits its history in two, and renaming back does not
  rejoin them.

## 3. Import the dashboard

In Grafana: **Dashboards → New → Import**, upload the file, and pick your
Prometheus-compatible datasource when it asks for `DS_PROMETHEUS`. It works
against Prometheus, VictoriaMetrics and Mimir; nothing in it is specific to
one of them.

### The data source is the scraper, not the board

The board serves a page of numbers; it does not store them and it cannot
answer a query. Grafana's Prometheus data source has to point at whatever
**scrapes** the board — a Prometheus server, VictoriaMetrics, Mimir — and
never at the board itself. The chain is:

```
board :9110  ──scraped by──▶  Prometheus :9090  ──queried by──▶  Grafana
```

So the URL in *Connections → Data sources → Prometheus* is the scraper's,
typically `http://<prometheus host>:9090`. If you put the board's address
there, *Save & test* fails and Grafana's log says
**`failed to get Prometheus heuristics`** — Grafana asked the URL a question
only a Prometheus server can answer, and got the metrics page instead. The
`curl` you ran against `:9110` returning data is exactly what it should do,
and is not the thing Grafana needs.

If you have Grafana and nothing scraping yet, the smallest Prometheus that
will do is one container and one file. `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: turingpi-bmc
    static_configs:
      - targets: ["192.168.1.59:9110"]   # your board
        labels:
          instance: bmc-1                  # your name for it
```

```console
$ docker run -d --name prometheus -p 9090:9090 \
    -v "$PWD/prometheus.yml:/etc/prometheus/prometheus.yml" prom/prometheus
```

Then the data source URL is `http://<the host running that container>:9090`
— `http://prometheus:9090` if Grafana runs in the same Compose network,
`http://localhost:9090` if both run on the same machine outside containers.
Confirm the scrape before blaming the dashboard: `http://<host>:9090/targets`
should list `turingpi-bmc` as **UP**.

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

On **2026-09-09** a board lost roughly 1 MB a minute twice and had to be
power-cycled by hand both times. The board-level series could show that memory
was going and **not where**, so two outages produced no diagnosis at all.

This series ended it on the third occasion, in about fifteen minutes. Board
memory fell 0.88 MB a minute while the daemon's own resident set sat at 18.7 MB
and did not move. That flat line ruled out `bmcd`, which five separate
reproductions had failed to convict, and the process table then gave up the
answer immediately: the mDNS responder, at 33.8 MB and climbing. See
[what is and isn't fixed](../reference/known-faults.md).

Beside it is **Threads**, and the pairing is what makes either useful: a heap
leak grows the resident set while the thread count stays flat, whereas a leaked
task or an unreaped worker grows both, because every thread carries a stack.
During the outage neither series existed, so the two could not be told apart.

If you run this fork unattended, these are the panels to alert on, and the
alert below would have paged before either outage rather than after.

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
