# The command line

`tpi` controls a board from a shell. Upstream ships it; this fork extends it to
reach the endpoints the fork added, which until **1.1.0** were reachable only
from the web interface.

That gap mattered more than it sounds. On a headless rack the CLI is what you
script and put in a runbook; the interface is what you open when you are
already looking at the machine. Shipping a feature to the browser alone means
shipping it to the half of the workflow that cannot be automated.

## What 1.1.0 adds

| command | what it does |
|---|---|
| `tpi firmware list` | every version this board could install, across all sources |
| `tpi firmware install <version>` | install one of them |
| `tpi firmware check` | is there anything newer |
| `tpi firmware sources` | where the board looks |
| `tpi about` | firmware, bmcd, kernel, board identity |
| `tpi thermal` | temperatures |
| `tpi metrics show \| rotate` | the read-only scrape credential |
| `tpi hostname [<name>]` | the board's name, live and after the next boot |
| `tpi ntp show \| set <servers…>` | the time sources, and how the clock is doing |
| `tpi config export \| import` | every setting on the board, as one file |

`tpi firmware --file X` still works and still means upload. It is upstream's
documented spelling and is already in people's scripts, so `firmware` grew
subcommands *around* it rather than replacing it.

## Listing and installing

```console
$ tpi firmware list
running v2.9.0

VERSION    SOURCE    TRUST       SIZE
= v2.9.0   fork      verified
v v2.8.1   fork      verified
v v2.8.0   fork      verified
^ v2.9.2   local     unverified  37.2 MB

^ newer   = running   v older   ? not comparable
```

The trust column is not decoration. **`verified`** means the release published
a checksum and it was checked on download. **`tls-only`** means the publisher
ships no checksums at all — upstream's HTTP mirror does not. **`unverified`**
is a local file, whose provenance is whatever put it there. Three genuinely
different things, and rendering them alike would be worse than omitting the
column.

```console
$ tpi firmware install v2.9.2 --yes
Done
staged v2.9.2; reboot to take it

$ tpi firmware list
running v2.9.0
staged  v2.9.2  (reboot to take it)
```

The version is resolved **against the catalogue** before anything is posted, so
a version no source offers fails immediately rather than half-way through a
download. If two sources offer the same version, it names them and asks rather
than guessing.

## Exit codes that mean something

```console
$ tpi firmware check
v2.9.0 is current

$ echo $?
0
```

When there is something newer it names it and exits **10** instead:

**10** means an upgrade exists, so `tpi firmware check || notify-me` works from
cron without parsing output. It is deliberately not `1`, which stays "the
command failed".

!!! danger "Every one of these was broken until 1.2.2"
    The commands on this page were written, documented and released **without
    ever being run against a board**. The response unwrapper returned the API's
    wrapper array instead of the result inside it, and since every command
    begins by reading `about` to check the daemon's version, every command
    failed.

    The examples above are now output captured from a real board. The ones that
    were here before were not, and one of them described a command
    (`firmware install`) that had never worked in any release. See
    [what is and isn't fixed](known-faults.md).

## Two builds, one source

`tpi` ships twice, and the difference is worth knowing before you wonder why
the one on the board never asks for a password.

| | on the board | on your workstation |
|---|---|---|
| arrives via | a firmware upgrade | a release binary or the AUR |
| features | `localhost,native-tls` | default |
| talks to | `127.0.0.1` | whatever you point it at |
| authentication | **skipped** — it is already root-local | prompts, then caches a token |
| version vs bmcd | always matched; they ship together | floats independently |

## Being a release behind is normal

Because the workstation copy updates on its own schedule, it will regularly be
older or newer than the board it is pointed at. That used to produce:

```
Invalid `type` parameter firmware_available
```

which names the query parameter `tpi` sent and tells you nothing. Now each
command asks the board its version first:

```console
$ tpi firmware list
this board runs bmcd 2.7.0; `tpi firmware list` needs 2.8.0 or newer --
upgrade the firmware first (`tpi firmware check`)
```

!!! note "Why the comparison is numeric"
    As text, `"2.10.0" < "2.9.0"` — so a string compare would tell a board on
    2.9.0 that it satisfied a 2.10.0 requirement, and it would then fail with
    exactly the unreadable error the gate exists to remove. There is a test
    that asserts this, because the bug is invisible until the tenth minor
    release.

## Installing

Release binaries are built for five targets — Linux (x86-64, aarch64), macOS
(Intel and Apple silicon) and Windows — on the
[releases page](https://github.com/excavador-turing/tpi/releases).

The copy on the board needs nothing: it arrives with the firmware.
