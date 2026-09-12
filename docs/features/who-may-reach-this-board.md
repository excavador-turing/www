---
hide:
  - navigation
  - toc
---

<div class="tp-feature tp-one-screen" markdown>

<div class="tp-feature__say" markdown>
<span class="tp-eyebrow">Feature</span>
# Who may reach this board

<p>On stock firmware the answer lives on the filesystem, and the only way to read or change it is a shell. The login page cannot change the password it demands. This fork puts both halves on Settings.</p>

<a class="tp-why" href="../../why/who-may-reach-this-board/">The argument, and the rules behind each control →</a>

<div class="tp-proof">
<div><b>2</b><span>ways in, both now visible: a password, and a trusted proxy</span></div>
<div><b>12</b><span>characters minimum, counted as characters and not as bytes</span></div>
<div><b>0</b><span>passwords written to the audit log — the reason this is not the ordinary API</span></div>
</div>

<div class="tp-next">
<a href="../a-certificate-that-does-not-rot/"><b>The certificate it serves →</b><span>The other half of the board's TLS story.</span></a>
<a href="../one-page-over-every-board/"><b>One page over every board →</b><span>What a trusted proxy buys: an operator who never types a board password.</span></a>
<a href="../../#demo/fork"><b>See it working →</b><span>The card, in the live demo, answering from captured data.</span></a>
<a href="../../reference/known-faults/"><b>What is still not fixed →</b><span>The honest list, with tickets.</span></a>
</div>

</div>

<figure class="tp-feature__show" markdown>
![The access card on Settings: how you got in, the password for the local account, and the certificate authority a proxy must hold to name you.](../assets/captures/access.png)
<figcaption>It says how <em>you</em> arrived before offering either control: an operator who came through a gateway is not holding the board's password.</figcaption>
</figure>

</div>
