---
hide:
  - toc
---

# Try it

Two interfaces, side by side, answering from data captured off a real board.
Nothing here talks to hardware: every reading is the board's own, every
control refuses politely and says why.

<div class="tp-demo" markdown>

<div class="tp-pane" markdown>
<h3>Stock firmware</h3>
<p>What a Turing Pi 2 ships with. bmcd 2.3.2, six tabs. Captured 2026-09-10, minutes before that board was upgraded.</p>
<iframe src="stock/" title="Stock Turing Pi 2 interface, demo" loading="lazy"></iframe>
<p><a href="stock/" target="_blank" rel="noopener">Open full size</a></p>
</div>

<div class="tp-pane" markdown>
<h3>This fork</h3>
<p>The same board after the upgrade. Seven tabs; a real rollback image in the previous slot; upstream's own releases listed beside ours.</p>
<iframe src="fork/" title="This fork's interface, demo" loading="lazy"></iframe>
<p><a href="fork/" target="_blank" rel="noopener">Open full size</a></p>
</div>

<div class="tp-pane tp-pane--soon" markdown>
<h3>turing-fleet</h3>
<p>One interface over every board. It is the next thing being built, and this space is honest about that rather than showing a mock-up.</p>
</div>

</div>

## What is and isn't real

- **Readings are real.** Temperatures, fan steps, NAND wear, slot versions,
  uptimes — captured from the board by
  [a script](https://github.com/excavador-turing/BMC-UI/blob/hive/scripts/capture-fixtures.sh)
  that also refuses to publish the board's identity. Addresses, MAC and serial
  are replaced with documentation-range values.
- **Controls do nothing, and say so.** Power, flash, reboot: each answers with
  a message that this is a demo. A control that pretends to work is what this
  project keeps removing from the real interface.
- **The console replays.** It shows a module's recorded scrollback rather than
  a fake live stream, and the panel says it is a recording.
- **Stock is stock.** The first pane is the vendor's own interface, unmodified
  apart from answering from fixtures — it is GPL-2.0, as is this fork, and its
  copyright notice is intact.

The fork pane is built from the tag the firmware pins, by `just refresh-demo`,
and names its version on the About tab. The stock pane was captured once and
does not change.
