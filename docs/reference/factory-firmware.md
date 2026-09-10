# The factory firmware

What a stock Turing Pi 2 looks like before any of this fork touches it.

Every value and every screenshot on this page came off a second board
— board B, still sealed on its shipped firmware — on **2026-09-10**. Nothing
here is quoted from upstream's documentation; it is what the board itself
reported.

The point of recording it is that it stops being observable the moment the
board is upgraded. A comparison against a baseline nobody kept is not a
comparison.

## What it reports about itself

![The About tab on stock firmware](../assets/factory/08-about.png)

| | value |
|---|---|
| Board model | Turing Pi 2 (v2.5.1) — **stock's answer, and it is wrong**; see below |
| Daemon (`bmcd`) | 2.3.2 |
| BMC UI | 3.3.3 |
| API | 1.1 |
| Buildroot | 2024.05.1 |
| Kernel | 6.8.12 |
| `tpi` | 1.0.6 |
| Built | 2024-09-03, two years before this capture |
| Hostname | `turingpi` |

!!! note "Build version v2024.05.1 is not a firmware version"
    The About tab reports **Build version v2024.05.1**, which is Buildroot's
    release, not the firmware's. The
    [install guide](../guides/install.md) mentions this leak; the screenshot
    above is the board doing it.

!!! warning "Stock names the wrong board revision"
    The screenshot says **v2.5.1**. The board is a **v2.5.2**.

    This was only visible because the same board was read twice. Stock
    firmware reported `v2.5.1`; after the upgrade, on the same hardware
    minutes later, this fork reported `v2.5.2`. Hardware settles it: a
    v2.5.1 has no PCF8563 real-time clock, and this board's answers a
    register read on `/dev/rtc1`. The chip is fitted, so the board is not a
    v2.5.1.

    The likely cause is ordinary and worth knowing: stock `bmcd` 2.3.2 was
    built on 2024-09-03, and it appears to report the newest revision it has
    heard of rather than admitting an unknown one. A board newer than the
    firmware gets silently aged down.

    It matters because board revision is what a person checks before
    believing a compatibility note. If your stock board says v2.5.1, that is
    a claim about your firmware's vintage as much as your hardware.

## The interface, tab by tab

Stock firmware serves six tabs. This fork adds a console, a network tab and a
settings tab on top of them, so the six below are the common ground.

### Login

![The login screen](../assets/factory/01-login.png)

A local username and password, and nothing else. There is no second factor and
no identity provider.

### Info

![The Info tab](../assets/factory/04-info.png)

Storage, one fan slider, the bridge address, and buttons to reboot the BMC or
reload the daemon. The MAC on this page has been replaced with the IANA
documentation address; everything else is untouched.

### Nodes

![The Nodes tab](../assets/factory/03-nodes.png)

Four power toggles and four restart buttons. All four modules were powered on
when this was taken, which is what the toggle position means here.

### USB

![The USB tab](../assets/factory/05-usb.png)

One USB bus, routed to one node at a time. The mode is Host, Device or Flash,
with a separate compatibility toggle for node 1's USB-A port. The capture shows
Flash mode pointed at node 2, left over from writing that module minutes
earlier — the board keeps the last route, it does not return to a default.

### Flash Node

![The Flash Node tab](../assets/factory/06-flash-node.png)

Write an operating system image to one module's eMMC: a node, a local or remote
file, and an optional SHA-256. A **Skip CRC** checkbox sits beside the install
button, so the one integrity check on offer can be turned off at the point of
use.

### Firmware Upgrade

![The Firmware Upgrade tab](../assets/factory/07-firmware-upgrade.png)

A `.tpu` file, an optional SHA-256, and an Upgrade button. This is the screen
that installs this fork, and the optional checksum field is the only integrity
check stock firmware offers.

## The API underneath

Authentication is a POST of a username and password to
`/api/bmc/authenticate`, which returns a 64-character token used as a bearer
token on every later call. Off-board calls without one are refused with `401`.

!!! danger "On the board itself, there is no authentication at all"
    A request to `https://127.0.0.1/api/bmc` from the BMC's own shell answers
    in full **without any credential**. Anything that can run code on the
    board — or reach that socket — holds the whole API, including node power
    and flashing.

    This fork inherits the bypass. Since v2.14.0 it at least *records* one —
    an unauthenticated call writes an audit line saying so — which makes it
    findable afterwards, not prevented. [What is and isn't
    fixed](known-faults.md) carries the detail and the plan to remove it.

## Flash layout

The NAND is one megabyte of boot plus a 255 MB UBI, divided in three:

| volume | size | holds |
|---|---|---|
| `uboot-env` | 124 KiB | the bootloader environment |
| `rootfs` | 38.1 MiB | the read-only root |
| `overlay` | 151.3 MiB | everything that survives a reboot |

The root is mounted as an overlay: a read-only lower layer with the overlay
volume written on top. That is why a file edited on a running board — an
authorised key, a password — persists, while the image underneath stays
whatever was flashed.

## Going back

Rolling back to stock means flashing an official image through the same
Firmware Upgrade tab pictured above. Turing Pi publishes those by two routes
that do not agree with each other; which one to trust, and why neither carries
a checksum, is [its own page](comparison.md).
