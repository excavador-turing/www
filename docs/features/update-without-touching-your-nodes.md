---
hide:
  - navigation
  - toc
---

<div class="tp-feature tp-one-screen" markdown>

<div class="tp-feature__say" markdown>
<span class="tp-eyebrow">Feature</span>
# Update the BMC without touching your nodes

<p>Upstream power-cycles all four compute modules to patch the management controller. Here their rails are never touched, measured on a live cluster.</p>

<a class="tp-why" href="../../why/update-without-touching-your-nodes/">The argument, and the measurements behind it →</a>

<div class="tp-proof">
<div><b>0</b><span>modules power-cycled by a BMC update</span></div>
<div><b>0</b><span>cluster nodes lost, measured</span></div>
<div><b>48 s</b><span>for the board to come back</span></div>
</div>

<div class="tp-next">
<a href="../../#demo/fork"><b>See it in the interface →</b><span>The Firmware tab, on a board that took this upgrade.</span></a>
<a href="../../guides/upgrade-from-stock/"><b>Do it on your board →</b><span>The upgrade from stock, step by step, and the way back.</span></a>
<a href="../updates-that-undo-themselves/"><b>If the new image is bad →</b><span>It boots on trial and takes itself back.</span></a>
<a href="../fresh-and-fixed/"><b>What you are updating to →</b><span>A longterm kernel, and the faults taken out.</span></a>
</div>

</div>

<figure class="tp-feature__show" markdown>
![The Firmware tab, where a BMC upgrade starts. The four compute modules keep running throughout.](../assets/cards/card-firmware.png)
<figcaption>The Firmware tab, where a BMC upgrade starts. The four compute modules keep running throughout.</figcaption>
</figure>

</div>
