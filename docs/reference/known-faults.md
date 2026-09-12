# What is and isn't fixed

A fork that lists only what it improved is advertising. This page is the other
half: what is wrong with this firmware today, measured, with the ticket that
tracks it. Nothing here is theoretical — each line is something observed on a
running board.

## Open

### The serial console needs a certificate your browser trusts

Every other tab works over a self-signed or internal-CA certificate once you
accept the warning. **The console does not.** A browser will not open a
WebSocket to a certificate it does not trust, and the exception you granted by
clicking through on the page does not extend to that connection — so the
console reports `not connected, close code 1006` while the rest of the
interface is fine.

Measured on 2026-09-12. What the browser reports:

```
webSocketCreated     wss://<board>/api/bmc/serial/ws?node=0
webSocketFrameError  net::ERR_SSL_PROTOCOL_ERROR
```

The board is not at fault. The same endpoint, from a client with verification
off and a valid token, answers `handshake: OK`.

Two ways round it, both of which work today:

* **Trust the authority that issued the board's certificate** in the browser's
  own store. A click-through exception is not enough; the certificate has to
  be trusted.
* **Reach the board through a proxy that terminates TLS on a certificate your
  browser already trusts.** That is what [one page over every
  board](../features/one-page-over-every-board.md) does.

*The interface says this now, in the panel under the console. It cannot detect
the case — a browser reports no reason for a failed handshake — so it names
the cause that is usually right rather than guessing.*

### Anything local is trusted

`/api/bmc` skips authentication entirely for requests from `127.0.0.1`. That
is how the on-board `tpi` works without credentials. It also means **any
process on the board can power off a node or stage firmware**, with no
credential and no audit line.

Since **v2.15.0** the on-board `tpi` is the *only* thing that relies on it.
The promotion gate used to need the bypass as well, to mint itself a metrics
token; `/metrics` moved to its own listener and takes no credential, so the
gate now makes one plain request and needs nothing.

Since **v2.14.0** the bypass at least leaves a trace: every mutating call
writes an audit line, and one that skipped authentication says so in plain
words rather than being folded in with a real credential.

```
Sep  9 15:12:41 hive-bmc authpriv.info bmcd[812]: power by loopback (unauthenticated) from 127.0.0.1: ok
```

That is a smaller thing than removing the bypass, and it is not a substitute
for it. It means an unauthenticated power-off can be found afterwards, not
that it can be prevented.

*Tracked as SQU-165 (a Unix socket authenticated by peer credentials, so the
bypass can be removed rather than merely narrowed) and SQU-113.*

### Flashing a module may not target the module you chose

On **v2.5** boards, `tpi flash` and the interface's flash page write to
whichever module is in maskrom *first* and report success — whatever was
selected. With one module in maskrom this is correct; with two it is a
coin toss, and the cost is a module that no longer boots.

**v2.14.0 changes the mechanism and has not yet been proven on hardware.** The
daemon now accepts a module only on the hub port the board's own device tree
says that node is wired to, and refuses anything on another port instead of
writing to it:

```
node 3 requested on 1-1.3; found Rockusb on 1-1.1 instead
```

What is proven is that the device tree says node N is port N — it is read at
runtime, and a unit test builds a tree wired the other way round and requires
the other answer. What is **not** proven is that the device tree agrees with
the physical wiring, which needs two modules in maskrom at once to test. Until
that is done, the interface keeps its red warning: put only the target module
into maskrom before installing.

*Tracked as SQU-105.*

### Nothing shuts the board down if it overheats

The thermal zone declares four `active` trips — 20, 45, 60 and 70 °C, each
driving the fan a step harder — and `hot` at 95 °C. There is no `critical`
trip, and `hot` notifies without acting. So if the fan fails, or is held low,
the board climbs with nothing to stop it.

This is not a regression and not something this fork introduced; it is what the
device tree has always declared. It is written down here because the fan can
now be **held** at a step from the interface, and a person doing that should
know what is and is not underneath them. The daemon takes a held fan back above
70 °C for exactly this reason — but that is a daemon that has to be running,
which is a weaker guarantee than a kernel trip.

