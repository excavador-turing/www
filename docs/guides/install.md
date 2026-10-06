---
description: "Install this firmware on your own Turing Pi 2: which file to take, flashing over the network or from the SD card installer, and what to check afterwards."
render_macros: true
---

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

- A Turing Pi 2, revision **v2.4, v2.5, v2.5.1 or v2.5.2** — upstream's
  compatibility list. What has actually been run is the record below: the
  two boards this fork is developed against, across the upgrades
  [their own counters record](../reference/gate-history.md), and every
  report a reader has sent. It is a record, not a test matrix, and this page
  will not pretend otherwise. Ran it on a board not listed?
  [Say so](../feedback.md) and it goes in.

    {{ board_reports() }}

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

## From an SD card: the installer

Every release also ships a `-sdcard-*.img`. **That card is an installer, not a
way to try a version.** Written as it comes and put in the board, it offers a
fresh installation of the firmware. For upgrades, use the `.tpu` — through the
web interface's Firmware page, `tpi firmware` or `tpi-selfupdate`, as above.
It replaces the root filesystem and always kept the overlay, so the password,
the certificate and the settings survive. The card is for recovery, or for a
reset you mean to do.

!!! warning "Cards from v2.41.0 and earlier erase the password, the certificate and the settings"
    Until v2.41.0 the installer formatted the board's whole UBI partition and
    wrote back only the bootloader environment and the root filesystem. The
    overlay volume went with it: the root password returned to `turing`, the
    board generated a new self-signed certificate, and the network, NTP, fan
    and node settings were gone. That is how the installer from Turing Pi's own
    tree behaves, and this fork's card inherited it. **From v2.42.0 the card
    keeps the overlay** when the installer can verify that the volume is intact
    and that the board will attach it afterwards. When it cannot, it erases as
    before and says why on the serial console. A card you wrote from v2.41.0 or
    earlier still erases, so write a fresh one.

```console
$ xz -d tp2-bmc-firmware-sdcard-v2.32.0.img.xz
$ sudo dd if=tp2-bmc-firmware-sdcard-v2.32.0.img of=/dev/sdX bs=4M status=progress conv=fsync
```

Insert the card and power-cycle the board. The installer then prints on the
serial console what it is about to do (keep the settings, or erase everything
and why) and waits for confirmation, forever if it gets none. Confirm either by
typing `CONFIRM` at the prompt, or by pressing one of the front panel buttons
(POWER or RESET), or the KEY1 button on the board, three times in a row. The
presses proceed with whatever the prompt said. Most people have no serial
console attached and see only the LEDs, so the three presses are the realistic
route. If you did not mean to install, pull the card and power-cycle: nothing
has been written until you confirm.

### Forcing a factory reset

To reset the board on purpose, put a file named `factory-reset.txt` on the
card's first (FAT) partition, next to `install.txt`. Its contents are ignored.
Windows hides extensions by default, so `factory-reset.txt.txt` is accepted
too. Or type `ERASE` instead of `CONFIRM` at the serial prompt. Either way the
installer erases the overlay: the password returns to `turing`, the
certificate is regenerated, and the settings go.

### Booting from the card without installing

The installer runs because a file named `install.txt` is on the card's first
partition, the FAT one. Delete it, or rename it, after writing the image and
before inserting the card, and the board boots from the card instead:

- **The NAND is untouched.** Pull the card, power-cycle, and the board is back
  on whatever was installed before, including a stock board that has never
  seen this fork. This is the way to try a version without committing to it.
- **Your settings do not follow.** The overlay that holds the hostname, the
  NTP servers, the fan mode and the certificate lives on the board's NAND. A
  card boot creates its own overlay partition on the card on first boot and
  starts from defaults.

This is also the path to take for anything that can strand the board. It is
how the switch and VLAN work will be done, with the USB-OTG console attached,
because a wrong network configuration on a card boot is a power cycle away
from being gone.

*Checked 2026-10-06 in simulation, not yet on a board. The installer's unit
tests run on a simulated NAND. In CI, a real Linux 6.8 kernel's `nandsim` with
the board's geometry (2 KiB page, 128 KiB eraseblock, 256 MiB) takes a board
built the way the firmware builds it, installs over it, attaches it with the
kernel, and mounts the kept UBIFS with every file's checksum matching and the
volume still writable. It also covers a second install, a factory reset, no
overlay, a corrupt superblock and the overlay at other volume ids. I have not
yet run a card through the installer on a physical board.*

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
