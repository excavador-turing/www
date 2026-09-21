# Installing on your own board

!!! danger "Read this part"
    This is unofficial firmware for hardware you own. It has run on two boards
    — both mine, both revision v2.5.2 — across the upgrades
    [their own counters record](../reference/gate-history.md).

    The A/B health gate makes it **safer than upstream's update path**: a bad
    image reboots back onto the previous one by itself. But it cannot save an
    image that hangs *before* the gate runs, and recovering from that means
    physical access to the board.

    Do not do this to a board you cannot reach.

## What you need

- A Turing Pi 2, revision **v2.4, v2.5, v2.5.1 or v2.5.2**.

    What has actually been run, rather than upstream's compatibility list:
    **v2.5.2** on the two boards this fork is developed against, across the
    upgrades [their own counters record](../reference/gate-history.md); and
    **v2.4** by two readers: one on 2026-09-16, who installed from the SD
    image below and found no crash and no bug; one on 2026-09-21, who went
    from the factory 2024.05.1 image to v2.34.0 in NAND by uploading the
    `.tpu` and then set up the Split layout. Two boards and two reports is
    not a test matrix, and this page will not pretend otherwise.
- The BMC reachable over the network
- Its root password

## Check what you have

```console
$ ssh root@BMC 'cat /etc/os-release | grep VERSION'
```

A stock board reports something like `v2.0.5`. If it reports `2024.05.1`, that
is Buildroot's version leaking through an upstream bug — the board is older
still.

## From the command line

The board fetches, verifies and stages the image itself:

```console
$ ssh root@BMC 'tpi-selfupdate --channel stable'
```

That verifies the download against the release's published `SHA256SUMS`,
checks the image fits the UBI slot, writes it to the *spare* slot and arms a
one-shot boot flag. **Nothing has changed yet.** Reboot when you choose:

```console
$ ssh root@BMC reboot
```

The board then boots the new image *tentatively*. It is kept only if the daemon
answers and every module's switch port is present; otherwise the board reboots
and lands back on what you had.

!!! tip "The first install is the awkward one"
    A stock board has no `tpi-selfupdate` — it ships with this fork. For the
    first install, upload the `.tpu` from
    [the releases page](https://github.com/excavador-turing/BMC-Firmware/releases)
    through the stock web interface's **Firmware Upgrade** tab, with the
    published SHA-256 in the checksum field.

## From an SD card, without touching the NAND

Every release also ships a `-sdcard-*.img`, and the board boots from a card
when one is present. Nothing is written to the board's own storage, so this
is the way to try a version without committing to it — and the way back when
something on the NAND has gone wrong.

```console
$ xz -d tp2-bmc-firmware-sdcard-v2.32.0.img.xz
$ sudo dd if=tp2-bmc-firmware-sdcard-v2.32.0.img of=/dev/sdX bs=4M status=progress conv=fsync
```

Insert the card, power-cycle the board, and it comes up on the image from the
card. The interface looks the same; `tpi info` reports the version you wrote.

Two things to know before you rely on it:

- **The NAND is untouched.** Pull the card, power-cycle, and the board is back
  on whatever was installed before — including a stock board that has never
  seen this fork.
- **Your settings do not follow.** The overlay that holds the hostname, the
  NTP servers, the fan mode and the certificate lives on the board, not on the
  card, so a card boot starts from defaults.

This is also the path to take for anything that can strand the board. It is
how the switch and VLAN work will be done, with the USB-OTG console attached,
because a wrong network configuration on a card boot is a power cycle away
from being gone.

## Afterwards

**The first thing the board asks for is a password.** Boards ship as `root` /
`turing`, which is printed in the quick-start guide and is the same on every
board — so until it is changed the interface shows one page and the API
refuses everything else. Twelve characters minimum. It is one account: the new
password is also this board's SSH password.

If you had already changed it over SSH, you are never asked.

The interface gains a **Firmware Upgrade** page that lists what every
configured source offers, and installs a chosen version. Four sources ship by
default: this fork, the SD card, and both of Turing Pi's own channels.

## Going back

The rollback slot still holds your previous image until the next upgrade
overwrites it. To return to stock, add Turing Pi's source — it is already
configured — and install one of their versions. It will be listed under *show
older or unrelated versions*, because it is older, and the confirmation will
say so.
