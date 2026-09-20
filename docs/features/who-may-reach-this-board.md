---
title: Who may reach this board
render_macros: true
hide:
- navigation
- toc
feature:
  order: 8
  icon: access.svg
  summary: The password and the trusted proxy, both readable and both changeable from the page that asks
    for one.
  lede: 'There are two ways into a board running this firmware: a local password, and a proxy holding
    a certificate the board trusts. Neither used to be visible from the interface, nor changeable there.'
  capture: access.png
  alt: 'The access card on Settings: how you got in, the password for the local account, and the certificate
    authority a proxy must hold to name you.'
  caption: 'The access card on Settings: how you got in, the password for the local account, and the certificate
    authority a proxy must hold.'
  proofs:
  - n: '2'
    of: ways in, both now visible
    source: the daemon as shipped in bmcd 2.36.3
    as_of: '2026-09-12'
  - n: '12'
    of: characters minimum, counted as characters
    source: the daemon as shipped in bmcd 2.36.3
    as_of: '2026-09-12'
  - n: '0'
    of: passwords written to the audit log
    source: the daemon as shipped in bmcd 2.36.3
    as_of: '2026-09-12'
  next:
    demo:
      href: ../../#demo/fork
      text: See it in the demo
      note: The access card on Settings, from captured data.
    do:
      href: ../../guides/install/
      text: Do it on your board
      note: Install the firmware that carries these controls.
    evidence:
      href: ../../reference/known-faults/
      text: The evidence
      note: Including that anything local is still trusted without a credential.
    related:
      href: ../a-certificate-that-does-not-rot/
      text: A certificate that does not rot
      note: The certificate the board serves on that connection.
---

{{ feature_screen() }}

<div class="tp-argument" markdown>

## The argument

These take a JSON body on their own path rather than joining the legacy interface, because every mutating call there is recorded with its whole query string -- which would put a password in a log file, in clear, for ever. What is logged is the action and the actor, never the secret. The current password is required even from an operator a proxy vouched for.

[The full argument, with every measurement →](../why/who-may-reach-this-board.md)

</div>
