---
title: Changelogs
hide:
  - toc
---

# Every component's changelog

What changed in each release, taken from each repository's own `CHANGELOG.md`. For the same history as one post per firmware release, newest first, read [the news](../news/index.md).

<div class="tp-plates">
<a class="tp-plate" href="../firmware/"><b>BMC-Firmware</b><span>The firmware image — what you flash onto the board. It carries a `bmcd`, a `BMC-UI` and a `tpi`, so this is the version to quote when reporting anything.</span><span class="tp-plate__meta">v2.34.0 · 21 September 2026 · 31 releases</span></a>
<a class="tp-plate" href="../bmcd/"><b>bmcd</b><span>The daemon: the API, the update logic, the metrics.</span><span class="tp-plate__meta">v2.37.0 · 20 September 2026 · 39 releases</span></a>
<a class="tp-plate" href="../bmc-ui/"><b>BMC-UI</b><span>The web interface the board serves.</span><span class="tp-plate__meta">v3.33.0 · 21 September 2026 · 31 releases</span></a>
<a class="tp-plate" href="../tpi/"><b>tpi</b><span>The command-line client.</span><span class="tp-plate__meta">v1.9.0 · 20 September 2026 · 14 releases</span></a>
</div>

These four version together. The firmware image carries a `bmcd`, a `BMC-UI` and a `tpi`, and the board's About tab names all four — so a firmware version is the one to quote when reporting anything.

New firmware releases come through [the feed](../feed.xml). What is planned rather than done is on the [roadmap](../roadmap.md), ordered by votes.

Refreshed 21 September 2026 by `just refresh-changelog`.
