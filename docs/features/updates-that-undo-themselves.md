---
hide:
  - navigation
  - toc
---

<div class="tp-feature tp-one-screen" markdown>

<div class="tp-feature__say" markdown>
<span class="tp-eyebrow">Feature</span>
# Updates that undo themselves

<p>Upstream promotes a new firmware image the moment it boots. Two images this fork built would have passed that bar while being broken, and one of them cuts all four compute modules off the network. Here a new image is kept only if the board comes back right.</p>

<a class="tp-why" href="../../why/updates-that-undo-themselves/">The argument, and the measurements behind it →</a>

<div class="tp-proof">
<div><b>18</b><span>updates taken on this board</span></div>
<div><b>1</b><span>rolled back by the board itself</span></div>
<div><b>0</b><span>trips to the rack</span></div>
</div>

<div class="tp-next">
<a href="../../#demo/fork"><b>See the Firmware tab →</b><span>The slots, the rollback image, and what the gate last decided.</span></a>
<a href="../see-what-the-board-sees/"><b>See what the board sees →</b><span>The sensor upstream never described, and a fan that explains itself.</span></a>
<a href="../../reference/gate-history/"><b>The gate's record →</b><span>Every decision it has made on this board, read off the board.</span></a>
<a href="../../guides/recover-a-bad-flash/"><b>When it goes wrong anyway →</b><span>The recovery path, and what is genuinely irreversible.</span></a>
</div>

</div>

<figure class="tp-feature__show" markdown>
![The Firmware tab on board B, minutes after its first upgrade: the running slot, and the image it can fall back to in the previous one.](../assets/fork/06-firmware-upgrade.png)
<figcaption>The Firmware tab on board B, minutes after its first upgrade: the running slot, and the image it can fall back to in the previous one.</figcaption>
</figure>

</div>
