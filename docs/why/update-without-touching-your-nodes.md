---
title: Update the BMC without touching your nodes
---

# Update the BMC without touching your nodes

This is the argument behind [Update the BMC without touching your nodes](../features/update-without-touching-your-nodes.md), with the measurements that back it. The feature page is the short version.

## Why upstream cycles them at all

Not out of malice: the daemon persisted each node's power state to a file and
re-applied it on start. A firmware upgrade restarts the daemon, the daemon
re-applies what the file says, and every module is switched to match — which
means off and on again, whatever it was doing.

The file is also the wrong source. It records what someone last asked for, not
what the hardware is doing, so after any disagreement the daemon confidently
restores a state that was never true.

## What happens instead

The daemon **reads the power state from the hardware on start** instead of
re-applying it from a file. There is nothing to restore, so nothing is
switched. A module that was running before the upgrade is still running
during and after it, with no interruption to its power.

Staging is separate from applying, too. Writing a new image arms the next
boot and changes nothing else; the board only moves when you reboot it. Right
up to that moment the whole thing is reversible with one `fw_setenv` — and
once it does move, [the image has to prove itself](../features/updates-that-undo-themselves.md)
before it is kept.

## Measured on a nine-node cluster

Board B was upgraded from stock firmware to this fork while its four modules
were running Kubernetes workloads, including an etcd member of the cluster's
control plane.

| | |
|---|---|
| Transfer of 36.12 MiB | 26.6 s |
| Reboot, until the board answered again | 48 s |
| Modules power-cycled | **0** |
| Nodes that went `NotReady` | **0** |

The honest detail: the network switch on the board *is* driven by the BMC, so
a BMC reboot does interrupt the modules' **links**, even though their power is
untouched — [the switch ports are visible per module](../reference/api/network.md)
if you want to watch it happen. On this run the reboot was quick enough that no node's kubelet
noticed. That is a property of the measurement, not a guarantee — a slower
boot could cross a readiness threshold, and this page says so rather than
claiming an isolation the hardware does not provide.

!!! warning "A prediction that was wrong, kept on the record"
    Before this upgrade the expectation written down was that four nodes would
    drop and etcd would fall to two of three members. None of that happened.
    The prediction is recorded on the ticket beside the result, because a
    project that only publishes its correct predictions is not measuring
    anything.
