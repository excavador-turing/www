---
title: Pick a version, from anywhere
render_macros: true
hide:
- navigation
- toc
feature:
  order: 9
  icon: versions.svg
  summary: This fork, upstream, or the SD card, every candidate checksum-verified and compared numerically.
  lede: Upstream ships one hard-coded firmware source, and its two catalogues disagree by a whole release.
    Here the source is a setting, and every candidate arrives with its checksum.
  capture: sources.png
  alt: 'Where this board looks for firmware: this fork, upstream''s two catalogues and the SD card, with
    the checksum each publisher does or does not ship.'
  caption: 'Where a board looks for firmware: this fork, upstream''s two catalogues and the SD card, with
    the checksum each publishes.'
  proofs:
  - n: '3'
    of: 'kinds of source: this fork, upstream, the card'
    source: reference/comparison.md, checked against both upstream catalogues
    as_of: '2026-09-08'
  - n: '2'
    of: upstream catalogues, disagreeing by a release
    source: reference/comparison.md, checked against both upstream catalogues
    as_of: '2026-09-08'
  - n: '0'
    of: checksums upstream publishes
    source: reference/comparison.md, checked against both upstream catalogues
    as_of: '2026-09-08'
  next:
    demo:
      href: ../../#demo/fork
      text: See it in the demo
      note: The firmware sources, with what each one publishes.
    do:
      href: ../../guides/upgrade-from-stock/
      text: Do it on your board
      note: Move off stock, and what to expect on the way.
    evidence:
      href: ../../reference/comparison/
      text: The evidence
      note: The two upstream catalogues, and what each returns.
    related:
      href: ../updates-that-undo-themselves/
      text: Updates that undo themselves
      note: What happens if the version you picked is bad.
description: "Install firmware from this fork, from upstream or from the SD card, every candidate checksum-verified and compared by version rather than by name."
---

{{ feature_screen() }}

<div class="tp-argument" markdown>

## The argument

Versions are compared numerically, so 2.10 is not older than 2.9 -- which a string comparison says and which upstream's own updater believes. A source that publishes no checksum is labelled TLS only rather than treated as verified, because trusting a transport is not the same as verifying bytes.

[The full argument, with every measurement →](../why/pick-a-version.md)

</div>
