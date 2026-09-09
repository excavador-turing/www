# Metrics

Upstream's firmware exposes no metrics. This fork serves **34 families**
at `/metrics`, in Prometheus text format.

This page is generated from the daemon's source, so it cannot describe a metric
the daemon does not emit. The authority is always the board:

```console
$ curl -sk -u metrics:$TOKEN https://<board>/metrics
```

## The credential

`/metrics` takes a token of its own — **not** the root password:

```console
$ tpi metrics show
username  metrics
token     <32 hex characters>
```

That token answers `/metrics` with 200 and `/api/bmc` with **401**, verified
from off-board. The distinction is the point: a scrape config is a file on
another machine, and it should not be able to power off a node or stage
firmware.

Unlike `/api/bmc`, `/metrics` has **no loopback exception**. It demands the
credential even from the board itself, which is the behaviour the rest of the
API should have and does not — see
[what is and isn't fixed](known-faults.md).

Rotate it with `tpi metrics rotate`; the previous token stops working
immediately, which is the entire point of rotation.

A Grafana dashboard over every family below ships with each release; see
[monitor it](../guides/monitor-it.md).

## Scraping it

```yaml
scrape_configs:
  - job_name: turingpi-bmc
    scheme: https
    tls_config:
      insecure_skip_verify: true   # until the certificate is real; see known-faults
    basic_auth:
      username: metrics
      password: <the token>
    static_configs:
      - targets: ["<board>:443"]
        labels:
          instance: <the board's hostname>
```

!!! warning "The instance label follows the hostname"
    Renaming the board changes the `instance` label on every series, so a
    history does not follow it across the rename — and renaming back does not
    rejoin them. Both `tpi hostname` and the Settings tab say so before they
    do it.

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
