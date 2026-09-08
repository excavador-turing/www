# Contributing

The loop below is how every change in this fork was tested, including on the
day it was written. It builds locally and installs onto **your own board** —
no tag, no release, no twenty-minute CI round trip.

!!! danger "This flashes firmware onto hardware"
    A locally built image is **unverified by construction**: an override copies
    a working tree instead of downloading a checksummed release. That is the
    point for iteration and the reason it must never be released.

    The A/B health gate makes this far safer than it sounds — a bad image
    reboots back onto the previous one — but it cannot save an image that
    hangs *before* the gate runs. That still needs physical access.

    Put dev images on a board you can reach.

## Three repositories

| repo | what it is |
|---|---|
| [`BMC-Firmware`](https://github.com/excavador-turing/BMC-Firmware) | the image: Buildroot, kernel, device tree, `tpi-selfupdate` |
| [`bmcd`](https://github.com/excavador-turing/bmcd) | the daemon: the API and the board's hardware access |
| [`BMC-UI`](https://github.com/excavador-turing/BMC-UI) | the web interface, shipped as a tarball the firmware pins by hash |

Each carries `devbox.json` and a `Justfile`, so the setup is `direnv allow` and
then `just`.

## Before a pull request

Run what CI runs, rather than something like it:

=== "bmcd"

    ```console
    $ just check
    ```

    The six commands from `cargo_ci.yml`, in its order, verbatim — including
    the stubbed-HAL build that exists so the hardware-less path cannot rot.

=== "BMC-UI"

    ```console
    $ just check
    ```

=== "firmware"

    ```console
    $ just lint
    ```

## Testing a change on your board

The tiers differ by an order of magnitude, so pick the smallest one that
actually exercises what you changed.

### A shell script — seconds

`tpi-selfupdate` and the init scripts are shell. Copy one to the board and run
it from `/tmp`; nothing is installed and nothing is at risk.

```console
$ scp tp2bmc/board/tp2bmc/overlay/sbin/tpi-selfupdate root@BMC:/tmp/tsu
$ ssh root@BMC '/tmp/tsu --list --json'
```

### A daemon or interface change — about nine minutes

Build the image with your working trees substituted for the pinned releases.

```console
$ just dev-flash --bmcd ../bmcd --ui ../BMC-UI --host BMC
```

Measured end to end on a warm cache: **8m17s** to build, **5s** to upload,
**26s** to install. Against roughly 23 minutes of CI plus a tag and a release.

Then reboot when you are ready. The board decides whether to keep it.

!!! tip "Put the board back afterwards"
    A dev image reports `VERSION=local`, which is not a version. The update
    check cannot order it against real tags and says so — every release shows
    as *cannot be compared* rather than as an upgrade. That is correct, and it
    is also why a board should not be left on a dev build:

    ```console
    $ ssh root@BMC 'tpi-selfupdate --channel stable' && ssh root@BMC reboot
    ```

## Opening the pull request

Against `hive`, not `main` — `main` tracks upstream untouched.

What a reviewer looks for, in rough order of how often it is missing:

- **evidence, not intent.** "Verified on the board: …" beats "should work".
  Say what you ran and what it printed.
- **the failure path.** What happens with no network, no SD card, an older
  daemon? A feature that only works when everything works is half a feature.
- **why, in the commit message.** The code says what; the message is the only
  place the reasoning survives.

## Releasing

Maintainer only, and the order matters — the firmware pins the other two by
hash, so they release first:

1. **bmcd** — bump `Cargo.toml`, tag `vN.N.N`
2. **BMC-UI** — bump `package.json`, tag `vN.N.N`
3. **firmware** — re-pin both, recompute the bmcd cargo sum, tag

!!! warning "The cargo sum depends on the Rust toolchain, not just the commit"
    The vendored archive is named after the commit alone, so a stale one in
    `dl/` looks right and hashes wrong. The same commit produced two different
    sums under rust-bin 1.85.0 and 1.98.1. Recompute from a tree extracted
    *after* any toolchain bump, with `buildroot/local.mk` removed, and prove it
    with `make bmcd-source` before tagging.
