---
hide:
  - navigation
  - toc
---

<div class="tp-feature tp-one-screen" markdown>

<div class="tp-feature__say" markdown>
<span class="tp-eyebrow">Feature</span>
# The board describes its own API

<p>Upstream documented its API in prose on a web page. This fork's daemon serves an OpenAPI 3.1 document describing every operation it has, and that document is the source both this site's reference and the interface's own types are generated from.</p>

<a class="tp-why" href="../../why/the-board-describes-itself/">The argument, and the measurements behind it →</a>

<div class="tp-proof">
<div><b>33</b><span>operations, described by the board itself</span></div>
<div><b>3</b><span>things generated from that description</span></div>
<div><b>0</b><span>hand-written pages that can drift</span></div>
</div>

<div class="tp-next">
<a href="../../#demo/fork"><b>See the interface →</b><span>Built from the types this document generates.</span></a>
<a href="../../reference/api/"><b>Every operation →</b><span>The generated reference, one page per group.</span></a>
<a href="../../reference/cli/"><b>The command line →</b><span><code>tpi</code> reaches every endpoint the document describes.</span></a>
<a href="../pick-a-version/"><b>Pick a version →</b><span>The next feature: sources, candidates and checksums.</span></a>
</div>

</div>

<figure class="tp-feature__show" markdown>
![This site's API reference, emitted from the document the board serves. Nothing on this page was written by hand.](../assets/captures/api-reference.png)
<figcaption>This site's API reference, emitted from the document the board serves. Nothing on this page was written by hand.</figcaption>
</figure>

</div>