*No ticket yet. A `critical` trip is a device-tree change and wants a decision
about what it should do at what temperature, not a number picked here.*

### There is no watchdog

Everything above has the same last resort: a person walking to the rack. The
SoC has a hardware watchdog and this firmware does not arm it, so a BMC whose
userspace dies stays dead until someone cuts its power.

*Tracked as SQU-106, and it is the most valuable unbuilt thing on the list.*

## Fixed, and worth knowing about

### Reconnect wrote a second copy of the scrollback

**Affected every release up to BMC-UI 3.27.0; fixed in 3.28.0 (firmware
v2.31.0).** Pressing **Reconnect** kept the terminal, as it is meant to, and
then replayed the daemon's whole 16 KiB ring buffer underneath what was
already on screen — the same lines with the same kernel timestamps, twice:

```
[64064.315286] eth0: renamed from tmpe5b7c
[65264.283498] eth0: renamed from tmp5cff0
[61664.597477] eth0: renamed from tmpc8e55    <- the ring again, from the top
[62864.338706] eth0: renamed from tmp83239
```

It affected a board's own interface and the fleet alike, because one component
serves both.

The replay is there because the daemon forwards only what arrives *after* a
subscriber joins; without it, a console opened on a module that has been up
for hours shows nothing at all. It simply never asked whether the terminal
already held that output.

Clearing the terminal first would have fixed the duplication and cost the
thing the scrollback is for. The daemon keeps only the last 16 KiB and one
module boot is about 82 KB, so the terminal is the only place a full boot
survives. Instead the replay now works out where what it has already shown
ends inside the buffer it has just been handed, and writes only what follows:
a reconnect with nothing new writes nothing, one after a gap writes exactly
the gap, and when the module wrote more than the ring holds there is no
overlap and the whole buffer is written, because there is a hole either way.

**Redraw is unchanged** and still clears first. It answers a different
question: *show me what the module's screen says now*.

### A console that failed at random, and a board that never said why

**Affected every release from bmcd 2.30.0 to 2.36.2; fixed in 2.36.3
(firmware v2.30.0).** A serial console or an API call arriving through a proxy
would occasionally fail outright, on any board, with nothing in the daemon's
log and the board perfectly healthy either side of it. Reconnecting usually
worked, which is what made it look like a network fault.

OpenSSL will not resume a TLS session on a server that asks for client
certificates unless the context carries a session id context — and the refusal
is not a quiet cache miss. It is `internal_error`, fatal, sent before a byte
of HTTP is exchanged:

```
error:0A000115:SSL routines:ssl_get_prev_session:session id context uninitialized
```

That error is raised on the **server**, which never logged it. The only trace
anywhere was an alert the client could not explain.

It looked random because of who resumes. A proxy keeps one session per board
and offers it on the next connection it opens, so connections taken from the
pool were always fine and new ones were a coin flip. Measured on a gateway in
front of two boards: **8 of 28** new connections failed to one, **19 of 45**
to the other. Reproduced deterministically from the same host — 30 fresh
connections all succeeded, 30 offering back a saved session all failed.

Nothing about it was specific to a gateway. Any client that resumes a session
hit the same wall, and the fault arrived the day client certificates were
first offered, so it was present and invisible for six releases.

The acceptor now sets a session id context, derived from the client CA so that
replacing a board's trust anchor will not resume a session authenticated under
the old one.

*Tracked as SQU-212.*

### A module in flash mode looked exactly like dead hardware

**Fixed in bmcd 2.36.3 (firmware v2.30.0), by making it visible rather than by
changing the behaviour.** Flashing a module leaves the board's persisted USB
configuration at `Flashing(nodeN, …)`, and the daemon re-applies it on every
start — which holds that module's USB-boot pin high and stops it booting from
its own eMMC.

The module carries on running, because it is already booted. The failure
arrives at its **next** reboot, which can be weeks later, and by then nothing
connects the two. What you see is a module that is silent on the serial
console — not a byte, not even a bootloader banner, because the loader does
not use the console — unreachable on the network, with the board still
reporting its rail on. `tpi usb status` did not help: it prints the same route
for a normal configuration and for this one.

