---
hide:
  - navigation
  - toc
render_macros: true
---

<div class="tp-hero-band tp-one-screen" markdown>
<span class="tp-eyebrow">About</span>
# Upstream stopped. The board did not.

<p>Turing Pi's firmware has had no release since February 2025, and its two catalogues disagree by a whole version. This fork keeps the board on a supported kernel and fixes what made it hard to run.</p>
</div>

<div class="tp-proof">
<div><b>{{ platform.rows }}</b><span>rows where this fork differs, each one measured</span></div>
<div><b>{{ releases.total }}</b><span>releases across four components</span></div>
<div><b>{{ faults.count }}</b><span>faults still open, each with a ticket</span></div>
</div>

??? note "Why fork it at all"

    Upstream publishes firmware by two routes that do not agree. The mirror the
    stock interface follows stops at **v2.0.5**; the GitHub releases reach
    **v2.1.0**. Same publisher, two catalogues, and on a board running anything
    newer, following the documented update path walks it *backwards*. Neither
    route publishes a checksum.

    That would be survivable if the firmware were finished. It was not. A
    firmware update power-cycled the compute modules. There was no temperature
    sensor anywhere, so the fan ran flat out against nothing. And a bad image
    meant a trip to the rack, because an image was promoted as soon as it
    booted — which proves the kernel started and nothing else.

??? note "What changed"

    {{ comparison_table() | indent(4) }}

    Every row above is the [comparison page](reference/comparison.md)'s own,
    rendered from it: measured on a running board, dated, and including the
    rows where upstream is ahead. What the table does not carry -- the
    consoles, the metrics port, the checksums, the fleet page, the API the
    board describes -- has [a feature page each](features/index.md) with the
    measurement behind it.

??? note "What is still not fixed"

    A fork that lists only its improvements is advertising. These are open, and
    each one has a ticket:

    - **Anything running locally on the BMC is trusted without a credential.**
      Since v2.14.0 it at least leaves an audit line saying so. The fix is a real
      local credential path, not a mitigation.
    - **Nothing shuts the board down if it overheats.** There is no `critical`
      trip. A held fan is taken back by the daemon above the hottest active trip,
      which is a weaker guarantee than a kernel doing it.
    - **Flashing a module on a v2.5 board refuses rather than guessing** when it
      cannot tell which module it is about to write — but the port mapping behind
      that has not been proven against two modules in maskrom at once.

    The [full list](../reference/known-faults/) carries the tickets, and the
    mDNS responder that killed this board twice in one day before v2.13.0 fixed
    it.

??? note "The demo is real data"

    The [live demo](../#demo/fork) is the actual interface, built from the latest
    release, answering from readings captured off a real board.

    - **The readings are real** — temperatures, fan steps, NAND wear, slot
      versions, uptimes. Captured by
      [a script](https://github.com/excavador-turing/BMC-UI/blob/hive/scripts/capture-fixtures.sh)
      that also refuses to publish the board's identity: addresses, MAC and serial
      are replaced with documentation-range values.
    - **The controls do nothing, and say so.** Power, flash, reboot: each answers
      that this is a demo. A control that pretends to work is exactly what this
      project keeps removing from the real interface.
    - **The console replays a recording** and the panel says it is one.
    - **The fleet pane shows two cards from one board's capture.** There is one
      set of readings and both boards display it, because inventing a second
      board's numbers would be the first thing on this site that was not
      measured. The interface is the real one, built from the same release as
      the board's own page.
    - **Stock is stock** — the vendor's own interface, unmodified apart from
      answering from fixtures. It is GPL-2.0, as is this fork, and its copyright
      notice is intact.

<div class="tp-maker">
<div class="tp-maker__who">
<span class="tp-eyebrow">Who makes this</span>
<b>Oleg Tsarev</b>
<span>One person, two boards, and a cluster that has to keep running while its firmware is rewritten under it. Every number on this site was measured on that hardware.</span>
</div>
<div class="tp-maker__links">
<a href="https://www.linkedin.com/in/oleg-tsarev-a0340012/" rel="me noopener">LinkedIn</a>
<a href="https://github.com/excavador" rel="me noopener">GitHub</a>
<a href="https://excavador.xyz/" rel="me noopener">excavador.xyz</a>
<!-- This flips to tsarev.id when SQU-271 lands: the personal site moves
     there and homelab.excavador.xyz to homelab.tsarev.id, with the old names
     redirecting. On 2026-09-20 tsarev.id had a Cloudflare zone and no A
     record at all, so the link stays on excavador.xyz until it answers --
     linking a domain that does not is the turing.excavador.xyz mistake
     again, which is still returning 502 in every old release note. -->
</div>
</div>

<div class="tp-next">
<a href="../features/"><b>What it does →</b><span>{{ features.count }} features, each with the evidence behind it.</span></a>
<a href="../guides/install/"><b>Put it on your board →</b><span>Install it, and what to read first.</span></a>
<a href="../reference/comparison/"><b>The measurements →</b><span>Every claim above, with its date and method.</span></a>
<a href="../roadmap/"><b>What is coming →</b><span>Planned features you can vote on, and where to propose your own.</span></a>
</div>
