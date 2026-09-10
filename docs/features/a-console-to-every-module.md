# A console to every module

Every compute module on a Turing Pi 2 has a serial console, and reaching it
used to mean a USB adapter and three jumper wires onto the board's header. The
BMC is already wired to all four. This fork puts them in the browser.

<figure markdown>
![Node 1's console in the browser, opened on its recent scrollback — a Talos node mid-boot, not a blank terminal.](../assets/fork/07-console.png)
<figcaption>Node 1's console in the browser, opened on its recent scrollback — a Talos node mid-boot, not a blank terminal.</figcaption>
</figure>

Four tabs, one per module. No adapter, no header, nothing on the desk.

## It shows you what happened before you opened it

A console that starts blank is almost useless for the thing consoles are for.
A module panics at three in the morning; you open the tab at nine and the
terminal is empty, because a WebSocket only carries what arrives after you
join.

The daemon keeps a **16 KiB ring buffer per module**, and has all along. The
console now asks for it on open and writes it into the terminal before
attaching to the live stream, so the tab opens on the last few pages of that
module's output rather than on nothing.

From a shell the same buffer is one request:

```console
$ tpi uart -n 2 get
```

## Two ways to type, and they are not the same

This is the distinction worth knowing, because picking the wrong one produces
a console that appears broken.

**The terminal** sends what you type, exactly as typed. Ctrl-C, tab
completion and the arrow keys all reach the module. Click into it and it
behaves like a terminal, because that is what it is.

**The REST writer** — `tpi uart -n 2 set --cmd "…"`, or the same endpoint from
a script — always appends CRLF. That makes it a fine way to send a command
from a shell script and a bad way to answer a boot prompt: it cannot send a
bare control character, so there is no Ctrl-C and no tab completion through it.

One is for a person at a prompt. The other is for a script sending whole
lines. Neither is a worse version of the other.

## "Reader: running" is about the BMC, not the module

The console reports the state of the daemon's own UART reader. It is easy to
read that as a statement about the module, and it is not one.

A module that is powered off, a module that booted and has gone quiet, and a
module part-way through boot all leave the reader in exactly the same state.
The reader is running; nothing is arriving. If you want to know whether the
module is alive, the node's power state and its switch port say so, and this
line does not.

!!! note "Why the buffer is 16 KiB and not larger"
    It lives in the BMC's RAM, and the BMC has 116 MB of it with no swap. Four
    modules at 16 KiB is 64 KiB, which is free; four at a megabyte is a
    meaningful fraction of a board that has already died twice this year from
    running out of memory.

    Keeping a longer history means writing it somewhere, and the overlay is
    UBI on a NAND with five free eraseblocks. Sending the lines off the board
    with `syslogd -R` is the answer that scales, and it is
    [one line of configuration](../reference/known-faults.md).
