# See what the board sees

The Turing Pi 2 has a temperature sensor. Upstream's device tree never
described it, so nothing could read it — and the fan, having nothing to
regulate against, ran at a fixed speed somebody had once written down.

This fork adds the sensor to the device tree and lets the kernel's thermal
governor drive the fan from it. That is a two-line change with a consequence
worth an article: the board became explicable.

## "Why is the fan on 4?"

That question is what started this. A fan control showing `4` with no
explanation reads as *someone set this to 4*, and the honest answer is that
nobody did — the governor did, and it was right.

The governor is `step_wise`. The device tree declares five trip points, and
the fan's step follows the highest `active` trip the board is above:

| trip | temperature | fan step |
|---|---|---|
| `fan_min` | 20 °C | 3 |
| `fan_low` | 45 °C | 4 |
| `fan_mid` | 60 °C | 5 |
| `fan_high` | 70 °C | 6 |
| `hot` | 95 °C | kernel escalation |

So a board sitting at 50 °C is on step 4 because it is above 45 and below 60.
There was never a mystery — only a number with its reason removed.

The daemon now reports the trips it read from sysfs, and both clients say
which one is in force:

```console
$ tpi thermal
bmc-thermal    50.0 C
               above the 45 C trip
pwm-fan        step 4 of 6  (40% duty)
```

The 40% is not step 4 of 6 as a fraction. It is the PWM duty that step
commands, read from the board's own `cooling-levels` table — which is
`0, 16, 32, 64, 102, 170, 254` and is not linear. An interface that divided
4 by 6 and said 67% would be inventing a number about hardware it had not
looked at.

## Read from the board, never written into a client

Every figure above is read at runtime: the trips from `/sys/class/thermal`,
the duty table from the device tree, the step from the cooling device. None
of it is a constant in the daemon or the web interface.

That rule costs a little code and buys the only property that matters here —
the numbers cannot go stale relative to the board they describe. A table
copied into a client is correct until someone changes the device tree, and
then it is a confident lie.

## Thirty-one families

Upstream exposes no metrics at all. This fork serves 31 Prometheus families:
temperatures and the cooling state, per-port switch traffic and errors, node
power and uptime, NAND wear, memory and load, the clock's discipline and
offset, the firmware slots, and the health gate's own record.

They are scraped with **a token that cannot touch `/api/bmc`**. Adding metrics
behind the root password would have been worse than having none — a scrape
config is a file on another machine, and it should not be able to power off a
node.

!!! note "One of these is about this fork's own mistakes"
    `bmcd_process_resident_bytes` was added on 2026-09-09, the night a board
    ran out of memory and stopped answering. The board-level memory metric
    could show *that* it was being consumed and not *by what*, so the
    diagnosis had to be argued from timing. One number closes that gap. See
    [what is and isn't fixed](../reference/known-faults.md).
