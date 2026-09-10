# Updates that undo themselves

Upstream's firmware update promotes unconditionally. Reaching the end of the
boot proves the kernel started and that init got that far — it says nothing
about whether the machine is usable. Two images this fork built would have
passed that bar while being broken.

<figure markdown>
![The Firmware tab on board B, minutes after its first upgrade: the running slot, and the stock image it can fall back to sitting in the previous one.](../assets/fork/06-firmware-upgrade.png)
<figcaption>The Firmware tab on board B, minutes after its first upgrade: the running slot, and the stock image it can fall back to sitting in the previous one.</figcaption>
</figure>

The first could not link `bmcd`, so the web interface never came up. The second
silently lost the DSA switch driver from its kernel config, which leaves the
BMC perfectly reachable and **all four compute modules cut off the network**.
Once promoted, recovering from either needs physical access.

## What happens instead

A new image boots *tentatively*. Before anything is renamed, three questions
are asked:

1. Does the daemon answer on `https://127.0.0.1/`?
2. Does every compute module's switch port exist?
3. Is this the image that was staged, and does it serve metrics?

If any answer is no, the board reboots. That is the entire rollback: nothing
has been renamed yet, so U-Boot boots the volume still called `rootfs` — the
old image — and the `nextboot` variable that steered this boot is one-shot and
already consumed. The next boot has no `postupdate` in its command line, so
the gate does nothing and there is no loop.

A false rollback costs one extra BMC reboot. That does not power-cycle the
compute modules, so the cost of being wrong is small and the direction is
safe.

## It has actually said no

On 2026-09-09 a `v2.8.1-rc1` image was installed with its staged note tampered
to claim `v0.0.1`:

```
23:29:54 postupdate: tentative boot; checking this image before making it permanent
23:29:57 postupdate: bmcd answered after 3s
23:29:57 postupdate: switch ports present: node1 node2 node3 node4
23:29:57 postupdate: FAILED: staged v0.0.1 but this image reports v2.8.1-rc1
23:29:57 postupdate: rolling back to the volume named rootfs by rebooting
```

Back on the previous version in about 35 seconds, with the reason on disk.
Installed again untampered, the same image promoted. Every compute module's
uptime advanced by exactly the wall-clock duration of both reboots.

A gate that has never refused anything is an untested gate. This one has
refused, on purpose, and the record of every decision it has made is in
[the gate's record](../reference/gate-history.md).

## The third check exists because the first two are not enough

The first two prove the image is **alive**. Neither proves it is the image
anyone asked for. A build whose `/metrics` was completely broken would have
passed both, and so would an image whose version disagreed with what was
staged.

Two details the board taught while that check was being written, both of which
would have made it worse than useless:

**The gate may depend on nothing the board might not have.** When `/metrics`
still took a token, the first draft read that token from a file on the overlay
— which would have **rolled back every good image on a board that had never
minted one**. Since v2.15.0 `/metrics` is on its own listener and takes no
credential, so the check is one request to `127.0.0.1:9110`; the lesson
outlived the token.

**A staged note need not carry a version.** A hand-built image yields no tag,
and treating that as a mismatch would reject exactly the images most worth
testing. The version check is skipped, with the reason logged, and the metrics
check still has to pass.

Both were caught by a test suite before a flash, which is the argument for
[having one](https://github.com/excavador-turing/BMC-Firmware/blob/hive/tests/gate.sh).
It runs under the board's own shell, and four of its twelve cases assert a
**refusal** — a gate that cannot say no is not a gate.

## What it does not cover

The gate only helps an image that boots far enough to run it. One that hangs
earlier still needs power cut, which hard-cuts the compute modules. A hardware
watchdog is the fix and is not built yet.

And it is a question about the first ninety seconds, not a warranty. A board
that passed cleanly on 2026-09-09 went on to run out of memory four hours
later; see [what is and isn't fixed](../reference/known-faults.md).
