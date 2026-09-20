---
title: Questions people actually ask
render_macros: true
hide:
  - toc
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

## Which board revisions does it run on?

**v2.5.2**, on the two boards this fork is developed against. **v2.4**, from
one reader's report. The other revisions are upstream's compatibility list,
not this fork's proof, and the install guide says so rather than implying a
test matrix that does not exist.

[What you need →](guides/install.md)

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
