# Installing on your own board

!!! danger "Read this part"
    This is unofficial firmware for hardware you own. It has run on exactly one
    board — mine — across the upgrades
    [its own counter records](../reference/gate-history.md).

    The A/B health gate makes it **safer than upstream's update path**: a bad
    image reboots back onto the previous one by itself. But it cannot save an
    image that hangs *before* the gate runs, and recovering from that means
    physical access to the board.

    Do not do this to a board you cannot reach.

## What you need

- A Turing Pi 2, revision **v2.4, v2.5 or v2.5.1**
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

## Afterwards

The interface gains a **Firmware Upgrade** page that lists what every
configured source offers, and installs a chosen version. Four sources ship by
default: this fork, the SD card, and both of Turing Pi's own channels.

## Going back

The rollback slot still holds your previous image until the next upgrade
overwrites it. To return to stock, add Turing Pi's source — it is already
configured — and install one of their versions. It will be listed under *show
older or unrelated versions*, because it is older, and the confirmation will
say so.
