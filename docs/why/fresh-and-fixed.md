---
title: Fresh, and fixed
render_macros: true
description: "Why this firmware moved to a longterm kernel and a supported Buildroot, and the named faults that came out with it."
---

# Fresh, and fixed

This is the argument behind [Fresh, and fixed](../features/fresh-and-fixed.md), with the measurements that back it. The feature page is the short version.

## The base is supported again

| | upstream | this fork |
|---|---|---|
| Kernel | 6.8, not a longterm series | **6.12.109**, a longterm series |
| Buildroot | 2024.05.1, end of life | **2025.02 LTS** |
| Last release | February 2025 | continuous |

The difference is not a bigger number. A longterm kernel keeps receiving
security and stability fixes from upstream Linux; 6.8 does not, so a board on
it accumulates known, published, unfixed defects for as long as it runs. The
same is true of an end-of-life Buildroot: every package in the image stops
getting updates at once.

## What was actually broken

Six faults are worth naming, because each one either took the board out or
made it lie to you. All are fixed and each has its ticket in
[what is and isn't fixed](../reference/known-faults.md).

**The board died silently, twice in one day.** Only a full power cut brought
it back. The cause was the mDNS responder: `mdnsd` 0.12 bound every switch
port, saw its own announcements as a conflict, and leaked about **0.85 MB a
minute** on each reload. On a 116 MB board that is a few hours to death. Fixed
by binding it to the bridge alone.

**A serial console could reboot the board by accident.** Magic SysRq on BREAK
was unguarded, so a serial adapter that dropped a line could restart the BMC.

**The Firmware page froze** on open and on "Check now", because the catalogue
was fetched synchronously from every source in turn.

**`tpi firmware` failed with exit 141** whenever the nodes were powered, while
the manual UBI path worked — so the documented command was the one that did
not.

**Five `tpi` releases were green and shipped nothing.** The release job
aborted on the very tag that triggered it, and nothing noticed because the
workflow went green.

**`turingpi.local` stopped resolving** when avahi was dropped, which also
meant `tpi` with no `--host` failed rather than falling back.

## {{ releases.total }} releases, and a count that is not decoration

| component | releases |
|---|---|
| BMC-Firmware | 17 |
| bmcd | 24 |
| BMC-UI | 19 |
| tpi | 6 |

Every one of them is listed on this site with its own release note,
[fetched from the releases themselves](../changelog/index.md) by
`just refresh-changelog` rather than written by hand — so the changelog and
the releases cannot disagree.

!!! note "Fast releasing is not the same as being stable"
    A high release count is only a good sign if a bad release cannot hurt you.
    That is what the [health-gated promotion](../features/updates-that-undo-themselves.md)
    is for: this board has taken {{ gate.promoted }} firmware updates and
    rolled {{ gate.rolled_back }} back by
    itself, with nobody at the rack. Releasing often and reverting
    automatically are the same policy seen from two sides.

## What it does not cover

A supported base is not a finished one. {{ faults.count }} faults are open on this fork right now, each with a ticket, and [the honest list](../reference/known-faults.md) is the other half of this page.

Tracking a longterm kernel also means tracking it: the guarantee is that the base is still receiving fixes, not that every fix has already been taken. What this board runs is what its [About tab reports](../features/see-what-the-board-sees.md), and what the fork has published is [the changelog](../changelog/firmware.md).

<div class="tp-next tp-next--argument"><a href="../../features/fresh-and-fixed/"><b>Back to the feature →</b><span>The short version: the claim, its numbers and the picture.</span></a><a href="../#demo/fork"><b>See it in the demo →</b><span>The About tab, naming every component's version.</span></a><a href="../guides/upgrade-from-stock/"><b>Do it on your board →</b><span>Move a board off the firmware it shipped with.</span></a><a href="../reference/comparison/"><b>The evidence →</b><span>Every row against upstream, including where upstream leads.</span></a><a href="../pick-a-version/"><b>Pick a version, from anywhere →</b><span>Why upstream's two catalogues disagree by a release.</span></a></div>
