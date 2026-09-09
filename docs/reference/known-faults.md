# What is and isn't fixed

A fork that lists only what it improved is advertising. This page is the other
half: what is wrong with this firmware today, measured, with the ticket that
tracks it. Nothing here is theoretical — each line is something observed on a
running board.

## Open

### The TLS certificate is an expired fossil

`/etc/ssl/certs/bmcd_cert.pem` on the reference board was issued **June 2025**
and **expired July 2025**. It is RSA, has no subject-alternative name, and
lives on the overlay, so it survives firmware upgrades — including every one
this fork has shipped.

A `bmcd` that finds no certificate mints one. A `bmcd` that finds an expired
one uses it. Every browser warning you see on this interface is that file, and
clicking through it is not a workaround for anything.

*Tracked as SQU-115. The replacement is issued by a real CA and renewed, not
minted.*

### Anything local is trusted

`/api/bmc` skips authentication entirely for requests from `127.0.0.1`. That
is how the on-board `tpi` works without credentials and how the promotion gate
obtains its metrics token. It also means **any process on the board can power
off a node or stage firmware**, with no credential and no audit line.

`/metrics` has no such exception and demands its token even on loopback, which
is the behaviour the rest of the API should have.

*Tracked as SQU-165 (a Unix socket authenticated by peer credentials, so the
bypass can be removed rather than merely narrowed) and SQU-113.*

### Flashing a module may not target the module you chose

On **v2.5** boards, `tpi flash` and the interface's flash page write to
whichever module is in maskrom *first* and report success — whatever was
selected. With one module in maskrom this is correct; with two it is a
coin toss, and the cost is a module that no longer boots.

The interface shows a red warning on v2.5 boards. Put only the target module
into maskrom before installing.

*Tracked as SQU-105.*

### mDNS eats the board

**Affects v2.9.0 through v2.12.0.** The `mdnsd` that advertises
`turingpi.local` leaks about **0.85 MB a minute** and does not stop. On a board
with 116 MB of RAM that is fatal in roughly ninety minutes: userspace stops
answering, the kernel keeps replying to ping for a while, and only cutting the
power brings it back. It happened twice on 2026-09-09.

The rate follows mDNS traffic rather than time, so a quiet network hides it
entirely and a busy one kills the board before lunch. That is why it reads as
intermittent.

**Restarting the daemon is a complete, instant remedy** and costs nothing —
mDNS keeps working across it:

```console
$ ssh root@<bmc> /etc/init.d/S50mdnsd restart
```

Measured on a board that had been up 36 minutes: available memory went from
54.4 MB back to 88.5 MB, and `mdnsd` from 36.0 MB back to 1.9 MB.

We introduced this. `turingpi.local` stopped resolving when avahi was dropped
for rootfs headroom, and `mdnsd` was chosen as the small replacement. We
compared the two on size alone. On a board with no swap and no watchdog, how a
long-running daemon behaves over hours deserved a look as well, and did not get
one.

!!! note "How it was found, and why it took two outages"
    The daemon was the obvious suspect and the wrong one. Five reproductions
    drove `bmcd` on a workstation — 183,702 requests across every endpoint,
    278,000 metrics scrapes, forced catalogue refreshes — and every one came
    back clean, because `bmcd` was innocent.

    What settled it was
    [`bmcd_process_resident_bytes`](../guides/monitor-it.md), added the night
    before for exactly this. Board memory fell 0.88 MB a minute while the
    daemon's own resident set sat at 18.7 MB and never moved. One flat line
    ended the search, and the process table then took about a minute to
    read.

*Tracked as SQU-175, with the outage itself as SQU-172.*

### There is no watchdog

Everything above has the same last resort: a person walking to the rack. The
SoC has a hardware watchdog and this firmware does not arm it, so a BMC whose
userspace dies stays dead until someone cuts its power.

*Tracked as SQU-106, and it is the most valuable unbuilt thing on the list.*

## Fixed, and worth knowing about

### `turingpi.local` stopped resolving

Dropping avahi for rootfs headroom also removed the board's mDNS
advertisement, and nothing replaced it. Since `tpi`'s default host is literally
`turingpi.local`, **every `tpi` command without `--host` failed** from v2.3.0
until v2.8.1 — including the one upstream's documentation tells you to run
first.

Fixed in **v2.8.1** with `mdnsd`, which does the same job without the D-Bus,
expat and libdaemon that made avahi expensive. `tpi` 1.1.1 also says so
plainly when the name does not resolve, which matters on the older firmware
where it never will.

### The command line did not work at all

Every command this fork added to `tpi` was broken from 1.1.0 to 1.2.0, and none
had ever been run against a board. The response unwrapper returned the API's
wrapper array instead of the result inside it; serde will build a struct from a
sequence by taking the elements as its fields in order, so the first thing every
command does — read `about` to check the daemon's version — failed with
*invalid type: map, expected a string*.

Behind that were four more: `firmware check` printed an empty version, `thermal`
printed raw JSON, every refusal printed as escaped JSON, and `firmware install`
had **never worked in any release** because its argument collided with the
`--version` flag.

All fixed by 1.2.2, each verified against a board. The examples on the
[command line](cli.md) page are now real output.

### The firmware page froze

Two causes. The daemon polled its four firmware sources one after another and
held its cache lock for the whole 16 seconds, so a "check now" froze every
other reader. And the interface's *Check now* button **never sent the refresh
parameter** — it replayed the same request and got the daemon's half-hour
cache back, which is to say the one control whose purpose was to bypass that
cache was the only one that did not.

Fixed in bmcd 2.11.0 and BMC-UI 3.8.0. Measured after: 1 ms main-thread
response while a check runs, with the list readable and the page navigable.

### One failed request blanked the whole interface

The header's version panel is a suspense query mounted on every route, wrapped
in a bare `<Suspense>`. Suspense handles a promise that is *pending*; a
rejected one is thrown during render and passes straight through — so a single
failed `about` request unwound past the header, past the route and past the
root, none of which had a boundary.

Fixed in BMC-UI 3.8.0.
