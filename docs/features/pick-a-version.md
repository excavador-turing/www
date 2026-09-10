# Pick a version, from anywhere

Upstream's board has one firmware source, hard-coded, and it disagrees with
itself. Its firmware mirror stops at **v2.0.5** while its GitHub releases reach
**v2.1.0** — the same publisher, two catalogues, and following the documented
update path would *downgrade* a board running anything newer.

<figure markdown>
![Every configured source, side by side: this fork, upstream's two catalogues, and the SD card — with each candidate's checksum state, and an honest error where a source had nothing.](../assets/cards/card-versions.png)
<figcaption>Every configured source, side by side: this fork, upstream's two catalogues, and the SD card — with each candidate's checksum state, and an honest error where a source had nothing.</figcaption>
</figure>

This fork makes the sources a setting, and shows you what each one offers.

## Every source, with what it is worth

A source is GitHub releases, an HTTP directory, or a path on the SD card. Each
candidate is listed with two independent facts:

**How it compares** to what is running — newer, current, older, or genuinely
not comparable. Compared numerically, because `"2.10.0" < "2.9.0"` as text and
that bug is invisible until the tenth minor release. A release candidate sorts
before its own release, which GNU `sort -V` gets backwards.

**How much is known about it**, which is a different question:

| trust | means |
|---|---|
| `verified` | the publisher shipped a checksum and it was checked on download |
| `tls-only` | the publisher ships no checksums at all — upstream's HTTP mirror does not |
| `unverified` | a local file, whose provenance is whatever put it there |

Three genuinely different things. Rendering them alike would be worse than
omitting the column.

## An upload is a file, not an event

Uploading a firmware image used to *be* the install: the daemon wrote it to a
scratch directory, ran the updater on it immediately, and deleted the
directory. So an upload was never a thing you *had*, only a thing that
*happened* — and the upload form was a second way to install that bypassed the
version list entirely. Somebody could upload one image and install another
with the page never showing which.

Now an upload **parks**: the image is written to the SD card and nothing else
happens. It appears in the list beside every other candidate, marked
`unverified` because that is what a file of unknown provenance is, and
installing it is a separate and visible choice.

That also makes the development loop honest. Park a build, install it, reboot,
park the next one — each step is a thing you did, not a side effect.

## What a source cannot do

A source that is unreachable reports **its own error**, next to its own name.
It never blanks the others, and an error is never rendered as "nothing new" —
those are different claims, and only the person reading knows which one they
are about to act on.

The catalogue answers from cache and re-polls behind the answer, so pressing
*Check now* does not freeze the page while four sources are contacted. Before
that change it took **16 seconds** and held a lock the whole time, which froze
every other request as well.

## From the shell, too

Everything above is on the command line, because a feature that exists only in
a browser is shipped to the half of the workflow that cannot be automated:

```console
$ tpi firmware list
running v2.9.2
staged  v2.10.0  (reboot to take it)

VERSION    SOURCE  TRUST       SIZE
= v2.9.2   local   unverified  37.2 MB
^ v2.10.0  fork    verified

$ tpi firmware check || echo "there is an upgrade"
```

`firmware check` exits **10** when an upgrade exists, so it works from cron
without parsing output. It is deliberately not `1`, which stays "the command
failed".
