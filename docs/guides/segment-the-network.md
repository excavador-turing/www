---
title: Segment the network
render_macros: true
---

# Segment the network

By default everything on this board shares one network: the four compute
modules, the BMC itself, and both uplink jacks. Anything a module can reach,
it can reach the BMC on — and the BMC can reflash any of them.

This page is how to change that, and what it costs.

!!! warning "Not in a release yet"

    The switch controls described here are built and merged, and no firmware
    release carries them. Until one does, this page is what is coming rather
    than what you can do today. The
    [roadmap](../roadmap.md) is where to watch, and it is the item with the
    most votes.

## What the board's switch actually is

Seven ports on one chip:

| | |
|---|---|
| four | one per compute module |
| one | the BMC's own, behind a 100 Mbit PHY |
| two | the uplink jacks, `ge0` and `ge1` |

All seven sit in one bridge, with VLAN filtering off and spanning tree off.
Two consequences follow from that, and they are the reason this page exists.

**The management plane shares a network with your workloads.** A container on
a module can reach the interface that can power it off and overwrite it.

**Two cables to the same switch is a loop.** With spanning tree off there is
nothing to break it, so plugging both jacks into one network floods it. That
is why `ge1` has been a cold spare rather than redundancy.

## Three shapes to choose from

The board offers three, and it expands them itself — the interface, `tpi` and
the fleet all ask the board what a preset means rather than deciding for
themselves, so none of them can disagree with the switch about what is
configured.

### Flat

What a board ships as, and what the reset goes back to. One network, no
filtering. Choose it when the board is on a network you already trust.

### Split

Two groups that never meet, and **nothing tagged ever leaves the board**:

- the BMC's own port and `ge0`
- the four modules and `ge1`

Two cables, two separate things on the other end, and the upstream switch
needs no VLAN configuration at all — it never sees a tag. This is the shape
for somebody with a plain unmanaged switch, or two of them.

It is also the least that can go wrong. No tags, no spanning tree, no router
configuration to match.

**What has to be true first:** both jacks plugged into whatever separation you
want. The board does not create that separation upstream; it only stops the
two groups meeting *inside the board*.

### Trunk

One cable carrying both networks, tagged, for a router that speaks VLANs:

- a **management VLAN**, untagged on the BMC's own port and tagged on `ge0`
- a **node VLAN**, untagged on the modules and tagged on `ge0`

The second jack is **redundant by default**: `ge1` carries the same VLANs and
spanning tree decides which one forwards. You may turn it off instead, leaving
`ge1` carrying nothing. The board refuses two uplinks sharing a VLAN with
spanning tree off, because that is the loop above.

The two VLAN numbers are **yours**. Your router has to use the same ones, and
only you know what is free there.

**What has to be true first, on the other end:**

- both VLANs exist on the router, on the port the board is plugged into
- something answers DHCP on the management VLAN, or the board holds a static
  address there

That second one is the trap. Spanning tree's delay is handled for you — see
below — but a DHCP server that does not answer on the new segment is not, and
it looks exactly like a board that has gone away.

## Your own layout

The three above are starting points, not modes. **The table is editable**, and
once you have picked a preset you are simply editing it — there is nothing to
switch into and nothing to switch back out of.

Each port gets one **untagged** VLAN, or none, and any number of **tagged**
ones. A port in no VLAN carries nothing, which is how you park an uplink you
are not using. Two switches sit under the table: whether the switch looks at
VLANs at all, and whether spanning tree is on.

**The BMC's own port is untagged only**, so its tagged box cannot be typed in.
This board's network stack reads untagged frames; a tag there would be traffic
it cannot see.

**Name your VLANs.** Beside each number there is a box for a word —
`management`, `storage`, `guests`. The board carries the names with the
configuration and never acts on them. They are for the person who opens this
board in a year, which is usually you, having forgotten what 30 was for.

**The board checks every edit as you make it.** Not this page, and not the
interface — the board. Each change goes to it and comes back either accepted,
or refused with the reason in the board's own words, and Apply is greyed out
until it is accepted. Warnings appear beside the port they are about. Nothing
here keeps its own copy of the rules, because a copy would eventually disagree
with the board, and the way that disagreement shows up is a board nobody can
reach.

### One module on its own network

Say `node3` runs something that should not see the rest.

1. Start from **Flat**, then turn *Look at VLANs* on.
2. Set `node3`'s untagged VLAN to `30`, and name it.
3. The board warns: *VLAN 30 has one member, node 3. It can talk to nobody.*
   True — it has no way off the board.
4. Put `ge1` in `30` as well and plug `ge1` into the port your router serves
   that network on. The warning goes.

Everything else stays in VLAN 1 out of `ge0`, including the BMC.

### Two networks, one cable

