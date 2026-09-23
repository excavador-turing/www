---
title: Questions people actually ask
render_macros: true
hide:
  - toc
description: "Can the board face the internet, does this run on a 2.4, why does the clock say not synchronised: the questions people ask, answered in a sentence."
---

# Questions people actually ask

Every one of these has been asked more than once. The answer is a sentence;
the link is where the reasoning lives.

## Can I put the board on the internet?

**No.** It can reflash four computers, its one account is a full
administrator with no authorization layer under it, and its login deliberately
does not depend on anything outside the board — because the board is what you
reach for when everything outside it is broken. Expose
[one page over every board](features/one-page-over-every-board.md) instead,
which holds no credential of its own.

[Why, at length →](guides/facing-the-internet.md)

## Does upgrading the firmware reboot my nodes?

**No.** Upstream power-cycles all four compute modules to patch the management
computer beside them; this fork leaves their rails alone. Measured on a
nine-node cluster during a live upgrade: **0** modules cycled, **0** cluster
nodes lost, and **48 seconds** for the board itself to come back.

The board's own network drops for those 48 seconds, because the board drives
the switch. The modules keep running throughout.

[The measurement →](guides/upgrade-from-stock.md)

## Can I use my own certificate?

Yes, and you should. If you run a private authority, import its root into your
browser once and every certificate it issues is trusted — which is also the
only fix for the serial console, because a click-through exception is not
applied to a WebSocket.

Getting your certificate onto the board is a control now — the Security tab,
`tpi tls install`, or the API — and it takes effect without a restart.
Automatic renewal over ACME is still on [the roadmap](roadmap.md). Let's
Encrypt is possible and is the wrong tool here, for three reasons.

[All of it →](guides/your-own-certificate.md)

## The password form will not let me type. Is my board broken?

No, and it was not you. Every release from v2.28.0 to v2.36.0 had a fault
in the shared text field that made password boxes read-only: the keystroke
arrived and the interface put the old value straight back, silently.
**v2.37.0 fixes it.**

Until you can install that, change the password over SSH — it is the same
account the interface means:

```console
$ ssh root@BMC
$ passwd
```

On a board still using the password it shipped with, that also clears the
page which blocks the rest of the interface. Nothing needs undoing
afterwards. The full account is in
[what is and isn't fixed](reference/known-faults.md).

## Grafana's Save & test fails with "failed to get Prometheus heuristics". What is wrong?

The data source URL points at the board. The board serves a page of numbers on
port 9110 and cannot answer queries; Grafana needs a Prometheus server (or
VictoriaMetrics, or Mimir) that *scrapes* the board, and its URL is that
server's — `http://<prometheus host>:9090` — never the board's. That `curl`
against `:9110` returns data is correct and is not what Grafana is asking
for. The [monitoring guide](guides/monitor-it.md#the-data-source-is-the-scraper-not-the-board)
has the one-container Prometheus for people who have Grafana and nothing
scraping yet.

## Which board revisions does it run on?

**v2.5.2**, on the two boards this fork is developed against, and **v2.4**,
from {{ boards.from_readers | title_number | lower }} readers' reports — every
one dated and recorded on the install guide. The other revisions are
upstream's compatibility list, not this fork's proof, and the install guide
says so rather than implying a test matrix that does not exist.

[What you need →](guides/install.md)

## The clock says "not synchronised". What now?

Since v2.35.0 the Time card on Settings lists every source chrony knows and
what it thinks of it, in chrony's own terms. Two states cover nearly every
report:

- **unresolved** — the board could not look the name up. It has no working
  resolver, which is what a static address set by hand over SSH leaves
  behind on this image. Give it one on the Network tab (the address card
  takes resolvers), or use the server's address instead of its name.
- **unreachable** — the server never answered: wrong address, a firewall, or
  a router that does not serve NTP at all.

A server that reports itself unsynchronised (stratum 16) is refused, and the
card says so; chrony will not take time from it. The pool the image ships
with is a name too, so a board with no resolver has no source at all — which
is how "not synchronised" looked before the card could say why.

**If the firmware check also says nothing**, the two have one cause. Until
v2.36.0 a source the board could not reach was reported as offering nothing
rather than as unreachable, so a board with no resolver showed an empty
catalogue and no error. It says which source failed and why now.

**If it was fine until a reboot**, and the address is static: on this image
`/etc/resolv.conf` is a link into a memory filesystem and starts empty at
every boot; the address card's stanza rebuilds it as the bridge comes up.
Firmware **v2.35.0** wrote that stanza with a `#` in it, which the board's
`ifup` reads as a comment, so the rebuild failed silently at every boot and
the resolvers were gone by the time you looked — reported from a 2.4 board
on 2026-09-22. **v2.36.0** fixes the stanza and repairs a board that
v2.35.0 already wrote, the first time its daemon starts. If you wrote a
`resolv.conf` into the overlay by hand to get past it, it does no harm and
is no longer needed.

## How much of this is written by a machine?

Some of it, and the parts that matter are read line by line — the API, the
build scripts, the TLS handling, the update gate. Every release is run against
a live board and the patch releases that follow minors are the visible
evidence of that. What CI can prove without hardware it proves; what only a
board can prove is listed as such.

[What is checked, and by what →](contributing.md)

## Where do I report something, or ask for a feature?

A bug goes to [Issues](https://github.com/excavador-turing/BMC-Firmware/issues/new/choose),
a question to
[Q&A](https://github.com/excavador-turing/BMC-Firmware/discussions/categories/q-a),
and a feature to
[Ideas](https://github.com/excavador-turing/BMC-Firmware/discussions/categories/ideas),
where **{{ roadmap.count }} are waiting and {{ roadmap.votes }} votes have
been cast**. The roadmap is ordered by those votes.

[Every door →](feedback.md)

## What changed recently?

Firmware **{{ releases.firmware.newest }}** is the newest of
{{ releases.total }} releases across four components. The changelog is each
repository's own, not a summary, and there is a feed.

[The news →](news/index.md) · [Every component's changelog →](changelog/index.md) · [Follow by feed →](feed.xml)

<div class="tp-next">
<a href="features/"><b>What it does →</b><span>{{ features.count }} features, each with the measurement behind it.</span></a>
<a href="guides/install/"><b>Put it on your board →</b><span>Install, or try it from an SD card first.</span></a>
<a href="reference/known-faults/"><b>What is not fixed →</b><span>{{ faults.count }} open faults, each with a ticket.</span></a>
<a href="roadmap/"><b>Vote on what comes next →</b><span>Ordered by the votes it has.</span></a>
</div>
