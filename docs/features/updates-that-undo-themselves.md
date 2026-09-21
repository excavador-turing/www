---
title: Updates that undo themselves
render_macros: true
since: v2.7.0
hide:
- navigation
- toc
feature:
  order: 1
  icon: undo.svg
  summary: A new image boots on trial and is kept only if the board comes back right.
  lede: Upstream promotes a new image the moment it boots, which proves the kernel started and nothing
    else. Here an image boots on trial and is kept only if the board answers properly afterwards.
  capture: firmware.png
  alt: 'The Firmware tab: the running slot, the image it can fall back to, and when the gate last promoted
    one.'
  caption: 'The Firmware tab: the running slot, the image it can fall back to, and when the gate last
    promoted one.'
  proofs:
  - n: '26'
    of: updates taken on this board
    source: the board's own bmcd_firmware_promotion_total counter
    as_of: '2026-09-12'
  - n: '1'
    of: rolled back by the board itself
    source: the board's own bmcd_firmware_promotion_total counter
    as_of: '2026-09-12'
  - n: '0'
    of: trips to the rack
    source: the board's own bmcd_firmware_promotion_total counter
    as_of: '2026-09-12'
  next:
    demo:
      href: ../../#demo/fork
      text: See it in the demo
      note: The Firmware tab, answering from a real board's data.
    do:
      href: ../../guides/install/
      text: Do it on your board
      note: Install this firmware, and what to read first.
    evidence:
      href: ../../reference/gate-history/
      text: The evidence
      note: Every decision the gate has made here, read off the board.
    related:
      href: ../pick-a-version/
      text: Pick a version, from anywhere
      note: Where the image the gate judges comes from.
description: "A new BMC image boots on trial and is kept only when the board answers properly afterwards, so a bad flash undoes itself without a trip to the rack."
---

{{ feature_screen() }}

<div class="tp-argument" markdown>

## The argument

The gate asks three questions after a new image boots, not one. Two images this fork built would have passed "did it boot" while being broken, and one of them cut all four compute modules off the network. The one rollback on record was deliberate: an image with its staged note tampered to claim an older version, refused in about 35 seconds.

[The full argument, with every measurement →](../why/updates-that-undo-themselves.md)

</div>
