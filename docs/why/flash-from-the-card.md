---
title: Flash a module from the card
---

# Flash a module from the card

This is the argument behind [Flash a module from the card](../features/flash-from-the-card.md), with the measurements that back it. The feature page is the short version.

Writing an operating system to a compute module means moving about two
gigabytes. Doing it from a browser means moving those bytes twice — up to the
board and then onto the module — over a management network, with an interface
holding the upload open the whole time. Doing it from the board's own SD card
means moving them once.

`tpi flash --local` has read images off that card for as long as the fork has
existed. What the interface could not do is **see what was on it**. The field
was free text labelled "File (remote or local)", the operator had to know the
path, and a wrong one was reported as a failure some minutes after the most
destructive button on the board had been pressed.

## What the daemon answers

`GET /api/bmc/sdcard/files` lists the card. Every entry carries its path, its
size, whether it can be written to a module, and — when it cannot — why not.

| | |
|---|---|
| Entries on bmc-1 | 16 |
| Flashable | 2 |
| Refused, with a reason | 14 |

The reasons are the point. `a directory`. `BMC firmware, not a node image —
use the firmware page`. An operator who cannot find their image wants to see
it listed and told why it was rejected, not to wonder where it went.

## The interface never decides what is flashable

Every row renders `flashable` and `reason` exactly as the board sends them.
There is no filename check in the interface, deliberately.

An interface that guessed would agree with the daemon only until one of them
changed, and the disagreement would not show up as a mismatch: it would show
up as a flash that the operator started and the board refused, minutes later,
after they had already committed. The interface's job here is to show what the
board decided, not to have an opinion.

## The card's free space is on the dialog

`GET /api/bmc/sdcard` reports capacity, and the picker says how much is left
before anything is chosen. A full card is a normal outcome on a 32 GB card
that also holds staged firmware, and it should be visible before a transfer
starts rather than after it fails.

## Two bugs this found on the way

**The install button threw before sending anything.** Both flash forms read
`form.elements.namedItem("file-url")` — a field neither had had for several
releases. `namedItem` answers null, reading `.value` off null throws, and the
handler died inside the confirmation modal. Pressing Install did nothing at
all, every time, and the only trace was a TypeError in the browser console.
The firmware page's candidate list is the path people actually use, which is
why nobody reported it.

**The capacity endpoint answers an array of one.** The document says
`minItems: 1, maxItems: 1` and the board agrees. Read as an object it yields
an undefined `free`, which reaches the byte formatter and throws "Invalid
number" — blanking the whole tab behind an error boundary, with the cause
three layers from the message.

Both were found by driving a browser against a real board rather than by
reading types, which is the only reason either is in this release.

!!! note "What this does not do yet"
    The checksum is not computed on the board. Doing it means reading a
    multi-gigabyte file on a machine with about 87 MB of usable memory, so it
    has to be on demand, reported as progress, and cached against size and
    modification time — none of which the daemon offers yet. Uploading,
    renaming and moving files on the card are not here either. Both are
    tracked in SQU-198.
