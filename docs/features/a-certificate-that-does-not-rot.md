---
hide:
  - navigation
  - toc
---

<div class="tp-feature tp-one-screen" markdown>

<div class="tp-feature__say" markdown>
<span class="tp-eyebrow">Feature</span>
# A certificate that does not rot

<p>The board serves its login page over HTTPS, and on stock firmware that certificate is unusable by any browser made since 2017, expires in thirty days, and is never replaced. This fork fixes all three.</p>

<a class="tp-why" href="../../why/a-certificate-that-does-not-rot/">The argument, and the measurements behind it →</a>

<div class="tp-proof">
<div><b>825 days</b><span>validity, renewed 30 days before it ends</span></div>
<div><b>5</b><span>key types served, each proved by a real handshake</span></div>
<div><b>0</b><span>certificates this firmware will overwrite that it did not issue</span></div>
</div>

<div class="tp-next">
<a href="../../#demo/fork"><b>See the interface it protects →</b><span>The login page, and everything behind it.</span></a>
<a href="../one-page-over-every-board/"><b>One page over every board →</b><span>What the client certificate on that connection buys.</span></a>
<a href="../../reference/metrics/"><b>Every metric the board exposes →</b><span>Including the expiry above.</span></a>
<a href="../../reference/known-faults/"><b>What is still not fixed →</b><span>The honest list, with tickets.</span></a>
</div>

</div>

<figure class="tp-feature__show" markdown>
![The login page the certificate protects. On stock firmware no browser would accept the certificate in front of it.](../assets/captures/login.png)
<figcaption>The login page the certificate protects. On stock firmware no browser would accept the certificate in front of it.</figcaption>
</figure>

</div>
