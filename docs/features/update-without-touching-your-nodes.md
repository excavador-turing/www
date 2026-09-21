---
title: Update the BMC without touching your nodes
render_macros: true
hide:
- navigation
- toc
feature:
  order: 2
  icon: rails.svg
  summary: Patching the management computer leaves the four compute modules powered.
  lede: Upstream power-cycles all four compute modules to patch the management computer beside them. This
    fork leaves their rails alone, so updating the board does not take the cluster down.
  capture: nodes.png
  alt: The four compute modules, powered and counted in uptime. A BMC upgrade leaves every one of them
    exactly like this.
  caption: The four compute modules, powered and counted in uptime, across a BMC upgrade.
  proofs:
  - n: '0'
    of: modules power-cycled by a BMC update
    source: measured on a nine-node cluster during a live upgrade
    as_of: '2026-09-08'
  - n: '0'
    of: cluster nodes lost
    source: measured on a nine-node cluster during a live upgrade
    as_of: '2026-09-08'
  - n: 48 s
    of: for the board itself to come back
    source: measured on a nine-node cluster during a live upgrade
    as_of: '2026-09-08'
  next:
    demo:
      href: ../../#demo/fork
      text: See it in the demo
      note: The Nodes tab, with every module powered and counted.
    do:
      href: ../../guides/upgrade-from-stock/
      text: Do it on your board
      note: Coming from stock firmware, step by step.
    evidence:
      href: ../../reference/comparison/
      text: The evidence
      note: This row and twelve others, each with its method.
    related:
      href: ../updates-that-undo-themselves/
      text: Updates that undo themselves
      note: What happens if the image you are updating to is bad.
description: "Update the Turing Pi 2 BMC while the four compute modules stay powered and running, measured across every flash on these boards."
---

{{ feature_screen() }}

<div class="tp-argument" markdown>

## The argument

Upstream cycles the modules because its update path resets the board's USB multiplexer and power rails together. Separating them is most of the change. The cost of not separating them is that patching a management computer becomes a cluster outage, which is the opposite of what a BMC is for.

[The full argument, with every measurement →](../why/update-without-touching-your-nodes.md)

</div>
