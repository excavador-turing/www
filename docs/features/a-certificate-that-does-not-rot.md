---
title: A certificate that does not rot
render_macros: true
since: v2.23.0
hide:
- navigation
- toc
feature:
  order: 11
  icon: certificate.svg
  summary: Named, renewed before it expires, and it refuses to overwrite one you installed.
  lede: Stock firmware serves a certificate no browser will accept, valid for thirty days, and never replaces
    it. This one is named after the board, renews itself, and will not overwrite yours.
  capture: login.png
  alt: The login page the certificate protects. On stock firmware no browser would accept the certificate
    in front of it.
  caption: The login page the certificate protects. On stock firmware no browser would accept the certificate
    in front of it.
  proofs:
  - n: '825'
    of: days of validity, renewed 30 days before it ends
    source: the daemon's certificate path, with a real handshake per key type
    as_of: '2026-09-12'
  - n: '5'
    of: key types served, each proved by a real handshake
    source: the daemon's certificate path, with a real handshake per key type
    as_of: '2026-09-12'
  - n: '0'
    of: certificates it will overwrite that it did not issue
    source: the daemon's certificate path, with a real handshake per key type
    as_of: '2026-09-12'
  next:
    demo:
      href: ../../#demo/fork
      text: See it in the demo
      note: The interface the certificate protects.
    do:
      href: ../../guides/install/
      text: Do it on your board
      note: Install the firmware that issues it.
    evidence:
      href: ../../reference/known-faults/
      text: The evidence
      note: Including the console's certificate requirement.
    related:
      href: ../who-may-reach-this-board/
      text: Who may reach this board
      note: The other half of the board's access story.
description: "The BMC issues its own HTTPS certificate with a name your browser accepts, renews it before it expires, and never overwrites one you installed."
---

{{ feature_screen() }}

<div class="tp-argument" markdown>

## The argument

An expired self-signed certificate teaches operators to click through warnings, which is the habit that makes every later certificate meaningless. This one carries the board's real names, renews itself 30 days out, and refuses to replace a certificate it did not issue -- so installing your own is safe.

[The full argument, with every measurement →](../why/a-certificate-that-does-not-rot.md)

</div>
