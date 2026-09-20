---
title: Flash a module from the card
render_macros: true
hide:
- navigation
- toc
feature:
  order: 7
  icon: sdcard.svg
  summary: What is on the board's own SD card, what can be written to a module, and why the rest cannot.
  lede: A 2 GB image is usually already on the board's own SD card. Installing it meant typing its path
    from memory into a field, and finding out minutes later whether you had.
  capture: sdcard.png
  alt: 'The picker on bmc-1: what is on the card, what can be written to a module, and how much room is
    left.'
  caption: 'The picker on a board: what is on the card, what can be written to a module, and how much
    room is left.'
  proofs:
  - n: '16'
    of: entries listed off a real card
    source: the picker reading a board's own card
    as_of: '2026-09-11'
  - n: '14'
    of: refused, each with the board's own reason
    source: the picker reading a board's own card
    as_of: '2026-09-11'
  - n: '0'
    of: paths typed from memory
    source: the picker reading a board's own card
    as_of: '2026-09-11'
  next:
    demo:
      href: ../../#demo/fork
      text: See it in the demo
      note: The flash picker, listing a real card's contents.
    do:
      href: ../../reference/cli/
      text: Do it on your board
      note: The same operation from a shell, through tpi.
    evidence:
      href: ../../reference/api/storage/
      text: The evidence
      note: The endpoints the picker calls, as the board describes them.
    related:
      href: ../pick-a-version/
      text: Pick a version, from anywhere
      note: The card is one of three places firmware can come from.
---

{{ feature_screen() }}

<div class="tp-argument" markdown>

## The argument

The interface never decides what is flashable. It asks the board, and the board answers per entry with a reason -- too small, wrong magic, a directory -- so the list and the refusals come from the same place that would do the writing.

[The full argument, with every measurement →](../why/flash-from-the-card.md)

</div>
