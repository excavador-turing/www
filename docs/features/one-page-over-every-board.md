---
hide:
  - navigation
  - toc
---

<div class="tp-hero-band" markdown>
<span class="tp-eyebrow">Feature</span>
# One page over every board

<p>A board's own interface can power off and reflash every compute module in it, which makes it the last thing you want facing the internet. So the boards do not face it. One page in the cluster reaches all of them, and it is the only thing exposed.</p>
</div>

<div class="tp-proof">
<div><b>1</b><span>hostname for the whole estate</span></div>
<div><b>0</b><span>credentials held by the page</span></div>
<div><b>0</b><span>boards on the public network</span></div>
</div>

## What exposing a board would have cost

Per board: a public hostname, a certificate, a route, a policy that verifies
the board's certificate, and a policy that authenticates the human. Board B
doubled every one of them. A third board would have tripled them.

And each of those hostnames would have published something that can cut power
to four computers, protected by whatever that board's own authentication
happened to be.

The fleet page collapses that to one of each. **Adding board B was two lines
of configuration**, which is the whole argument for the shape.

## The pod holds no credential

This is the part worth being precise about, because "a page that reaches
every board" sounds like something that holds the keys to every board.

It holds nothing. The page is a static bundle — HTML, JavaScript and a web
server, with no server code of its own. Two separate things happen in front
of it:

- **The proxy authenticates you** against the estate's identity provider, and
  will not pass a request from anyone outside the group that is allowed in.
- **The proxy holds the client certificate**, not the page, and presents it
  to a board on your behalf. The board trusts that certificate and reads the
  name of the human the proxy already checked.

So a board admits the request because of something the *proxy* proved, and it
records *your* name against it, not the page's. Stealing the bundle gets an
attacker a copy of some HTML.

## The board still works without any of it

The board keeps its whole interface on the management network, with a
password, and nothing here changes that. It has to: this page depends on a
cluster, a tunnel and an identity provider, and the reason the board exists
is to fix the cluster when the cluster is broken.

That is also why client certificates are *requested* and not *required*. A
browser on the management network presents none and reaches the login page as
it always did — the same interface, with
[its own console per module](a-console-to-every-module.md) and
[the sensors it can read](see-what-the-board-sees.md). What shrinks is the
exposure machinery per board, not the firmware.

## A board that is down costs you its card

Every board answers for itself. One that is rebooting, or off the network,
shows as exactly that, with a retry — and the boards either side of it carry
on reporting. That is not a nicety: the times you most want a page over every
board are the times one of them is not answering.

Boards on different firmware are normal here and always will be — which is
what [picking a version per board](pick-a-version.md) makes possible — so
every reading is allowed to be absent, and a board running a daemon outside
the range the page was built against says so in a banner rather than
breaking. The readings themselves come from
[the description the board publishes](the-board-describes-itself.md), so the
page cannot ask for a field the daemon does not have.

<div class="tp-next">
<a href="../update-without-touching-your-nodes/"><b>Updating them →</b><span>The BMC updates without power-cycling your compute modules.</span></a>
<a href="../../reference/known-faults/"><b>What is still not fixed →</b><span>The honest list, with tickets.</span></a>
<a href="../../about/"><b>Why this fork exists →</b><span>What upstream does, and what changed.</span></a>
</div>
