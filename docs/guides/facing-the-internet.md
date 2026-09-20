---
title: Should the board face the internet?
render_macros: true
---

# Should the board face the internet?

No. Not this board, and not the one upstream ships either.

That answer is short enough to sound like caution. It is not — it comes from
what the device actually is, and the firmware is built around it. This page
is the reasoning, and what to do instead.

## What the board is

A board management controller is not a server with a web page on it. It can
power four computers off, route their USB to itself, and **write a new
operating system onto any of them**. It sits below everything those computers
run: below their firewall, below their operating system, below whatever
you trust to protect them.

Reaching it is reaching all of them.

## Why a password is not enough for that

The board authenticates one local account against `/etc/shadow`. That is the
right mechanism for a device on a management network and the wrong one for a
device on the public internet, for two reasons that have nothing to do with
how good the password is:

**Every account that passes is a full administrator.** There is no
authorization layer under the login — no read-only operator, no "may look, may
not flash". A credential is all-or-nothing, and the *all* includes reflashing
your cluster.

**And a board that ships as `root` / `turing`** — which upstream's does, and
this fork's still does today — will be found by the first scan that reaches it.
Forcing that password to change is
[on the roadmap](../roadmap.md) and is not a substitute for the paragraph
above.

## Why the login cannot be delegated

The obvious fix is single sign-on: put the board behind your identity
provider, and let it check. This fork deliberately does not do that, and the
reason is worth stating because it is not about effort.

Measured from a board on this estate, the path to the identity provider is:
board → internet → Cloudflare → a tunnel → the cluster → the provider. Every
one of those has to be working.

**The board is the thing you reach for when they are not.** It is what
power-cycles a node that has wedged so badly it took the cluster with it. A
login that depends on the cluster, in order to fix the cluster, is a circular
dependency that fails exactly when the tool is needed — and the failure is
that you drive to the rack.

So the board keeps a local password, and that password stays break-glass: the
credential you use on the management network when something is already wrong.

## What to do instead

Expose **one page, inside your cluster, that speaks to every board** — and
leave the boards themselves on the management network where they belong.

That is what [the fleet](../features/one-page-over-every-board.md) is. It runs
as a pod, it carries every control a board's own interface has, and the
important part is what it does *not* carry:

| | the board | the fleet |
|---|---|---|
| who authenticates you | the board, with a password | your identity provider, at the gateway |
| what it holds | a local account | **no credential of its own** |
| what is exposed | nothing, by design | one hostname |
| when the cluster is down | still works | does not, and that is fine — the board still works |

The gateway in front of it authenticates the operator, then presents a client
certificate the board trusts. The board's question is not *do I believe this
token* but *did this connection present a certificate my authority signed* —
answerable with the internet down, no keys to rotate, no clock to keep.

And if the fleet is unreachable because the cluster is broken, you fall back
to the board's own interface on the management network, with the password.
Which is the case it was kept for.

## If you are going to do it anyway

You own the hardware. If you expose a board despite the above, at least:

- put it behind something that authenticates **before** the request reaches
  the board, rather than forwarding a port to it;
- change the password first;
- give it [a certificate your browser trusts](your-own-certificate.md), so you
  are not training yourself to click through warnings on the one device where
  that matters most;
- and know that [`{{ faults.count }}` faults are open](../reference/known-faults.md)
  on this firmware, one of which is that anything running locally on the board
  is trusted without a credential at all.

<div class="tp-next">
<a href="../../features/one-page-over-every-board/"><b>One page over every board →</b><span>The exposure surface, and what it holds.</span></a>
<a href="../../features/who-may-reach-this-board/"><b>Who may reach this board →</b><span>The two ways in: a password, and a proxy a certificate names.</span></a>
<a href="../your-own-certificate/"><b>Your own certificate →</b><span>A green padlock, and a console that connects.</span></a>
<a href="../../reference/known-faults/"><b>What is still not fixed →</b><span>Including the local-trust fault named above.</span></a>
</div>
