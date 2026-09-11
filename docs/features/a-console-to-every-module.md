---
hide:
  - navigation
  - toc
---

<div class="tp-feature tp-one-screen" markdown>

<div class="tp-feature__say" markdown>
<span class="tp-eyebrow">Feature</span>
# A console to every module

<p>Reaching a compute module's serial console used to mean a USB adapter and three jumper wires on the board's header. The BMC is already wired to all four. This fork puts them in the browser, with scrollback.</p>

<a class="tp-why" href="../../why/a-console-to-every-module/">The argument, and the measurements behind it →</a>

<div class="tp-proof">
<div><b>4</b><span>consoles, one per module</span></div>
<div><b>16 KiB</b><span>of scrollback replayed when you open one</span></div>
<div><b>0</b><span>USB adapters and jumper wires</span></div>
</div>

<div class="tp-next">
<a href="../../#demo/fork"><b>Open a console now →</b><span>The demo replays a real recording into a real terminal.</span></a>
<a href="../the-board-describes-itself/"><b>The board describes its own API →</b><span>OpenAPI 3.1, and everything generated from it.</span></a>
<a href="../../demo/fork/"><b>Open a console now →</b><span>The live demo replays a real recording.</span></a>
<a href="../../reference/cli/"><b>From a shell instead →</b><span>`tpi` reaches the same consoles.</span></a>
</div>

</div>

<figure class="tp-feature__show" markdown>
![A module's console in the browser, opened on the scrollback the daemon kept before the tab was.](../assets/captures/console.png)
<figcaption>A module's console in the browser, opened on the scrollback the daemon kept before the tab was.</figcaption>
</figure>

</div>
