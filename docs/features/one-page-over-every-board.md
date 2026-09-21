---
title: One page over every board
render_macros: true
since: v2.22.0
hide:
- navigation
- toc
feature:
  order: 3
  icon: fleet.svg
  summary: One page drives every board in the cluster, and holds no credential of its own.
  lede: A board that can reflash four computers should not face the internet. One page inside the cluster
    drives them all, with every control a board has, and it holds no credential of its own.
  capture: fleet.png
  alt: Both boards on one page, each answering for itself. A board that is down costs you its card and
    nothing else.
  caption: Both boards on one page, each answering for itself. A board that is down costs you its card
    and nothing else.
  proofs:
  - n: '1'
    of: hostname exposed for the whole estate
    source: the fleet interface as shipped in BMC-UI 3.29.0
    as_of: '2026-09-13'
  - n: '9'
    of: tabs per board, the same ones a board serves
    source: the fleet interface as shipped in BMC-UI 3.29.0
    as_of: '2026-09-13'
  - n: '0'
    of: credentials held by the page
    source: the fleet interface as shipped in BMC-UI 3.29.0
    as_of: '2026-09-13'
  next:
    demo:
      href: ../../#demo/fleet
      text: See it in the demo
      note: Two boards on one page, from a real board's capture.
    do:
      href: ../../guides/install/
      text: Do it on your board
      note: Install the firmware each board in the fleet runs.
    evidence:
      href: ../../reference/known-faults/
      text: The evidence
      note: What is still not fixed, including where trust is assumed.
    related:
      href: ../who-may-reach-this-board/
      text: Who may reach this board
      note: The two ways in, and what a trusted proxy buys.
description: "Drive every Turing Pi 2 in the cluster from one page that holds no credential of its own and never exposes a board to the network."
---

{{ feature_screen() }}

<div class="tp-argument" markdown>

## The argument

The page renders each board's own tabs from the same data layer the board's page uses, so the two cannot drift apart. It holds no credential: a gateway in front of it authenticates the operator and presents a client certificate the board trusts, which is why no board needs to be reachable from anywhere else.

[The full argument, with every measurement →](../why/one-page-over-every-board.md)

</div>
