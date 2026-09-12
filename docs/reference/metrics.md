# Metrics

Upstream's firmware exposes no metrics. This fork serves **40 families**
at `/metrics`, in Prometheus text format.

This page is generated from the daemon's source, so it cannot describe a metric
the daemon does not emit. The authority is always the board:

```console
$ curl -s http://<board>:9110/metrics
```

## Its own port, and no credential

`/metrics` is served on **port 9110**, plain HTTP, and takes no credential.

That is a change from earlier releases, which put it on `:443` beside the API
behind a token of its own. The token existed for one reason: so that a
credential sitting in a scrape config could not also reach `/api/bmc` and
power four compute modules off. On a listener that serves nothing but
`/metrics` there is nothing else to reach, so the property survives and the
mechanism is a port instead of a secret — one fewer thing to mint, store,
rotate and leak.

The TLS went with it. It was always scraped with verification disabled,
because the board's certificate is expired and carries no subject-alternative
name, so nothing could verify it. Unverified TLS is a handshake per scrape on
a Cortex-A7 in exchange for nothing.

What protects the endpoint is the network. It binds the same address as the
API, so restricting the daemon to a management network restricts both. And
there is nothing secret in it: temperatures, fan steps, port counters, power
state, NAND wear and slot versions.

!!! note "On a board older than v2.15.0"
    `/metrics` is on `:443` and wants a token, which `tpi metrics show`
    printed. That command is gone, along with the token; if you are scraping
    an older board, keep the old config until you update it.

A Grafana dashboard over every family below ships with each release; see
[monitor it](../guides/monitor-it.md).

## Scraping it

```yaml
scrape_configs:
  - job_name: turingpi-bmc
    static_configs:
      - targets: ["<board>:9110"]
        labels:
          instance: <the board's hostname>
```

!!! note "The `instance` label is yours, not the board's"
    The board's exposition carries **no** `instance` label and no hostname —
    190 lines, and its own name appears in none of them. The labels it emits
    are `device`, `kind`, `name`, `node`, `port`, `result`, `sensor`, `slot`,
    `state`, `version` and `volume`.

    So `instance` is whatever your scraper assigns, and the example above
    assigns it deliberately. **Renaming a board moves no history**; editing
    that label moves all of it. Both boards here were renamed on 2026-09-11
    and not one series moved.

    This page said the opposite until then, as did `tpi hostname` and the
    API's own description of the endpoint (SQU-191). The claim was written
    from a worry rather than from the exposition, and a confident wrong
    warning is worse than none: it makes a safe rename look dangerous, and
    implies that leaving the name alone protects a history that the scrape
    config alone decides.

## The families

### The daemon

| metric | type | what it is |
|---|---|---|
| `bmcd_build_info` | gauge | Version of the daemon that produced these metrics. Always `1`; the answer is in the `version` label. |

Read this one first when a number looks wrong. Every other family below is
produced by the daemon this names, and a metric that does not exist in an older
build is simply absent rather than zero.

## Temperature and cooling

| metric | type | what it is |
|---|---|---|
| `bmcd_cooling_state` | gauge | Step a cooling device is currently at. |
| `bmcd_cooling_state_max` | gauge | Highest step a cooling device accepts. |
| `bmcd_cooling_overridden` | gauge | 1 while a fan is held at a step and its zone's governor is paused. |
| `bmcd_temperature_celsius` | gauge | Temperature reported by a kernel thermal zone. |

## The switch

| metric | type | what it is |
|---|---|---|
| `bmcd_switch_port_link` | gauge | Whether a switch port has carrier. |
| `bmcd_switch_port_present` | gauge | Whether the kernel has a netdev for this switch port. |
| `bmcd_switch_port_rx_bytes_total` | counter | Bytes received on a switch port. |
| `bmcd_switch_port_rx_errors_total` | counter | Receive errors on a switch port. |
| `bmcd_switch_port_speed_bits_per_second` | gauge | Negotiated line rate of a switch port. |
| `bmcd_switch_port_tx_bytes_total` | counter | Bytes transmitted on a switch port. |
| `bmcd_switch_port_tx_errors_total` | counter | Transmit errors on a switch port. |

## Compute modules

| metric | type | what it is |
|---|---|---|
| `bmcd_node_power_on_seconds` | gauge | Seconds since a compute module was powered on. |
| `bmcd_node_power_state` | gauge | Whether a compute module is powered on. |
| `bmcd_node_usb_boot_armed` | gauge | 1 when a module's USB-boot pin is asserted, which stops it booting from its own eMMC. |
| `bmcd_usb_config` | gauge | The board's persisted USB multiplexer configuration, labelled with its node, mode, route and bus type. |

