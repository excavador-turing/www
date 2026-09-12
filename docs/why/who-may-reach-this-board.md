---
title: Who may reach this board
---

# Who may reach this board

This is the argument behind [Who may reach this board](../features/who-may-reach-this-board.md), with the rule behind each control. The feature page is the short version.

There are exactly two ways into a board running this firmware: the password of
a local account, and a proxy holding a client certificate the board trusts,
telling it which person it has already authenticated. Everything else — the web
interface, the API, the command line — is one of those two wearing different
clothes.

Until this release neither was visible from the interface, and neither could be
changed from it. The password lived in `/etc/shadow` and was changed with
`passwd` on a console. The certificate authority lived in `/etc/bmcd/config.yaml`
and arrived through a script in a different repository. So the page that demands
a password on every login could not change that password, and no page anywhere
could answer *who can get in* without logging in to look.

## Why it is not the ordinary API

The obvious way to add these is as two more operations on the legacy interface,
which is where every other setting lives. That would have written the password
to the audit log.

Every mutating call on that path is recorded with its whole query string — which
is the right behaviour, and the reason the audit line exists at all — into
`bmcd.<date>.log` and, when remote syslog lands, off the board entirely. A
password in a query string is a password in that file, in clear, forever.

So these take a JSON body on their own path, and what is logged is the action
and the actor: *password changed for root by oleg@tsarev.id*. Never the secret.

## The rules, and what each one is for

**The current password is required, always — including from an operator a proxy
vouched for.** A certificate proves the gateway trusts you. It does not prove
you are the person who holds this board's console. Without this rule, anyone
with a live session could lock its owner out of the hardware, and the recovery
is a serial cable. It costs a legitimate operator one field.

**Twelve characters, counted as characters.** Not eight, because the same
account answers the web interface, the API and SSH, and the daemon's rate
limiter slows an online guess while doing nothing at all for anyone who walks
off with a copy of `/etc/shadow`. Counted as characters because a passphrase is
not shorter for being written in an alphabet whose codepoints are wider — there
is a test for exactly that, and it caught an arithmetic mistake in its own
author's first draft.

**A wrong password and an account that does not exist get the same refusal.**
Otherwise this endpoint answers a question nobody should be able to ask it.

**The new password is set with `chpasswd`, reading the pair from standard
input.** Not a shell, and not a command line: the daemon runs as root, and a
password in `argv` is visible in `ps` to anyone on the box and lands in shell
history afterwards.

**A certificate authority is loaded the way the TLS layer will load it, before
it is stored.** A bundle the acceptor cannot read does not fail at the next
login — it stops the daemon from *starting*. That is precisely why this setting
never shipped in the firmware's default configuration: a path pointing at
nothing was a board that would not boot its own interface. Validating first is
what makes it safe to offer at all.

**Removing the trust anchor is refused when you are authenticated by it.** That
request ends its own session, through the proxy it is travelling through, and
leaves the interface you would use to undo it unreachable. Do it from the
board's own interface, with a password, where the consequence is in front of
you.

## What the daemon will not do

It will not rewrite `config.yaml`. That file is the operator's, it carries their
comments, and the daemon reads it with a library that has no writer — so saving
it from an HTTP handler would mean shipping a YAML serialiser and losing every
comment on the first save.

Instead the interface owns two small files of its own, and `config.yaml` still
wins wherever it speaks. Where it pinned a value, the endpoints refuse to touch
it and the card says so rather than offering a control that will be rejected.

One consequence is worth having on its own: the trust anchor is now found by
the file **existing** rather than by a path being configured. A board whose
anchor was removed comes back up, instead of refusing to start because a
setting still points at a file that is gone.

## What this does not do

It does not manage SSH keys — `authorized_keys` on the board's overlay outlives
every firmware flash, and nothing here shows it or takes it back. That is
[the next item on the roadmap](../roadmap.md), and it is filed as one piece with
this: the same page should answer for every way in, not two of the three.
