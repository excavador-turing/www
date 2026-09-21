---
title: See what the board sees
render_macros: true
hide:
- navigation
- toc
feature:
  order: 6
  icon: sensors.svg
  summary: The temperature sensor upstream never described, and a fan that says why it is where it is.
  lede: The Turing Pi 2 has a temperature sensor. Upstream's device tree never described it, so nothing
    could read it and the fan ran against nothing.
  capture: info.png
  alt: 'The Overview: temperature and the trip that explains the fan''s step, beside storage, load, memory
    and the clock.'
  caption: 'The Overview: temperature and the trip that explains the fan''s step, beside storage, load,
    memory and the clock.'
  proofs:
  - n: '5'
    of: trip points the fan follows
    source: the board's own thermal zone and /metrics
    as_of: '2026-09-12'
  - n: '40'
    of: metric families the board exposes
    source: the board's own thermal zone and /metrics
    as_of: '2026-09-12'
  - n: '0'
    of: temperature readings upstream can take
    source: the board's own thermal zone and /metrics
    as_of: '2026-09-12'
  next:
    demo:
      href: ../../#demo/fork
      text: See it in the demo
      note: The Overview tab, with real readings from a board.
    do:
      href: ../../guides/monitor-it/
      text: Do it on your board
      note: The metrics port, a scrape config and the dashboard.
    evidence:
      href: ../../reference/metrics/
      text: The evidence
      note: Every family the board can measure, catalogued.
    related:
      href: ../the-board-describes-itself/
      text: The board describes its own API
      note: Where the readings on this page come from.
description: "The Turing Pi 2 board temperature, the fan step and the trip that explains it, plus every reading the stock firmware never described."
---

{{ feature_screen() }}

<div class="tp-argument" markdown>

## The argument

A fan speed nobody can explain is a fault waiting to be misdiagnosed. The board now reports the temperature, the trip points and which trip put the fan where it is, so "why is the fan at step 4" has an answer. Nothing here writes to the sensor; a held fan is taken back by the daemon above the hottest active trip.

[The full argument, with every measurement →](../why/see-what-the-board-sees.md)

</div>