!!! warning "The one to put a rule on"
    `bmcd_node_usb_boot_armed` is the only reading here that describes a
    **trap rather than a state**. Flashing a module leaves the board's
    persisted configuration at `Flashing(nodeN, …)`, and the daemon re-applies
    it on every start — which holds that module's USB-boot pin high and stops
    it booting from its own eMMC.

    The module carries on running, because it is already booted. The failure
    arrives at its *next* reboot, which can be weeks later, and it looks like
    dead hardware: nothing at all on the serial console, not even a bootloader
    banner, because the loader does not use the console; nothing on the
    network; and the board still reporting the rail on. `tpi usb status`
    cannot tell you either — it prints the same route for a normal
    configuration and for this one.

    So alert on **duration**, not on the state. Flashing a module is a
    legitimate thing to be doing; a module still armed fifteen minutes later
    is a forgotten `tpi usb device -n N`, and the page reaches whoever armed
    it while they still remember.

    ```yaml
    - alert: ModuleLeftArmedForUsbBoot
      expr: bmcd_node_usb_boot_armed == 1
      for: 15m
      annotations:
        summary: "{{ $labels.node }} will not boot from its own eMMC - run `tpi usb device`."
    ```

    The family is four samples rather than one because a single "which node"
    gauge cannot say *none*, and none is the normal answer.

## The BMC itself

| metric | type | what it is |
|---|---|---|
| `bmcd_load1` | gauge | 1-minute load average of the BMC. |
| `bmcd_load15` | gauge | 15-minute load average of the BMC. |
| `bmcd_load5` | gauge | 5-minute load average of the BMC. |
| `bmcd_memory_available_bytes` | gauge | Memory available to a new allocation on the BMC, reclaim included. |
| `bmcd_memory_free_bytes` | gauge | Free memory of the BMC. |
| `bmcd_memory_total_bytes` | gauge | Total memory of the BMC. |
| `bmcd_process_resident_bytes` | gauge | This daemon's own resident set. Board memory says the board is being consumed; only this says by whom. |
| `bmcd_process_threads` | gauge | Threads this daemon has. Read beside the resident set: a heap leak grows memory with this flat, while a leaked task or an unreaped blocking thread grows both, because every thread carries a stack. |
| `bmcd_uptime_seconds` | gauge | Seconds since the BMC booted. |

## The certificate it is serving

| metric | type | what it is |
|---|---|---|
| `bmcd_tls_certificate_expiry_timestamp_seconds` | gauge | When the certificate the listener is serving expires. |
| `bmcd_tls_certificate_info` | gauge | The key behind that certificate, in a `key` label. Always `1`; the answer is the label. |

Both describe the **running listener**, not whatever is on disk now. They are
read once, when the certificate is read, which is at start — so replacing the
file and not restarting is exactly the case where a fresh read would lie, and
these keep telling you what the board is actually presenting.

Alert on the expiry with a long fuse. A board whose certificate has expired
still serves, but nothing that verifies can reach it, and the recovery needs a
hand on the board.

## NAND

| metric | type | what it is |
|---|---|---|
| `bmcd_nand_available_bytes` | gauge | Unallocated space on the BMC's NAND. |
| `bmcd_nand_eraseblock_size_bytes` | gauge | Size of one logical eraseblock of the BMC's NAND. |
| `bmcd_nand_eraseblocks` | gauge | Eraseblocks of the BMC's NAND, by what UBI counts them as. |

## Clock

| metric | type | what it is |
|---|---|---|
| `bmcd_clock_offset_seconds` | gauge | The BMC's system clock minus true time; negative when the board is behind. |
| `bmcd_clock_stratum` | gauge | Stratum of the time source the BMC is synchronised to. |
| `bmcd_clock_synchronised` | gauge | Whether the BMC's system clock is disciplined. Absent when that cannot be determined. |
| `bmcd_rtc_info` | gauge | A real-time clock the kernel registered on the BMC. |
| `bmcd_rtc_present` | gauge | Whether the BMC has a real-time clock at all. |

## Firmware

| metric | type | what it is |
|---|---|---|
| `bmcd_firmware_promotion_total` | counter | Boots that ran the firmware health gate, by what the gate decided. `promoted` is derived as attempts minus rollbacks, because the gate has no single line meaning `kept`; a board cut off mid-gate therefore counts as promoted. |
| `bmcd_firmware_last_promotion_timestamp_seconds` | gauge | When the firmware health gate last decided, so a dashboard can say *when* and not only how often. Absent rather than wrong when the board's clock cannot be trusted: the gate records the board's own time, which on a BMC that has just come up may be well before the real one, and only UTC is accepted. |
| `bmcd_firmware_slot_info` | gauge | A firmware slot on the BMC's NAND. The rollback slot is not mounted, so it has no version. |
| `bmcd_firmware_slot_size_bytes` | gauge | Size of the firmware in a slot. |
| `bmcd_firmware_update_staged` | gauge | Whether a firmware update is staged for the next boot. Absent when the U-Boot environment cannot be read. |

!!! note "A gauge that is absent is not a zero"
    Several of these are omitted rather than sent as `0` when the board cannot
    answer: `bmcd_clock_synchronised` on a board with no chrony,
    `bmcd_firmware_update_staged` when the boot environment cannot be read,
    `bmcd_process_resident_bytes` on a kernel without `/proc/self/statm`,
    `bmcd_process_threads` on one without `/proc/self/status`.
    An absent series means *not known*; a zero would be a claim.
