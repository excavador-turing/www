---
title: One page over every board
---

# One page over every board

This is the argument behind [One page over every board](../features/one-page-over-every-board.md), with the measurements that back it. The feature page is the short version.

## Everything the board's own interface can do

Not a status page. Power a module on or off, reset it, rename it, route the
USB bus, open its serial console, write an OS image to it, upgrade the board's
firmware, set its time servers, hold its fan, back up and restore its
configuration — for any board, without leaving this page and without that
board's password.

These are not reimplementations. They are **the same components** the board
serves itself, rendered against that board's API. A control that exists once
cannot drift into a worse second copy, and a fix to one is a fix to both.

The overview is still the first thing you see, because "is anything wrong
across eight modules" is the question you usually arrive with. Picking a board
gives you that board's whole interface.

Two boards can be worked on at once. Each gets its own cache, its own request
path and its own progress state, so a firmware upload to one does not show up
as the other one's progress bar — which is what happens when that state is
shared, and it is not obvious until the day you need both.

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
[its own console per module](../features/a-console-to-every-module.md) and
[the sensors it can read](../features/see-what-the-board-sees.md). What shrinks is the
exposure machinery per board, not the firmware.

## A board that is down costs you its card

Every board answers for itself. One that is rebooting, or off the network,
shows as exactly that, with a retry — and the boards either side of it carry
on reporting. That is not a nicety: the times you most want a page over every
board are the times one of them is not answering.

Boards on different firmware are normal here and always will be — which is
what [picking a version per board](../features/pick-a-version.md) makes possible — so
every reading is allowed to be absent, and a board running a daemon outside
the range the page was built against says so in a banner rather than
breaking. The readings themselves come from
[the description the board publishes](../features/the-board-describes-itself.md), so the
page cannot ask for a field the daemon does not have.
