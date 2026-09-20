# Developing

Three repositories build one image. This page is the loop between changing a
line and seeing it on a board — including the shortcut that skips the release
cycle entirely.

!!! warning "This is written from one board"
    Every timing and every failure mode below was measured on a single Turing
    Pi 2. Treat the numbers as orders of magnitude, not specifications.

## What builds what

| repository | produces | how the firmware consumes it |
|---|---|---|
| [`bmcd`](https://github.com/excavador-turing/bmcd) | the daemon | Buildroot fetches a **commit** archive and vendors its crates |
| [`BMC-UI`](https://github.com/excavador-turing/BMC-UI) | a tarball | pinned by **release URL** and sha256 |
| [`BMC-Firmware`](https://github.com/excavador-turing/BMC-Firmware) | `.tpu` and `.img` | this is the thing you flash |

So a bmcd change reaches a board only after the firmware re-pins its commit —
and re-pinning means recomputing a hash. That is the slow path, and most of
this page is about not taking it.

Why it is arranged this way — one daemon, one bundle, which listener serves
what, and what was declined — is written down in the firmware repository's
[architecture note](https://github.com/excavador-turing/BMC-Firmware/blob/hive/docs/architecture.md),
with the board measurements the decisions rest on.

## The full build

The firmware builds inside a pinned container. Nothing outside it is used, so
your host toolchain does not matter.

```console
$ docker build -t buildroot_local:latest .
$ docker run --rm -v "$PWD:/work" -w /work \
    -e BR2_DL_DIR=/work/dl -e BR2_CCACHE_DIR=/work/.ccache \
    buildroot_local:latest \
    bash -c '/work/scripts/configure.sh && /work/scripts/build.sh --release local'
```

Expect **around 100 minutes cold** — no `dl/`, no ccache, and Buildroot
compiles its own toolchain first. With both caches warm it drops to roughly a
fifth of that. Keep `dl/` and `.ccache` between runs; they are the difference
between a coffee and an afternoon.

Output lands in `dist/`:

```
tp2-bmc-firmware-ota-local.tpu       the OTA package
tp2-bmc-firmware-sdcard-local.img    a recovery SD image
```

### Building one package

```console
$ /work/scripts/build.sh --package bmcd-source
```

`--package` passes the target straight to Buildroot, so any package target
works. `<pkg>-source` fetches and vendors without compiling, which is how you
recompute a hash (below).

## Iterating without a release

Pinning bmcd by commit means a one-line change normally costs: commit, push,
tag, wait for a release, re-pin, recompute a hash, rebuild the firmware. For
day-to-day work, override the source instead.

Buildroot reads `buildroot/local.mk` for overrides. The build container
mounts this repository's parent read-only at `/src`, so a sibling checkout is
reachable as `/src/<repo>`:

```make
BMCD_OVERRIDE_SRCDIR = /src/bmcd
BMCD_OVERRIDE_SRCDIR_RSYNC_EXCLUSIONS = --exclude target --exclude .git

BMC_UI_OVERRIDE_SRCDIR = /src/BMC-UI/dist
```

An override **rsyncs that tree** in place of the pinned archive and builds
into a separate `bmcd-custom` directory. No commit, no tag, no hash.

!!! warning "The two packages want different things"

    **`bmcd` is source.** Buildroot compiles it, so the override is the
    repository root — and `target/` must be excluded. It is tens of gigabytes
    of host-architecture build output, and rsync fails partway through
    `target/debug/incremental` anyway, because Cargo is rewriting it while the
    copy runs.

    **`bmc-ui` is not source.** Its pinned download is a release tarball of
    the *built* interface, and the package's install step copies the source
    directory straight into `/srv/bmcd/www/`. So the override is `dist/`, and
    you run `npm run build` in BMC-UI yourself first.

    Point the interface override at the repository instead and `node_modules`
    lands in the web root — the build then fails on x86-64 `.node` binaries
    being installed into an ARM image, which is a confusing way to be told
    you pointed at the wrong directory.

!!! danger "`RSYNC_EXCLUSIONS` takes rsync flags, not names"

    Buildroot drops that variable into the `rsync` command **verbatim**, so it
    has to carry the `--exclude` itself. Write `target .git` and rsync reads
    them as two more *source* paths, the exclusion never happens, and the copy
    quietly becomes the whole tree — tens of gigabytes, with no error to tell
    you why the build is suddenly slow.

    The tell is a build that goes silent with nothing burning CPU. Look at the
    process list inside the container (`docker top <name> -o cmd`) and read
    the rsync invocation; it shows exactly what it was given.

!!! tip "A host path will not work"

    `/home/you/src/bmcd` is a path in *your* shell, not in the container. An
    override naming one fails with `ERROR: <path> does not exist`, from
    inside, where that path genuinely does not.

!!! danger "A bad build leaves its mess in the next one"

    Buildroot's `target/` tree is built up in place, and nothing sweeps it
    between builds. A package that installed the wrong files once keeps them
    there until you remove them by hand, so the *next* build — with the
    override corrected — still ships them.

    The symptom is a rootfs several times the slot size. One wrong interface
    override put 406 MB of *repository* into `/srv/bmcd/www`, and the
    following build produced a 206 MB rootfs against a 46 MB slot. Nothing in
    the log mentioned the earlier mistake.

    Clear the files the package installed and the stamps that say it is
    already installed:

    ```sh
    rm -rf buildroot/output/target/srv/bmcd/www
    rm -f  buildroot/output/build/bmc-ui-*/.stamp_target_installed
    ```

    When in doubt about which package is responsible, the size is the clue:
    compare the rootfs against the slot before you go looking anywhere else.

!!! warning "Do not start a build over a running one"

    A second build entering the same `output/` tree while the first is still
    writing fails in a way that reads like nothing happened. `rm -rf` on the
    package directory reports **Directory not empty**, the `&&` chain gives
    up, and the log the new build would have written is never created.

    If your status check then greps that log with stderr discarded, it finds
    no `BUILD_RC` line and reports a build still in progress — for a build
    that never began. Check for a running container first, and treat a
    missing log as a failure, not as patience.

!!! danger "Remove `local.mk` before computing any hash"
    With an override in place, the hash you compute describes whatever happened
    to be on your workstation — not the pinned archive. Every hash in
    `tp2bmc/package/*/` is computed with `local.mk` **removed**. This is
    written down because it has been got wrong.

## The fast loop: upload, then install

Even an overridden build is a full firmware build. The genuinely fast path
uses the board's own catalogue:

1. Build a `.tpu` locally.
2. Upload it to the SD card through the web interface, or drop it in the
   firmware directory on the card.
3. It appears as a candidate under the **SD card** source, alongside anything
   from GitHub.
4. Install it from the version list, then reboot.

The board treats a local file exactly like a release, with one deliberate
difference: it is marked **unverified**, because a file's provenance is
whatever put it there. A GitHub release is `verified` — its checksum was
published and checked on download.

## The A/B update, and what actually protects you

`/sbin/osupdate` writes a new root filesystem into a second UBI volume and arms
a **one-shot** `nextboot`. On the next boot `S99postupdate` decides whether to
keep it.

The gate is four questions:

- does bmcd answer `https://127.0.0.1/`?
- do all four node switch ports exist?
- is the running version the one the staged note recorded?
- does `/metrics` answer on `127.0.0.1:9110`?

All pass, and the volumes are renamed — the new image becomes permanent. Any
fails, and the board reverts.

**Rollback is a plain reboot.** There is no recovery menu and nothing to press:
the one-shot flag is already spent, so booting again lands on the old image.

!!! warning "The gate cannot see a regression"
    It checks that the daemon is *alive*, that the image is the one that was
    staged and that its metrics answer — not that any of it is *correct*. A
    build whose fan control is wrong or whose page is mangled passes all four
    and gets promoted. Health gating protects against a brick, not against a
    bug.

The log survives at `/mnt/overlay/postupdate.log` — read it after any upgrade
that behaved oddly.

## Things about the board worth knowing before you debug on it

- `/mnt/overlay` is **shared by both A/B images**. A value one image writes,
  the other reads. That is deliberate for settings and a trap for anything you
  assumed was per-image.
- The root filesystem is **erofs, read-only**. Only the overlay persists.
- `/var/log` is a **tmpfs** — logs do not survive a reboot.
- There is roughly **116 MB of RAM** and `/tmp` is a 58 MB tmpfs.
- There is **no `jq`, no `python3`, no `strings`**. Shell tooling is awk and
  sed. Scripts that ship on the board are written to that constraint.

## The interface's API types come from the daemon

`BMC-UI` does not hand-write the types for what the board sends. They are
generated from the OpenAPI document a bmcd release publishes, committed as
`src/lib/api/schema.d.ts`, and refreshed with `npm run api:refresh` after
moving the version in `bmcd-release.txt`. CI regenerates and fails on any
difference.

That pin should name the same bmcd release the firmware pins. If they diverge,
the interface is typed against an API the board does not serve — which
compiles, and is exactly the failure the generation exists to prevent.

Only the types are generated. The query hooks are written by hand, because
which endpoint may throw into a suspense boundary is a decision, not a detail.

## The command line

`tpi` ships both inside the firmware and as a workstation binary, from one
source with different feature sets. The on-board build carries `localhost`,
which points it at `127.0.0.1` and skips authentication; the workstation build
authenticates.

Because a workstation `tpi` updates on its own schedule and a board's does not,
being a release behind is normal. Commands that need a newer daemon say so:

```console
$ tpi firmware list
this board runs bmcd 2.7.0; `tpi firmware list` needs 2.8.0 or newer --
upgrade the firmware first (`tpi firmware check`)
```

`tpi firmware check` exits **10** when an upgrade exists, so it is usable from
cron without parsing its output.
