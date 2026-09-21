---
title: A console to every module
render_macros: true
hide:
- navigation
- toc
feature:
  order: 5
  icon: console.svg
  summary: Four serial consoles in the browser, each replaying the scrollback you missed.
  lede: Reaching a compute module's serial console used to mean a USB adapter and three jumper wires.
    The BMC is already wired to all four, so this fork puts them in the browser.
  capture: console.png
  alt: A module's console in the browser, opened on the scrollback the daemon kept before the tab was.
  caption: A module's console in the browser, opened on the scrollback the daemon kept before the tab
    was.
  proofs:
  - n: '4'
    of: consoles, one per module
    source: the daemon as shipped in bmcd 2.36.3
    as_of: '2026-09-12'
  - n: 16 KiB
    of: of scrollback replayed when you open one
    source: the daemon as shipped in bmcd 2.36.3
    as_of: '2026-09-12'
  - n: '0'
    of: USB adapters and jumper wires
    source: the daemon as shipped in bmcd 2.36.3
    as_of: '2026-09-12'
  next:
    demo:
      href: ../../#demo/fork
      text: See it in the demo
      note: The Console tab, replaying a real recording.
    do:
      href: ../../reference/cli/
      text: Do it on your board
      note: The same consoles from a shell, through tpi.
    evidence:
      href: ../../reference/known-faults/
      text: The evidence
      note: Including the console fault fixed in v2.31.0.
    related:
      href: ../a-certificate-that-does-not-rot/
      text: A certificate that does not rot
      note: Why a console needs a certificate a browser accepts.
description: "A serial console to each of the four compute modules in the browser, replaying the boot output you were not there to watch."
---

{{ feature_screen() }}

<div class="tp-argument" markdown>

## The argument

The daemon keeps the last 16 KiB per module and replays it when a tab opens, because a console opened on a module that has been up for hours would otherwise show nothing at all. A reconnect used to replay the whole buffer underneath what was already on screen; since v2.31.0 it writes only the gap.

[The full argument, with every measurement →](../why/a-console-to-every-module.md)

</div>
