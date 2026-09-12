---
hide:
  - navigation
  - toc
---

<div class="tp-hero-band tp-one-screen" markdown>
<span class="tp-eyebrow">About</span>
# Upstream stopped. The board did not.

<p>Turing Pi's firmware has had no release since February 2025, and its two catalogues disagree by a whole version. This fork keeps the board on a supported kernel and fixes what made it hard to run.</p>
</div>

<div class="tp-proof">
<div><b>13</b><span>rows where this fork differs, each one measured</span></div>
<div><b>66</b><span>releases across four components</span></div>
<div><b>4</b><span>faults still open, each with a ticket</span></div>
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

    <div class="tp-vs">
    <div class="tp-vs__row"><div class="tp-vs__what">Kernel</div><div class="tp-vs__them">6.8, which is not a longterm release</div><div class="tp-vs__us"><b>6.12 LTS</b>, tracking the stable series</div></div>
    <div class="tp-vs__row"><div class="tp-vs__what">Buildroot</div><div class="tp-vs__them">2024.05.1, end of life</div><div class="tp-vs__us"><b>2025.02 LTS</b></div></div>
    <div class="tp-vs__row"><div class="tp-vs__what">A bad image</div><div class="tp-vs__them">promoted the moment it boots; recovering means a trip to the rack</div><div class="tp-vs__us"><b>boots on trial</b> and is taken back automatically if the board does not come back right</div></div>
    <div class="tp-vs__row"><div class="tp-vs__what">Updating the BMC</div><div class="tp-vs__them">power-cycles all four compute modules</div><div class="tp-vs__us"><b>leaves their rails alone</b></div></div>
    <div class="tp-vs__row"><div class="tp-vs__what">Board temperature</div><div class="tp-vs__them">unreadable — the sensor exists but the device tree never described it</div><div class="tp-vs__us"><b>read, with its trip points</b>, so the fan can say why it is where it is</div></div>
    <div class="tp-vs__row"><div class="tp-vs__what">The fan</div><div class="tp-vs__them">a fixed speed somebody once wrote down</div><div class="tp-vs__us"><b>kernel-governed</b>, and overridable behind an explicit switch</div></div>
    <div class="tp-vs__row"><div class="tp-vs__what">Metrics</div><div class="tp-vs__them">none</div><div class="tp-vs__us"><b>a documented catalogue</b>, on a listener that holds no credential and reaches nothing else</div></div>
    <div class="tp-vs__row"><div class="tp-vs__what">Checksums</div><div class="tp-vs__them">none published, on either catalogue</div><div class="tp-vs__us"><b>SHA256SUMS per release</b>, verified on download</div></div>
    <div class="tp-vs__row"><div class="tp-vs__what">Serial consoles</div><div class="tp-vs__them">a header on the board, and your own USB adapter</div><div class="tp-vs__us"><b>four, in the browser</b>, each replaying the scrollback you missed</div></div>
    <div class="tp-vs__row"><div class="tp-vs__what">Firmware sources</div><div class="tp-vs__them">one, hard-coded — and its two catalogues disagree</div><div class="tp-vs__us"><b>a setting</b>: GitHub releases, an HTTP directory, or the SD card</div></div>
    <div class="tp-vs__row"><div class="tp-vs__what">Several boards</div><div class="tp-vs__them">one interface per board, each of which can reflash four computers, each needing its own exposure</div><div class="tp-vs__us"><b>one page over all of them</b>, and it is the only thing exposed — a board is never on the public network</div></div>
    <div class="tp-vs__row"><div class="tp-vs__what">The API</div><div class="tp-vs__them">described in prose on a web page</div><div class="tp-vs__us"><b>OpenAPI 3.1, served by the board</b>, and everything generated from it</div></div>
    <div class="tp-vs__row"><div class="tp-vs__what">Command line</div><div class="tp-vs__them">upstream's <code>tpi</code>, unaware of all of the above</div><div class="tp-vs__us"><b>reaches every endpoint</b> this fork added</div></div>
    </div>

    Every row above is [backed by a measurement](../reference/comparison/), taken
    on a running board and dated, including the rows where upstream is ahead.

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

<div class="tp-next">
<a href="../features/"><b>What it does →</b><span>Fifteen features, each with the evidence behind it.</span></a>
<a href="../guides/install/"><b>Put it on your board →</b><span>Install it, and what to read first.</span></a>
<a href="../reference/comparison/"><b>The measurements →</b><span>Every claim above, with its date and method.</span></a>
<a href="../roadmap/"><b>What is coming →</b><span>Planned features you can vote on, and where to propose your own.</span></a>
</div>
