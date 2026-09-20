---
title: The board describes its own API
render_macros: true
hide:
- navigation
- toc
feature:
  order: 10
  icon: describe.svg
  summary: OpenAPI 3.1, served by the board, and this site's reference generated from it.
  lede: Upstream documented its API in prose on a web page. This fork's daemon serves an OpenAPI 3.1 document
    describing every operation it has, and everything else is generated from that.
  capture: api.png
  alt: This site's API reference, emitted from the document the board serves. Nothing on this page was
    written by hand.
  caption: This site's API reference, emitted from the document the board serves. Nothing on this page
    was written by hand.
  proofs:
  - n: '33'
    of: operations, described by the board itself
    source: the openapi.json this site commits, from a bmcd release
    as_of: '2026-09-12'
  - n: '3'
    of: things generated from that description
    source: the openapi.json this site commits, from a bmcd release
    as_of: '2026-09-12'
  - n: '0'
    of: hand-written pages that can drift
    source: the openapi.json this site commits, from a bmcd release
    as_of: '2026-09-12'
  next:
    demo:
      href: ../../#demo/fork
      text: See it in the demo
      note: The interface built from the types this document generates.
    do:
      href: ../../reference/cli/
      text: Do it on your board
      note: tpi reaches every operation the document describes.
    evidence:
      href: ../../reference/api/
      text: The evidence
      note: Every operation, on pages emitted from the document.
    related:
      href: ../see-what-the-board-sees/
      text: See what the board sees
      note: The readings those operations return.
---

{{ feature_screen() }}

<div class="tp-argument" markdown>

## The argument

Three things are generated from one document: this site's reference, the interface's own types, and the command line's knowledge of what exists. A hand-written API page drifts from the API within about two releases; a generated one cannot.

[The full argument, with every measurement →](../why/the-board-describes-itself.md)

</div>
