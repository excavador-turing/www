---
title: Fresh, and fixed
render_macros: true
hide:
- navigation
- toc
feature:
  order: 4
  icon: fresh.svg
  summary: A longterm kernel, a supported Buildroot, and six named faults taken out.
  lede: Upstream's last release was February 2025, on a kernel that is not a longterm release and a Buildroot
    that is end of life. This fork tracks both and has taken out six named faults.
  capture: about.png
  alt: 'What the board says it is running: kernel, daemon, interface and firmware, each a version you
    can check against a release.'
  caption: 'The board''s About tab: kernel, daemon, interface and firmware, each a version you can check
    against a release.'
  proofs:
  - n: '6.12'
    of: LTS kernel, against upstream's 6.8
    source: reference/comparison.md, read from a running board
    as_of: '2026-09-08'
  - n: '107'
    of: releases across four components
    source: reference/comparison.md, read from a running board
    as_of: '2026-09-08'
  - n: '6'
    of: named faults taken out
    source: reference/comparison.md, read from a running board
    as_of: '2026-09-08'
  next:
    demo:
      href: ../../#demo/fork
      text: See it in the demo
      note: The About tab, naming every component's version.
    do:
      href: ../../guides/upgrade-from-stock/
      text: Do it on your board
      note: Move a board off the firmware it shipped with.
    evidence:
      href: ../../reference/comparison/
      text: The evidence
      note: Every row against upstream, including where upstream leads.
    related:
      href: ../pick-a-version/
      text: Pick a version, from anywhere
      note: Why upstream's two catalogues disagree by a release.
description: "A longterm kernel and a supported Buildroot under the Turing Pi 2 BMC, with named faults from the stock firmware taken out."
---

{{ feature_screen() }}

<div class="tp-argument" markdown>

## The argument

A longterm kernel matters here because the board is a management computer: it is the thing you reach for when the cluster is broken, so it is the thing that must not need attention itself. The six faults are named on the comparison page with the release that fixed each, including the mDNS responder that killed this board twice in one day.

[The full argument, with every measurement →](../why/fresh-and-fixed.md)

</div>
