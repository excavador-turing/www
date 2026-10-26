---
title: Documentation
description: 'Every guide and reference for this Turing Pi 2 BMC firmware: install it, upgrade from stock, recover a bad flash, segment the network, monitor it.'
slug: guides
tableOfContents: false
tp:
  htmlTitle: Overview
  ogTitle: Overview
---

A Guide instructs, a Reference lists. Start with the guide that matches where
your board is; the references are there when a guide sends you to one.

<div class="tp-cols">


<div>

## Guides

- **[Install](/guides/install/)** — putting this on your own board
- **[Upgrading from stock](/guides/upgrade-from-stock/)** — from the firmware it shipped with, and what to expect on the way
- **[Recover a bad flash](/guides/recover-a-bad-flash/)** — what to do when it goes wrong
- **[Should it face the internet?](/guides/facing-the-internet/)** — no, and what to expose instead
- **[Your own certificate](/guides/your-own-certificate/)** — a green padlock, a working console, and why not Let's Encrypt
- **[Monitor it](/guides/monitor-it/)** — the metrics port, a scrape config, the dashboard
- **[Developing](/guides/development/)** — build it, and iterate without cutting a release

</div>

<div>

## Reference

- **[The API](/reference/api/)** — OpenAPI 3.1, served by the board; [every operation](/reference/api/operations/) on one page
- **[Command line](/reference/cli/)** — `tpi`, which reaches every endpoint above
- **[Metrics](/reference/metrics/)** — every family the board exposes
- **[Upstream vs this fork](/reference/comparison/)** — row by row, with evidence, including where upstream is ahead
- **[The factory firmware](/reference/factory-firmware/)** — what a board ships with, captured
- **[What is and isn't fixed](/reference/known-faults/)** — the honest list, with tickets
- **[Changelog](/changelog/)** — every release of every component

</div>


</div>
