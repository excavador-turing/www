# Upgrading from stock firmware

What changes on your board, what it costs, and how to go back.

Every timing and every screenshot on this page came from doing it once, on a
board that shipped with stock firmware, on **2026-09-10**. Where something was
not measured, it says so.

Read [Installing on your own board](install.md) first for the warnings. This
page is the transition itself.

## What you have, and what you get

=== "Stock"

    ![The stock About tab](../assets/factory/08-about.png)

    Six tabs. bmcd 2.3.2, BMC UI 3.3.3, Buildroot 2024.05.1, kernel 6.8.12,
    built 2024-09-03.

=== "This fork"

    ![The About tab after the upgrade](../assets/fork/10-about.png)

    Seven tabs — a console, a network tab and a settings tab that stock does
    not have. bmcd 2.29.0, BMC UI 3.19.0, Buildroot 2025.02.17, kernel
    **6.12.109 LTS**.

The full stock interface, tab by tab, is [its own
page](../reference/factory-firmware.md), captured before this board was
upgraded.

## Doing it

Download the `.tpu` and its checksum from [the releases
page](https://github.com/excavador-turing/BMC-Firmware/releases). Verify it
before it goes near the board:

```console
$ sha256sum -c tp2-bmc-firmware-ota-v2.20.0.tpu.sha256
```

Then either route below. **Both stage the image and neither applies it until
the board reboots.**

### Through the interface

Stock's **Firmware Upgrade** tab takes the file and, optionally, the checksum.
Put the checksum in. It is the only integrity check stock offers, and the
field is optional in a place where it should not be.

![Stock's Firmware Upgrade tab](../assets/factory/07-firmware-upgrade.png)

### From the command line

Stock has no `tpi-selfupdate` — that ships with this fork — but it does have
`tpi firmware`:

```console
$ scp tp2-bmc-firmware-ota-v2.20.0.tpu root@BMC:/mnt/sdcard/
$ ssh root@BMC 'tpi firmware --file /mnt/sdcard/tp2-bmc-firmware-ota-v2.20.0.tpu \
    --sha256 8380e98dffb1972da9c51ee06c31766a8d7cb8f22be05e1405bc1a629ec0cf17'
started transfer of 36.12 MiB..
Done
```

!!! danger "`Done` does not mean upgraded"
    It means *staged*. The board keeps running the old firmware, its uptime
    does not reset, and nothing appears in `dmesg`. It looks exactly like a
    failed upgrade, and on the first run here it was mistaken for one for ten
    minutes.

    What actually happened is visible in the flash layout: a new UBI volume
    `rootfs_new` appears beside `rootfs`, and u-boot's boot target begins with
    `nextboot`. The image is written and armed.

    ```console
    $ ssh root@BMC reboot
    ```

## What it costs

Measured on the run described above:

| | |
|---|---|
| Transfer of 36.12 MiB | 26.6 s |
| Reboot, until the board answers again | 48 s |
| Compute modules disturbed | **none** |

That last row deserves a caveat rather than a promise. The board's network
switch is driven by the BMC, so a BMC reboot is expected to interrupt the
modules' links. On this run the reboot was quick enough that four modules —
running Kubernetes, one of them a control-plane node — were never marked
unhealthy, and a public service in front of them answered every probe
throughout. **A slower board, or a busier cluster, may not be so lucky.** Do
not plan on zero disruption; plan on a minute of it and be pleased.

## Going back

After the upgrade the flash holds `rootfs` and `rootfs_prev`, and
`rootfs_prev` is **the stock image your board shipped with**. Returning to
stock is a boot away, not a re-flash.

!!! warning "That is true for exactly one upgrade"
    The next upgrade overwrites `rootfs_prev` with the version you are leaving.
    After it, the rollback slot holds *this fork's* previous release, and
    getting back to stock means flashing a stock `.tpu` again.

For the longer route, stock's own releases are already a configured source in
this fork's Firmware Upgrade page, listed under *show older or unrelated
versions*. How Turing Pi publishes those, and why neither of their two routes
carries a checksum, is [its own
page](../reference/comparison.md).

## What the upgrade does not change

Your root password and your authorised keys survive: they live on the overlay
volume, which the upgrade does not touch. The hostname survives for the same
reason. Node power states are read from the hardware on start rather than
re-applied from a stale file, so modules are not power-cycled to suit the
daemon's memory of them.
