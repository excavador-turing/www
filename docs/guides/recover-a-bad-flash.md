---
description: "Get a Turing Pi 2 BMC back after a bad firmware flash: what the board undoes by itself, and the recovery paths for when it cannot."
---

# Recover a bad flash

What to do when a firmware update goes wrong, in the order the board itself
tries them.

## First: it probably already recovered

A new image boots tentatively. If the daemon does not answer, or a compute
module's switch port is missing, or the image is not the one that was staged,
the board reboots **onto the version it had** and writes down why.

This is what that looks like on a board that has just refused an image:

```console
$ tpi firmware list
running v2.8.0
last boot  FAILED: staged v0.0.1 but this image reports v2.8.1-rc1
```

and in full, from the board's own log:

```
23:29:54 postupdate: tentative boot; checking this image before making it permanent
23:29:57 postupdate: bmcd answered after 3s
23:29:57 postupdate: switch ports present: node1 node2 node3 node4
23:29:57 postupdate: FAILED: staged v0.0.1 but this image reports v2.8.1-rc1
23:29:57 postupdate: rolling back to the volume named rootfs by rebooting
```

About 35 seconds, and the compute modules kept running throughout. There is
nothing to do except find out why the image was bad.

The log is `/mnt/overlay/postupdate.log`, and it survives the rollback it
describes — both firmware images mount that volume, which is the whole reason
the note is written there instead of `/var/log`, which is a tmpfs.

## If an update is staged and you have changed your mind

```console
$ fw_setenv nextboot
```

That clears the one-shot boot variable. The next boot is a normal one on the
current image, and the staged image is simply never taken.

## If the board answers but the interface is wrong

Reinstall over it. Any candidate can be installed, including one older than
what is running:

```console
$ tpi firmware list --all
$ tpi firmware install v2.8.1 --yes
$ tpi reboot
```

The gate will check the result exactly as it checks any other image.

## If the board does not answer at all

Establish what kind of "not answering" it is, because the remedies differ.

**Does it reply to ping?** If yes, the kernel is running and userspace is not.
If no, check your route before you check the board — a whole subnet going
quiet is much more often a firewall window or a missing route than four
machines failing at once.

**Are the compute modules still up?** They are on the board's switch and it
keeps forwarding once configured, so they usually are. If the modules answer
and the BMC does not, nothing you are running is at risk and you have time.

From a machine on the same fabric:

```console
$ ping -c2 <bmc>
$ for p in 22 80 443; do nc -z -w3 <bmc> $p && echo "$p open" || echo "$p closed"; done
```

If the kernel answers and every port is closed, there is no remote path back
in. The board needs its power cut. That is the situation a hardware watchdog
would fix, and this firmware does not arm one yet — see
[what is and isn't fixed](../reference/known-faults.md).

## If you gave the board an address you cannot reach

The address card should make this impossible: an address goes on the bridge
and is kept only when you confirm from it, and a wrong one is put back by
itself. This section is for the two ways round that — a file edited by hand
over SSH, or a card change confirmed from an address that then stopped being
reachable (a VLAN change on the router, a moved cable).

The board has a **safe mode**, documented by upstream: hold **KEY1** for five
seconds while powering on, or after releasing **BMC_RESET**, and it boots
with every change on the overlay set aside — factory network settings, so
DHCP on `br0`, SSH on, the factory password — without deleting anything. A
plain reboot afterwards brings the overlay back exactly as it was.
([Failsafe boot](https://docs.turingpi.com/docs/turing-pi2-bmc-failsafe-boot),
upstream's page.)

From safe mode, over SSH, the file the boot path reads is on the overlay:

```console
$ mount_overlay
$ vi /mnt/overlay/upper/etc/network/interfaces   # fix it, or delete it for DHCP
$ reboot
```

Deleting it is the image's default, which is DHCP. Do not edit
`/etc/resolv.conf` on this image to fix a resolver: it is a link into memory
and is empty at every boot. The resolvers belong in the stanza, where the
address card puts them, and the boot path writes them from there.

## If the board will not boot at all

The SD card is the recovery path. Every release publishes a `.img` alongside
the `.tpu`:

```console
$ curl -LO https://github.com/excavador-turing/BMC-Firmware/releases/download/v2.9.2/tp2-bmc-firmware-sdcard-v2.9.2.img
$ curl -LO https://github.com/excavador-turing/BMC-Firmware/releases/download/v2.9.2/SHA256SUMS
$ sha256sum -c SHA256SUMS --ignore-missing
```

Write it to a card, put the card in the board, and hold KEY1 while powering
on. Verify the checksum first — this is the image that runs when nothing else
does.

!!! warning "Cutting power hard-cuts the compute modules"
    Everything above this section leaves the modules running. Pulling the
    board's power does not. If they are running anything that would rather be
    shut down cleanly, do that first.
