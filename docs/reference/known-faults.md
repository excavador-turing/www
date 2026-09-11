# What is and isn't fixed

A fork that lists only what it improved is advertising. This page is the other
half: what is wrong with this firmware today, measured, with the ticket that
tracks it. Nothing here is theoretical — each line is something observed on a
running board.

## Open

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
