---
title: Roadmap
description: "What is planned for the Turing Pi 2 BMC firmware and what has shipped: 7 open ideas ordered by your vote, proposed and voted on in GitHub Discussions."
hide:
  - navigation
  - toc
---

<div class="tp-hero-band" markdown>
<span class="tp-eyebrow">Roadmap</span>
# 7 things planned. Your vote orders them.

<p>Every card is a GitHub Discussion. Upvote the ones you want and this page reorders itself: the votes are read every hour, so a vote cast now is on the page within one. Not on the list? <a href="https://github.com/excavador-turing/BMC-Firmware/discussions/new?category=ideas">Propose it</a> — a sentence about the problem is enough.</p>
</div>

<div class="tp-proof">
<div><b>7</b><span>planned, ordered by votes</span></div>
<div><b>18</b><span>votes cast, read hourly</span></div>
<div><b>2</b><span>shipped from this list</span></div>
</div>

<div class="tp-ideas">
<a class="tp-idea tp-idea--open" href="https://github.com/excavador-turing/BMC-Firmware/discussions/24"><b class="tp-idea__votes">3<small>votes</small></b><span class="tp-idea__title">A hardware watchdog, so a hung daemon does not mean a trip to the rack</span><span class="tp-idea__what">The SoC has a watchdog and this firmware does not arm it.</span><span class="tp-idea__status">Open</span></a>
<a class="tp-idea tp-idea--open" href="https://github.com/excavador-turing/BMC-Firmware/discussions/29"><b class="tp-idea__votes">3<small>votes</small></b><span class="tp-idea__title">Manage the BMC&#x27;s SSH keys and change its password from the interface and the fleet</span><span class="tp-idea__what">The only way to put an SSH key on the BMC, or take one off, is to log in over SSH and edit <code>/root/.ssh/authorized_keys</code> by hand.</span><span class="tp-idea__status">Open</span></a>
<a class="tp-idea tp-idea--open" href="https://github.com/excavador-turing/BMC-Firmware/discussions/27"><b class="tp-idea__votes">2<small>votes</small></b><span class="tp-idea__title">Remote syslog, and an audit line for every mutating API call</span><span class="tp-idea__what">Ship the board&#x27;s logs somewhere that survives it, and write one line per call that changes state — who, what, from where.</span><span class="tp-idea__status">Open</span></a>
<a class="tp-idea tp-idea--started" href="https://github.com/excavador-turing/BMC-Firmware/discussions/22"><b class="tp-idea__votes">1<small>vote</small></b><span class="tp-idea__title">OpenTelemetry: traces, logs and metrics over OTLP, opt-in</span><span class="tp-idea__what">The board already exposes Prometheus metrics on their own credential-free listener, which is the right thing when the cluster is down.</span><span class="tp-idea__status">Designed, not started</span></a>
<a class="tp-idea tp-idea--started" href="https://github.com/excavador-turing/BMC-Firmware/discussions/23"><b class="tp-idea__votes">1<small>vote</small></b><span class="tp-idea__title">SD card: checksums computed on the board, upload, rename and move</span><span class="tp-idea__what">The interface can now list what is on the card and say which files can be written to a module (v3.25.0).</span><span class="tp-idea__status">Listing shipped in v3.25.0; the rest is open</span></a>
<a class="tp-idea tp-idea--open" href="https://github.com/excavador-turing/BMC-Firmware/discussions/26"><b class="tp-idea__votes">1<small>vote</small></b><span class="tp-idea__title">Choose the self-signed certificate&#x27;s key type and validity</span><span class="tp-idea__what">When no operator certificate is installed the board issues its own: EC P-384, real names, 825 days, renewed 30 days out.</span><span class="tp-idea__status">Open</span></a>
<a class="tp-idea tp-idea--open" href="https://github.com/excavador-turing/BMC-Firmware/discussions/46"><b class="tp-idea__votes">1<small>vote</small></b><span class="tp-idea__title">ACME against a private CA, so the certificate renews itself</span><span class="tp-idea__what">ACME is a protocol, not a company.</span><span class="tp-idea__status">Open</span></a>
</div>

Something broken rather than missing? [Report it](feedback.md), and read [what is and isn't fixed](reference/known-faults.md) first, because it may already be there with a ticket.

## Shipped from this list

Voted for, built, released. Each card still opens its discussion.
<div class="tp-ideas tp-ideas--done">
<a class="tp-idea tp-idea--shipped" href="https://github.com/excavador-turing/BMC-Firmware/discussions/25"><b class="tp-idea__votes">5<small>votes</small></b><span class="tp-idea__title">VLANs on the board&#x27;s switch, with apply-then-confirm</span><span class="tp-idea__what">**VLANs on the board&#x27;s switch — shipped in firmware v2.33.0, with three ways to use them**</span><span class="tp-idea__status">Shipped in v2.33.0</span></a>
<a class="tp-idea tp-idea--shipped" href="https://github.com/excavador-turing/BMC-Firmware/discussions/45"><b class="tp-idea__votes">1<small>vote</small></b><span class="tp-idea__title">Install a certificate from your own CA</span><span class="tp-idea__what">If you run a private certificate authority — step-ca, your router&#x27;s, your own — you can already trust its root in your browser and get a green padlock on anything it issues.</span><span class="tp-idea__status">Shipped in v2.33.0</span></a>
</div>

## Recently shipped

One post per firmware release, from the repositories' own changelogs — [all of them](news/index.md), or [by feed](feed.xml).

<div class="tp-releases">
<a href="news/v2.39.0/"><b>v2.39.0</b><span>23 September 2026</span></a>
<a href="news/v2.38.0/"><b>v2.38.0</b><span>22 September 2026</span></a>
<a href="news/v2.37.0/"><b>v2.37.0</b><span>22 September 2026</span></a>
<a href="news/v2.36.0/"><b>v2.36.0</b><span>22 September 2026</span></a>
<a href="news/v2.35.0/"><b>v2.35.0</b><span>21 September 2026</span></a>
</div>

## How a thing gets from here to there

A feature is a ticket in the maintainer's tracker, a Discussion here, and then a page under [Features](features/index.md) with the numbers that prove it — in that order. The [known-faults page](reference/known-faults.md) is the other half of this one: what is wrong today, with the ticket that tracks it. A roadmap that lists only what is coming is advertising.

Votes read 24 September 2026 by `just refresh-roadmap`, which runs every hour.

<div class="tp-next">
<a href="news/"><b>What shipped →</b><span>One post per firmware release, newest first.</span></a>
<a href="feedback/"><b>Propose or report →</b><span>Ideas carry votes; faults carry tickets.</span></a>
<a href="reference/known-faults/"><b>What is not fixed →</b><span>The honest list, each with a ticket.</span></a>
<a href="features/"><b>What it does today →</b><span>Every feature, with the measurement behind it.</span></a>
</div>
