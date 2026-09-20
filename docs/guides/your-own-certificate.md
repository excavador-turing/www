---
title: Your own certificate
render_macros: true
---

# Your own certificate

The board serves HTTPS from the moment it boots, with a certificate it issued
itself. Your browser does not trust it, because nothing told your browser to.
This page is how to get from there to a green padlock — and why the obvious
answer, Let's Encrypt, is the wrong tool for a board like this one.

## What the board serves by default

When nobody has installed a certificate, the board issues its own:

| | |
|---|---|
| key | EC P-384 |
| names | the board's hostname, its `.local` name, and every address it holds |
| valid for | 825 days |
| renewed | 30 days before it expires |
| replaced | never, if you installed the certificate yourself |

825 days is not a rule about public certificates. It is the longest
**any** certificate may be valid before Apple's platforms reject it, public or
private, and it has been since 2019. Publicly trusted certificates are capped
far lower — 398 days today, and heading to 47 — but that cap does not apply to
a certificate your own authority issued.

Accepting the browser's warning works for every tab except one. **The serial
console will still refuse to connect**, because a click-through exception is
not applied to WebSocket handshakes, and the console is a WebSocket. That is
[a known fault](../reference/known-faults.md), and everything below fixes it
as a side effect.

## Trust your own authority, once

If you already run a certificate authority — [step-ca][step], your router's,
your own `openssl` one — this is the shortest path and it needs nothing from
the board:

1. Import your CA's **root certificate** into your browser or operating
   system trust store. Once, per machine.
2. Every certificate that CA issues is now trusted there, for any name at
   all: `bmc.lan`, `bmc.home.arpa`, anything. No warning, and the console
   connects.

Nobody outside is asked to verify anything, because there is nobody outside:
your trust store decides, and you are the authority. This is what the people
running this fork's own boards do — the estate has an internal CA, the boards
carry certificates from it, and the gateway in front of them is told to trust
exactly that CA and nothing else.

It is worth doing even if you never install a certificate on the board,
because it is also what makes the fleet's connection to each board verifiable.

## Put your certificate on the board

Trusting your CA is only half of it: the board still has to serve a
certificate that CA issued. Generate one on your own machine, where the key
already is —

```console
$ step ca certificate bmc-1.lan bmc.crt bmc.key
```

— and install it on the board.

!!! warning "Today this is a shell operation"

    There is no endpoint for it yet: copy the pair over SSH and restart the
    daemon. An install control on the Settings tab, in `tpi`, and in the
    fleet is [on the roadmap](../roadmap.md) and is the thing to upvote if you
    want it.

Whatever you install is what the board serves. Every key type is covered by a
test that performs a real handshake against the real acceptor, over both
protocol versions — RSA, EC P-256, P-384 and P-521, and Ed25519 — so this is
not a promise, it is a thing that is checked on every release. And the
self-signed generator will not touch a certificate it did not issue, so
installing yours is safe from it.

## Let it renew itself

A private CA can issue short-lived certificates, and most people who run one
do: [step-ca][step] defaults to **24 hours**. Renewing that by hand is not a
plan.

ACME is a protocol, not a company. A private CA speaks it on your own network,
answers the challenge over your own LAN, and issues from your own root. An
ACME client on the board, pointed at your directory URL, would renew without
anyone watching. That is [on the roadmap](../roadmap.md) too.

Until it exists, the working answer is the one a reader of this project
already runs: `acme.sh` in a cron job on the board itself, pointed at a local
directory. The board has room for it.

## Why not Let's Encrypt

Let's Encrypt **can** issue a certificate for a device that only exists on
your LAN. You need a public domain you own, and the DNS-01 challenge: a client
writes a `TXT` record under `_acme-challenge.your-name.example.com`, Let's
Encrypt reads it from public DNS, and issues. The name is allowed to point at
a private address; Let's Encrypt never connects to the board.

So it is possible, and for a home service it is often the right thing. For a
board management controller it is not, for three reasons:

**The board would hold a credential that can edit your DNS zone.** On a device
that can reflash four computers, whose local processes are
[still trusted without a credential](../reference/known-faults.md). A DNS
credential is not a small secret; it is the one that can be used to obtain
certificates for everything else you own.

**Your board's hostname becomes public.** Every publicly trusted certificate
is published in Certificate Transparency logs, which anyone can search. A
management controller is not a thing to announce.

**Hiding the name means a wildcard**, and then the wildcard's private key — the
one that covers every service under your domain — is sitting on the board.

The 47-day lifetimes arriving for public certificates apply only to this
route. They are a good reason to automate; they are not a reason to put a
public certificate on a BMC.

## What this fork decided against

The board making its own key and emitting a certificate signing request, so
the private key never leaves it, was designed and then **dropped**. The
reasoning is worth having, because it sounds like the obvious next step:

- A CA-signed certificate matters in exactly one place — a browser talking to
  a board directly. Everywhere else, the gateway in front of the boards is
  already told which CA to trust, so it verifies each board without any
  public trust being involved.
- For that one place, trusting your CA once in the browser is the whole fix,
  and costs nothing to build.
- What it would have cost is a signing service with standing access to every
  board, to save an operator a manual step they take about once a year.

Installing your own certificate, and renewing it over ACME against your own
CA, are the two things that were kept.

[step]: https://smallstep.com/docs/step-ca/

<div class="tp-next">
<a href="../../features/a-certificate-that-does-not-rot/"><b>What the board issues itself →</b><span>The certificate that does not rot, with its measurements.</span></a>
<a href="../../features/who-may-reach-this-board/"><b>Who may reach this board →</b><span>The password, and the proxy a certificate can name.</span></a>
<a href="../../reference/known-faults/"><b>Why the console refuses →</b><span>The fault this page fixes as a side effect.</span></a>
<a href="../../roadmap/"><b>Vote on the two that are missing →</b><span>Installing your own, and renewing it over ACME.</span></a>
</div>