Both VLANs tagged out of `ge0`, which is what **Trunk** builds — but by hand
you can mix: the modules split across two VLANs, one uplink trunked and the
other parked, the BMC untagged on the management VLAN. The refusals below are
the only shapes the board will not build.

## Applying it without locking yourself out

The board's own port is the one that can strand it. Put it in a VLAN nothing
else is in, and nothing can reach the board — including the page you would use
to undo it.

So the board refuses the configurations that do that, rather than warning:

- the BMC's port in no untagged VLAN
- the BMC's port alone in its VLAN
- a BMC VLAN that no uplink carries, so the board would answer only to the
  modules it exists to administer
- a tagged BMC port, which the board's own network stack cannot read
- two uplinks sharing a VLAN with spanning tree off

Everything else is a warning next to the port it is about, and you may
proceed.

### Apply, then confirm

An apply does **not** keep the change. It puts it on the switch and starts a
window; a second request confirms it.

That second request is the whole proof. After an apply the old path no longer
exists, so if a confirmation reaches the board at all, the new configuration
works. Nothing else has to be checked.

**If it does not reach the board, there is nothing to press.** The board puts
the previous configuration back by itself and records why, and the next time
you load the page it tells you: *your change at 12:03 was put back because it
was not confirmed in time*. That is the design working.

### Try it

Beside Apply there is **Try it**, which does the same thing with no intention
of confirming. Apply the layout, watch what you reach the board by, and let
the window run out.

For a hand-made layout this is the honest dry run, and it is the only one
there is. A configuration can be correct, pass every refusal, and still cut
the particular path *you* arrive by — and the way you find that out is by
losing the page. Try it means losing the page for thirty seconds on purpose
rather than indefinitely by accident.

### Confirm from the network you just changed

> Confirm from the browser, or from `tpi` on the machine you reach the board
> with. That is the whole proof: if the confirmation arrives, the new
> configuration works for you. A confirmation sent from a shell **on the board
> itself** arrives over nothing, proves nothing, and the board refuses it.

This is not theory. On 20 September 2026 a configuration that had been reasoned
through and looked harmless was applied to a board and confirmed from that
board's own console. It locked its owner out of the interface — and the revert
window, which exists for exactly that, never got the chance to run, because
the confirmation had already arrived.

### Why the countdown starts late

**The window is 30 seconds by default, and it does not start when you press
Apply.** It starts when the uplink carrying the BMC's VLAN begins forwarding.

Spanning tree holds a port in listening and then learning for its own
forwarding delay — also 30 seconds, by default — before it passes a frame. A
window counted from the apply would therefore expire before anybody could
confirm a correct Trunk change, every time.

The page says which of the two it is waiting on, so a countdown that has not
started reads as *waiting for the uplink* rather than as a number you are
losing.

You can set the window per apply, between 10 seconds and 5 minutes.

## If it goes wrong

In order. The first one is almost always enough.

**1. Wait.** Do not confirm, and the board reverts on its own within the
window. This is the ordinary recovery and it needs nothing from you. And if
you are ever tempted to confirm from the board's own console to save the
change — do not. Let it revert.

**2. Reboot.** Only a *confirmed* configuration is ever written down. A reboot
during the window comes back on the previous one, because the pending change
never reached the disk.

**3. Hold the safe-mode key at power-on.** The board then skips applying its
switch configuration entirely and comes up on the default network. This is the
exit from a configuration that *was* reachable when you confirmed it and has
since stopped being — because a cable moved, or the router changed.

**4. The USB-OTG console.** A serial console over the micro-USB port, which
needs no network at all. [Recovering a bad flash](recover-a-bad-flash.md)
describes it.

**5. An SD-card boot** from a released image, the last exit for anything else.

The thing worth carrying away: **nothing you can do from this page survives a
power cycle unless you confirmed it.**

## What this does not cover

**The BMC's own port is untagged only.** Giving the board's Linux a tagged
sub-interface, so the BMC itself sits on several VLANs, is not in the
first version. Ask if you want it.

**There is no "apply to every board" in the fleet.** Deliberately. Stranding
eight boards in one click is the worst thing this feature could do, and
applying per board with a confirmation each costs about a minute.

**LACP is not here either**, and is not planned: the driver has no link
aggregation offload, and the gain would be board-aggregate bandwidth rather
than per-module.

<div class="tp-next">
<a href="../../features/see-what-the-board-sees/"><b>What the switch reports →</b><span>Link, speed and counters per port, before you move anything onto an uplink.</span></a>
<a href="../recover-a-bad-flash/"><b>The console and the SD card →</b><span>The two recoveries that need no network.</span></a>
<a href="../facing-the-internet/"><b>Should it face the internet? →</b><span>The other half of keeping this board where it belongs.</span></a>
<a href="../../roadmap/"><b>Vote on what comes next →</b><span>Including per-port tagging for the BMC itself.</span></a>
</div>