Twenty minutes went into exactly that on 2026-09-12, on a board where the
answer was sitting in the daemon's own database unexported.

`/metrics` now carries `bmcd_node_usb_boot_armed`, one sample per module.
Alert on it lasting more than a few minutes and the page reaches whoever armed
it while they still remember doing so; the
[metrics reference](metrics.md#compute-modules) has the rule. Finish a flash
with `tpi usb device -n N` and it never arms at all.

*Tracked as SQU-213.*

### The board could stop checking for firmware, for ever

**Affected every release up to bmcd 2.34.0; fixed in 2.35.0.** The Firmware
page said *checking the sources now* and never stopped, with **Check now**
disabled beside it, and the board could not have found a new release if one
had appeared. Only restarting the daemon cleared it.

Opening the Firmware tab on a board whose cached listing had aged out was
enough to trigger it. bmc-2 sat in that state for **three and a half hours**
on 2026-09-11 — `refreshing: true`, the timestamp frozen, and **no fan-out
process running at all**:

```
{'age_seconds': 13004, 'checked_at': '2026-09-11T19:12:35Z', 'refreshing': True}
# ps w — nothing
```

The claim that says "a refresh is running" was a flag taken before the work
and released by a guard when it finished. That is correct for a crash and
wrong for everything else: a task dropped before it starts constructs no
guard, and a blocking call that never returns never drops one. Either way the
flag stayed set and every later refresh returned early.

It is a **deadline** now, and a deadline cannot be lost: the claim expires
whether or not anything is left to release it.

Worth knowing even now it is fixed, because the normal case is slower than it
looks. A refresh asks four sources and takes between **75 and 230 seconds** on
this hardware, and the control is disabled for all of it.

*Tracked as SQU-201.*

### The TLS certificate was an expired fossil

**Fixed in v2.24.0 (SQU-115).** `/etc/ssl/certs/bmcd_cert.pem` on the reference
board was issued **June 2025** and **expired July 2025**. It was RSA 4096, had
no subject-alternative name — which no browser has accepted since 2017 — and
lives on the overlay, so it survived every firmware upgrade this fork had
shipped up to that point.

Three things were wrong at once, and all three are covered by
[a certificate that does not rot](../features/a-certificate-that-does-not-rot.md):
the generation script now issues EC P-384 with real names and **825 days** of
validity, reissues **30 days** before expiry rather than only when the file is
missing, and refuses to touch a certificate it did not issue. Fifteen
assertions cover it in CI.

Measured on both boards on **2026-09-11**, after the fork's own certificates
were replaced with ones from the estate's internal authority:

```
subject=CN=bmc-1.haarlem.lan   issuer=CN=hive-internal-ca-p384
notBefore=Sep 11 10:55:09 2026 GMT   notAfter=Dec 10 10:55:09 2026 GMT
```

P-384, named, and inside its validity on both. The board also publishes
`bmcd_tls_certificate_expiry_timestamp_seconds`, so the next expiry is
something a scrape notices rather than a person.

### mDNS ate the board

**Affected v2.9.0 through v2.12.0; fixed in v2.13.0.** The `mdnsd` that
advertised `turingpi.local` leaked about **0.85 MB a minute** and did not
stop. On a board with 116 MB of RAM that was fatal in roughly ninety minutes:
userspace stopped answering, the kernel kept replying to ping for a while, and
only cutting the power brought it back. It happened twice on 2026-09-09.

The rate followed mDNS traffic rather than time, so a quiet network hid it
entirely and a busy one killed the board before lunch. That is why it read as
intermittent.

**The cause was the switch ports.** Every DSA port on this board — `node1`
through `node4`, `ge0`, `ge1`, `dsa` — carries the same MAC address, and
`mdnsd` bound all of them. It saw its own advertisement arrive from what looked
like another host with its name, declared a conflict, and reloaded its
configuration: **825 times in twelve seconds**, leaking on each one.

The fix is one line, binding it to the bridge instead:

```sh
MDNSD_ARGS="-i br0"
```

Measured after: **0 reloads in 90 seconds and 8 kB of growth**, against
956 kB/minute before. On an affected release, restarting the daemon is still a
complete and instant remedy:

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
