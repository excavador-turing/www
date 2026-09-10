import{t as e}from"./axios-Cwt1K6go.js";var t=Object.assign({"./fixtures/about.json":{response:[{result:{api:`1.1`,bmcd_version:`2.29.0`,board_model:`TuringPi2\0\0\0\0\0\0\0`,board_revision:`v2.5.2`,board_serial:`XZCT000000000`,build_version:`2.29.0`,buildroot:`2025.02.17`,buildtime:`2026-09-10 02:09:42-00:00`,hostname:`turingpi`,kernel:`6.12.109`,version:`v2.20.0`}}]},"./fixtures/captured.json":{captured_at:`2026-09-10T22:48:56Z`,firmware:`v2.20.0`,note:`Captured from a Turing Pi 2 running this firmware. Addresses, MAC, hostname and serial are replaced with documentation-range values; every measurement is the board's own.`},"./fixtures/cooling.json":{response:[{result:[{device:`system fan`,max_speed:6,overridden:!1,speed:4,zone:`thermal_zone0`}]}]},"./fixtures/firmware.json":`Ready`,"./fixtures/firmware_available.json":{response:[{result:{age_seconds:766,checked_at:`2026-09-10T22:36:14Z`,refreshing:!0,running:`v2.20.0`,sources:[{candidates:[{relation:`current`,trust:`verified`,version:`v2.20.0`},{relation:`older`,trust:`verified`,version:`v2.19.0`},{relation:`older`,trust:`verified`,version:`v2.18.0`},{relation:`older`,trust:`verified`,version:`v2.17.0`},{relation:`older`,trust:`verified`,version:`v2.16.0`},{relation:`older`,trust:`verified`,version:`v2.15.0`},{relation:`older`,trust:`verified`,version:`v2.14.0`},{relation:`older`,trust:`verified`,version:`v2.13.0`},{relation:`older`,trust:`verified`,version:`v2.12.0`},{relation:`older`,trust:`verified`,version:`v2.11.0`},{relation:`older`,trust:`verified`,version:`v2.10.0`},{relation:`older`,trust:`verified`,version:`v2.9.2`},{relation:`older`,trust:`verified`,version:`v2.9.1`},{relation:`older`,trust:`verified`,version:`v2.9.0`},{relation:`older`,trust:`verified`,version:`v2.8.1`},{relation:`older`,trust:`verified`,version:`v2.8.0`},{relation:`older`,trust:`verified`,version:`v2.7.0`}],id:`fork`,kind:`github`,label:`excavador-turing (this fork)`,location:`excavador-turing/BMC-Firmware`},{candidates:[],error:`/mnt/sdcard/firmware is not a directory`,id:`local`,kind:`local`,label:`SD card`,location:`/mnt/sdcard/firmware`},{candidates:[{relation:`older`,trust:`verified`,version:`v2.1.0`},{relation:`older`,trust:`verified`,version:`v2.0.5`},{relation:`older`,trust:`verified`,version:`v1.0.2`},{relation:`older`,trust:`verified`,version:`1.1.0`}],id:`turingpi`,kind:`github`,label:`Turing Pi (official releases)`,location:`turing-machines/BMC-Firmware`},{candidates:[{relation:`older`,trust:`tls`,version:`v2.0.5`},{relation:`older`,trust:`tls`,version:`v2.0.4`},{relation:`older`,trust:`tls`,version:`v2.0.3`},{relation:`older`,trust:`tls`,version:`v1.1.0`},{relation:`older`,trust:`tls`,version:`v1.0.2`},{relation:`older`,trust:`tls`,version:`v1.0.1`},{relation:`older`,trust:`tls`,version:`v1.0.0`}],id:`turingpi-http`,kind:`http`,label:`Turing Pi (firmware.turingpi.com)`,location:`https://firmware.turingpi.com/turing-pi2`}]}}]},"./fixtures/firmware_slots.json":{response:[{result:{last_promotion:{message:`metrics answer, with bmcd_build_info`,timestamp:`Thu Sep 10 19:49:35 UTC 2026`},nextboot:null,present:!0,promotion_history:{attempts:1,promoted:1,rolled_back:0},rollback:{size_bytes:39989248,version:null,volume:`rootfs_prev`,volume_id:1},running:{size_bytes:37879808,version:`v2.20.0`,volume:`rootfs`,volume_id:3},staged:null,update_staged:!1}}]},"./fixtures/firmware_sources.json":{response:[{result:{sources:[{enabled:!0,id:`fork`,kind:`github`,label:`excavador-turing (this fork)`,location:`excavador-turing/BMC-Firmware`},{enabled:!0,id:`local`,kind:`local`,label:`SD card`,location:`/mnt/sdcard/firmware`},{enabled:!0,id:`turingpi`,kind:`github`,label:`Turing Pi (official releases)`,location:`turing-machines/BMC-Firmware`},{enabled:!0,id:`turingpi-http`,kind:`http`,label:`Turing Pi (firmware.turingpi.com)`,location:`https://firmware.turingpi.com/turing-pi2`}]}}]},"./fixtures/flash.json":`Ready`,"./fixtures/health.json":{response:[{result:{clock:{measured_by:`chronyc tracking`,offset_seconds:36809e-9,rtc:[{device:`rtc0`,name:`rtc-pcf8563 0-0051`},{device:`rtc1`,name:`sun6i-rtc 7090000.rtc`}],source:`ntppool1.time.nl`,stratum:2,synchronised:!0},load:{fifteen_minutes:.24,five_minutes:.25,one_minute:.61,present:!0},memory:{available_bytes:85995520,free_bytes:46125056,present:!0,self_resident_bytes:20119552,self_threads:18,total_bytes:121839616},nand:{available_bytes:7618560,available_eraseblocks:60,bad_eraseblocks:0,eraseblock_size_bytes:126976,present:!0,reserved_eraseblocks:40,total_eraseblocks:2040},uptime_seconds:10787.97}}]},"./fixtures/hostname.json":{response:[{result:{hostname:`turingpi`,on_next_boot:`turingpi`}}]},"./fixtures/info.json":{response:[{result:{ip:[{device:`br0`,ip:`203.0.113.20`,mac:`00:00:5e:00:53:01`}],storage:[{bytes_free:144621568,name:`BMC`,total_bytes:144683008},{bytes_free:24521756672,name:`SD card`,total_bytes:31231758336}]}}]},"./fixtures/network.json":{response:[{result:{ports:[{duplex:`full`,kind:`node`,link:!0,name:`node1`,operstate:`up`,present:!0,rx_bytes:469869770,rx_errors:0,speed_mbps:1e3,tx_bytes:547460906,tx_errors:0},{duplex:`full`,kind:`node`,link:!0,name:`node2`,operstate:`up`,present:!0,rx_bytes:1408152810,rx_errors:0,speed_mbps:1e3,tx_bytes:198859925,tx_errors:0},{duplex:`full`,kind:`node`,link:!0,name:`node3`,operstate:`up`,present:!0,rx_bytes:94576712,rx_errors:0,speed_mbps:1e3,tx_bytes:72593889,tx_errors:0},{duplex:`full`,kind:`node`,link:!0,name:`node4`,operstate:`up`,present:!0,rx_bytes:240341028,rx_errors:0,speed_mbps:1e3,tx_bytes:224936750,tx_errors:0},{duplex:`full`,kind:`uplink`,link:!0,name:`ge0`,operstate:`up`,present:!0,rx_bytes:974463724,rx_errors:0,speed_mbps:1e3,tx_bytes:2160284719,tx_errors:0},{duplex:null,kind:`uplink`,link:!1,name:`ge1`,operstate:`lowerlayerdown`,present:!0,rx_bytes:0,rx_errors:0,speed_mbps:null,tx_bytes:0,tx_errors:0}]}}]},"./fixtures/node_info.json":{response:[{result:[{module_name:null,name:null,power_on_time:29696,uart_baud:null},{module_name:null,name:null,power_on_time:29696,uart_baud:null},{module_name:null,name:null,power_on_time:29696,uart_baud:null},{module_name:null,name:null,power_on_time:29696,uart_baud:null}]}]},"./fixtures/ntp.json":{response:[{result:{clock:{measured_by:`chronyc tracking`,offset_seconds:36742e-9,rtc:[{device:`rtc0`,name:`rtc-pcf8563 0-0051`},{device:`rtc1`,name:`sun6i-rtc 7090000.rtc`}],source:`ntppool1.time.nl`,stratum:2,synchronised:!0},configurable:!0,servers:[]}}]},"./fixtures/other.json":{response:[{result:[{api:`1.1`,buildroot:`2025.02.17`,buildtime:`2026-09-10 02:09:42-00:00`,ip:`203.0.113.20`,mac:`00:00:5e:00:53:01`,version:`v2.20.0`}]}]},"./fixtures/power.json":{response:[{result:[{node1:`1`,node2:`1`,node3:`1`,node4:`1`}]}]},"./fixtures/sdcard.json":{response:[{result:[{free:24521756672,total:31231758336,use:6710001664}]}]},"./fixtures/serial_status.json":[`Running`,`Running`,`Running`,`Running`],"./fixtures/thermal.json":{response:[{result:{cooling:[{cur_state:4,levels:[0,16,32,64,102,170,254],max_level:254,max_state:6,name:`pwm-fan`,present:!0}],sensors:[{name:`bmc-thermal`,present:!0,temperature_c:44.2,trips:[{index:0,kind:`active`,temperature_c:20},{index:1,kind:`active`,temperature_c:45},{index:2,kind:`active`,temperature_c:60},{index:3,kind:`active`,temperature_c:70},{index:4,kind:`hot`,temperature_c:95}]}]}}]},"./fixtures/uart_0.json":{response:[{uart:`[12779.654605] [talos] service[etcd](Running): Health check failed: context deadline exceeded\r
[12779.664447] [talos] removed static pod {"component": "controller-runtime", "controller": "k8s.StaticPodServerController", "id": "kube-scheduler"}\r
[12779.679100] [talos] removed static pod {"component": "controller-runtime", "controller": "k8s.StaticPodServerController", "id": "kube-apiserver"}\r
[12779.693732] [talos] removed static pod {"component": "controller-runtime", "controller": "k8s.StaticPodServerController", "id": "kube-controller-manager"}\r
[12784.655665] [talos] service[etcd](Running): Health check successful\r
[12784.665380] [talos] rendered new static pod {"component": "controller-runtime", "controller": "k8s.StaticPodServerController", "id": "kube-apiserver"}\r
[12784.680626] [talos] rendered new static pod {"component": "controller-runtime", "controller": "k8s.StaticPodServerController", "id": "kube-controller-manager"}\r
[12784.696860] [talos] rendered new static pod {"component": "controller-runtime", "controller": "k8s.StaticPodServerController", "id": "kube-scheduler"}\r
[12796.697471] [talos] deleted Talos API endpoint slices in Kubernetes {"component": "controller-runtime", "controller": "kubeaccess.EndpointController", "addressType": "IPv6"}\r
[12796.721113] [talos] no dangling Talos API endpoints in Kubernetes {"component": "controller-runtime", "controller": "kubeaccess.EndpointController"}\r
[12796.755267] [talos] deleted Talos API endpoint slices in Kubernetes {"component": "controller-runtime", "controller": "kubeaccess.EndpointController", "addressType": "IPv6"}\r
[12796.780252] [talos] no dangling Talos API endpoints in Kubernetes {"component": "controller-runtime", "controller": "kubeaccess.EndpointController"}\r
`}]},"./fixtures/uart_1.json":{response:[{uart:``}]},"./fixtures/uart_2.json":{response:[{uart:``}]},"./fixtures/uart_3.json":{response:[{uart:`[18945.844730] eth0: renamed from tmp536d2\r
[19245.500617] eth0: renamed from tmpebd31\r
[19545.486999] eth0: renamed from tmp07e88\r
[19593.543992] eth0: renamed from tmp0ed4f\r
[19593.817785] eth0: renamed from tmp6a638\r
[19845.488368] eth0: renamed from tmp71607\r
[20145.717686] eth0: renamed from tmp394aa\r
[20445.414294] eth0: renamed from tmp1f47b\r
[20565.453422] eth0: renamed from tmpb688c\r
[20745.380061] eth0: renamed from tmpeb1e7\r
[21045.403208] eth0: renamed from tmp8681c\r
[21345.489938] eth0: renamed from tmpb87c0\r
[21645.636781] eth0: renamed from tmpeeb56\r
[21945.308694] eth0: renamed from tmp6d1dc\r
[22245.356135] eth0: renamed from tmp34eff\r
[22545.287416] eth0: renamed from tmpc683b\r
[22845.552907] eth0: renamed from tmpd931b\r
[23145.232202] eth0: renamed from tmp4082a\r
[23445.591505] eth0: renamed from tmpb3407\r
[23745.270319] eth0: renamed from tmpa51e3\r
[24045.189940] eth0: renamed from tmp348d2\r
[24165.145291] eth0: renamed from tmpee7ce\r
[24345.588444] eth0: renamed from tmp99eb5\r
[24645.125022] eth0: renamed from tmp153b8\r
[24945.646803] eth0: renamed from tmp99161\r
[25245.082513] eth0: renamed from tmp02711\r
[25545.340867] eth0: renamed from tmp51cf1\r
[25845.335966] eth0: renamed from tmpe5a5e\r
[26145.299634] eth0: renamed from tmpcc6d9\r
[26444.986469] eth0: renamed from tmp5c2cf\r
[26745.021287] eth0: renamed from tmp3ff70\r
[27044.936526] eth0: renamed from tmp16c78\r
[27345.071576] eth0: renamed from tmp7b485\r
[27644.956012] eth0: renamed from tmpb6df2\r
[27765.346784] eth0: renamed from tmpf9d17\r
[27944.879073] eth0: renamed from tmp08c28\r
[28244.849440] eth0: renamed from tmp28a69\r
[28544.836591] eth0: renamed from tmpea3fc\r
[28845.112119] eth0: renamed from tmp4a423\r
[29145.135587] eth0: renamed from tmpceb0e\r
[29444.809484] eth0: renamed from tmp04f02\r
`}]},"./fixtures/update_check.json":{response:[{result:{checked_at:`2026-09-10T22:27:33Z`,edge:{channel:`edge`,repo:`excavador-turing/BMC-Firmware`,running:`v2.20.0`,target:`v2.20.0`,update_available:!1},error:null,stable:{channel:`stable`,repo:`excavador-turing/BMC-Firmware`,running:`v2.20.0`,target:`v2.20.0`,update_available:!1}}}]},"./fixtures/usb.json":{response:[{result:[{bus_type:`Usb hub`,mode:`Flash`,node:`Node 2`,route:`AlternativePort`}]}]}}),n=Object.assign({"./fixtures/metrics.txt":`# HELP bmcd_build_info Version of the daemon that produced these metrics.
# TYPE bmcd_build_info gauge
bmcd_build_info{version="2.29.0"} 1

# HELP bmcd_temperature_celsius Temperature reported by a kernel thermal zone.
# TYPE bmcd_temperature_celsius gauge
bmcd_temperature_celsius{sensor="bmc-thermal"} 46.6

# HELP bmcd_cooling_state Step a cooling device is currently at.
# TYPE bmcd_cooling_state gauge
bmcd_cooling_state{device="system fan"} 4

# HELP bmcd_cooling_state_max Highest step a cooling device accepts.
# TYPE bmcd_cooling_state_max gauge
bmcd_cooling_state_max{device="system fan"} 6

# HELP bmcd_cooling_overridden 1 when a cooling device is held at a step and its zone's governor is paused.
# TYPE bmcd_cooling_overridden gauge
bmcd_cooling_overridden{device="system fan"} 0

# HELP bmcd_switch_port_present Whether the kernel has a netdev for this switch port.
# TYPE bmcd_switch_port_present gauge
bmcd_switch_port_present{port="node1",kind="node"} 1
bmcd_switch_port_present{port="node2",kind="node"} 1
bmcd_switch_port_present{port="node3",kind="node"} 1
bmcd_switch_port_present{port="node4",kind="node"} 1
bmcd_switch_port_present{port="ge0",kind="uplink"} 1
bmcd_switch_port_present{port="ge1",kind="uplink"} 1

# HELP bmcd_switch_port_link Whether a switch port has carrier.
# TYPE bmcd_switch_port_link gauge
bmcd_switch_port_link{port="node1",kind="node"} 1
bmcd_switch_port_link{port="node2",kind="node"} 1
bmcd_switch_port_link{port="node3",kind="node"} 1
bmcd_switch_port_link{port="node4",kind="node"} 1
bmcd_switch_port_link{port="ge0",kind="uplink"} 1
bmcd_switch_port_link{port="ge1",kind="uplink"} 0

# HELP bmcd_switch_port_speed_bits_per_second Negotiated line rate of a switch port.
# TYPE bmcd_switch_port_speed_bits_per_second gauge
bmcd_switch_port_speed_bits_per_second{port="node1",kind="node"} 1000000000
bmcd_switch_port_speed_bits_per_second{port="node2",kind="node"} 1000000000
bmcd_switch_port_speed_bits_per_second{port="node3",kind="node"} 1000000000
bmcd_switch_port_speed_bits_per_second{port="node4",kind="node"} 1000000000
bmcd_switch_port_speed_bits_per_second{port="ge0",kind="uplink"} 1000000000

# HELP bmcd_switch_port_rx_bytes_total Bytes received on a switch port.
# TYPE bmcd_switch_port_rx_bytes_total counter
bmcd_switch_port_rx_bytes_total{port="node1",kind="node"} 469983478
bmcd_switch_port_rx_bytes_total{port="node2",kind="node"} 1408163680
bmcd_switch_port_rx_bytes_total{port="node3",kind="node"} 94654146
bmcd_switch_port_rx_bytes_total{port="node4",kind="node"} 240349428
bmcd_switch_port_rx_bytes_total{port="ge0",kind="uplink"} 974695587
bmcd_switch_port_rx_bytes_total{port="ge1",kind="uplink"} 0

# HELP bmcd_switch_port_tx_bytes_total Bytes transmitted on a switch port.
# TYPE bmcd_switch_port_tx_bytes_total counter
bmcd_switch_port_tx_bytes_total{port="node1",kind="node"} 547620369
bmcd_switch_port_tx_bytes_total{port="node2",kind="node"} 198959494
bmcd_switch_port_tx_bytes_total{port="node3",kind="node"} 72651910
bmcd_switch_port_tx_bytes_total{port="node4",kind="node"} 224990644
bmcd_switch_port_tx_bytes_total{port="ge0",kind="uplink"} 2160533345
bmcd_switch_port_tx_bytes_total{port="ge1",kind="uplink"} 0

# HELP bmcd_switch_port_rx_errors_total Receive errors on a switch port.
# TYPE bmcd_switch_port_rx_errors_total counter
bmcd_switch_port_rx_errors_total{port="node1",kind="node"} 0
bmcd_switch_port_rx_errors_total{port="node2",kind="node"} 0
bmcd_switch_port_rx_errors_total{port="node3",kind="node"} 0
bmcd_switch_port_rx_errors_total{port="node4",kind="node"} 0
bmcd_switch_port_rx_errors_total{port="ge0",kind="uplink"} 0
bmcd_switch_port_rx_errors_total{port="ge1",kind="uplink"} 0

# HELP bmcd_switch_port_tx_errors_total Transmit errors on a switch port.
# TYPE bmcd_switch_port_tx_errors_total counter
bmcd_switch_port_tx_errors_total{port="node1",kind="node"} 0
bmcd_switch_port_tx_errors_total{port="node2",kind="node"} 0
bmcd_switch_port_tx_errors_total{port="node3",kind="node"} 0
bmcd_switch_port_tx_errors_total{port="node4",kind="node"} 0
bmcd_switch_port_tx_errors_total{port="ge0",kind="uplink"} 0
bmcd_switch_port_tx_errors_total{port="ge1",kind="uplink"} 0

# HELP bmcd_node_power_state Whether a compute module is powered on.
# TYPE bmcd_node_power_state gauge
bmcd_node_power_state{node="node1"} 1
bmcd_node_power_state{node="node2"} 1
bmcd_node_power_state{node="node3"} 1
bmcd_node_power_state{node="node4"} 1

# HELP bmcd_node_power_on_seconds Seconds since a compute module was powered on.
# TYPE bmcd_node_power_on_seconds gauge
bmcd_node_power_on_seconds{node="node1"} 29712
bmcd_node_power_on_seconds{node="node2"} 29712
bmcd_node_power_on_seconds{node="node3"} 29712
bmcd_node_power_on_seconds{node="node4"} 29712

# HELP bmcd_uptime_seconds Seconds since the BMC booted.
# TYPE bmcd_uptime_seconds gauge
bmcd_uptime_seconds 10798.29

# HELP bmcd_load1 1-minute load average of the BMC.
# TYPE bmcd_load1 gauge
bmcd_load1 1.44

# HELP bmcd_load5 5-minute load average of the BMC.
# TYPE bmcd_load5 gauge
bmcd_load5 0.44

# HELP bmcd_load15 15-minute load average of the BMC.
# TYPE bmcd_load15 gauge
bmcd_load15 0.3

# HELP bmcd_memory_total_bytes Total memory of the BMC.
# TYPE bmcd_memory_total_bytes gauge
bmcd_memory_total_bytes 121839616

# HELP bmcd_memory_free_bytes Free memory of the BMC.
# TYPE bmcd_memory_free_bytes gauge
bmcd_memory_free_bytes 46460928

# HELP bmcd_memory_available_bytes Memory available to a new allocation on the BMC, reclaim included.
# TYPE bmcd_memory_available_bytes gauge
bmcd_memory_available_bytes 86331392

# HELP bmcd_process_resident_bytes This daemon's own resident set. Board memory says the board is being consumed; only this says by whom.
# TYPE bmcd_process_resident_bytes gauge
bmcd_process_resident_bytes 20119552

# HELP bmcd_process_threads Threads this daemon has. Read beside the resident set: a heap leak grows memory with this flat, while a leaked task or an unreaped blocking thread grows both, because every thread carries a stack.
# TYPE bmcd_process_threads gauge
bmcd_process_threads 20

# HELP bmcd_nand_eraseblocks Eraseblocks of the BMC's NAND, by what UBI counts them as.
# TYPE bmcd_nand_eraseblocks gauge
bmcd_nand_eraseblocks{state="total"} 2040
bmcd_nand_eraseblocks{state="available"} 60
bmcd_nand_eraseblocks{state="bad"} 0
bmcd_nand_eraseblocks{state="reserved"} 40

# HELP bmcd_nand_eraseblock_size_bytes Size of one logical eraseblock of the BMC's NAND.
# TYPE bmcd_nand_eraseblock_size_bytes gauge
bmcd_nand_eraseblock_size_bytes 126976

# HELP bmcd_nand_available_bytes Unallocated space on the BMC's NAND.
# TYPE bmcd_nand_available_bytes gauge
bmcd_nand_available_bytes 7618560

# HELP bmcd_rtc_present Whether the BMC has a real-time clock at all.
# TYPE bmcd_rtc_present gauge
bmcd_rtc_present 1

# HELP bmcd_rtc_info A real-time clock the kernel registered on the BMC.
# TYPE bmcd_rtc_info gauge
bmcd_rtc_info{device="rtc0",name="rtc-pcf8563 0-0051"} 1
bmcd_rtc_info{device="rtc1",name="sun6i-rtc 7090000.rtc"} 1

# HELP bmcd_clock_synchronised Whether the BMC's system clock is disciplined. Absent when that cannot be determined.
# TYPE bmcd_clock_synchronised gauge
bmcd_clock_synchronised 1

# HELP bmcd_clock_stratum Stratum of the time source the BMC is synchronised to.
# TYPE bmcd_clock_stratum gauge
bmcd_clock_stratum 2

# HELP bmcd_clock_offset_seconds The BMC's system clock minus true time; negative when the board is behind.
# TYPE bmcd_clock_offset_seconds gauge
bmcd_clock_offset_seconds 0.000036466

# HELP bmcd_firmware_promotion_total Boots that ran the firmware health gate, by what the gate decided. \`promoted\` is derived as attempts minus rollbacks, because the gate has no single line meaning \`kept\`; a board cut off mid-gate therefore counts as promoted.
# TYPE bmcd_firmware_promotion_total counter
bmcd_firmware_promotion_total{result="promoted"} 1
bmcd_firmware_promotion_total{result="rolled_back"} 0

# HELP bmcd_firmware_last_promotion_timestamp_seconds When the health gate last reached a verdict, in Unix seconds. Taken from the board's own clock at that moment, which on a BMC that had just come up may be behind true time; absent when the recorded timestamp cannot be read as UTC.
# TYPE bmcd_firmware_last_promotion_timestamp_seconds gauge
bmcd_firmware_last_promotion_timestamp_seconds 1789069775

# HELP bmcd_firmware_slot_info A firmware slot on the BMC's NAND. The rollback slot is not mounted, so it has no version.
# TYPE bmcd_firmware_slot_info gauge
bmcd_firmware_slot_info{slot="running",volume="rootfs",version="v2.20.0"} 1
bmcd_firmware_slot_info{slot="rollback",volume="rootfs_prev",version=""} 1

# HELP bmcd_firmware_slot_size_bytes Size of the firmware in a slot.
# TYPE bmcd_firmware_slot_size_bytes gauge
bmcd_firmware_slot_size_bytes{slot="running",volume="rootfs"} 37879808
bmcd_firmware_slot_size_bytes{slot="rollback",volume="rootfs_prev"} 39989248

# HELP bmcd_firmware_update_staged Whether a firmware update is staged for the next boot. Absent when the U-Boot environment cannot be read.
# TYPE bmcd_firmware_update_staged gauge
bmcd_firmware_update_staged 0

`})[`./fixtures/metrics.txt`]??``;function r(e){return t[`./fixtures/${e}.json`]}var i=120,a=`This is a demo. It reads from a captured board and cannot change anything.`;function o(t,n,r,a=`application/json`){return new Promise((o,s)=>{setTimeout(()=>{let i={data:r,status:n,statusText:n===200?`OK`:`Error`,headers:{"content-type":a},config:t,request:{}};n>=200&&n<300?o(i):s(Object.assign(new e.AxiosError(`demo: ${n}`,String(n),t,{},i),{response:i}))},i)})}function s(e){return{response:[{result:e}]}}var c=e=>{let t=(e.method??`get`).toLowerCase(),i=e.url??``,c=e.params??{};if(i.endsWith(`/bmc/authenticate`))return o(e,200,{id:`demo`,name:`User Session`,username:`root`});if(i.endsWith(`/bmc/serial/status`))return o(e,200,r(`serial_status`)??[]);if(i===`/bmc`||i.endsWith(`/bmc`)){let t=String(c.opt??``),n=String(c.type??``);if(t===`get`){let t=r(n===`uart`?`uart_${c.node??0}`:n);return t===void 0?o(e,200,s(`not captured for this demo: ${n}`)):o(e,200,t)}if(t===`set`)return o(e,200,s(a))}return i.endsWith(`/bmc/backup`)||i.includes(`/bmc/upload/`)?o(e,403,{type:`about:blank`,title:`This is a demo`,status:403,detail:a},`application/problem+json`):i.endsWith(`/metrics`)?o(e,200,n,`text/plain`):o(e,404,{type:`about:blank`,title:`Not in the demo`,status:404,detail:`${t.toUpperCase()} ${i} is not captured.`},`application/problem+json`)};function l(){let e=window.fetch.bind(window);window.fetch=async(t,n)=>{let r=new URL(typeof t==`string`?t:t instanceof URL?t.href:t.url,location.href);if(!r.pathname.includes(`/api/bmc`))return e(t,n);let i={};r.searchParams.forEach((e,t)=>{i[t]=e});let a=(n?.method??(t instanceof Request?t.method:`GET`)).toLowerCase(),o=r.pathname.replace(/^.*\/api/,``);try{let e=await c({url:o,method:a,params:i,headers:{}}),t=typeof e.data==`string`?e.data:JSON.stringify(e.data);return new Response(t,{status:e.status,headers:{"Content-Type":e.headers[`content-type`]}})}catch(e){let t=e.response;if(!t)throw e;return new Response(JSON.stringify(t.data),{status:t.status,headers:{"Content-Type":t.headers[`content-type`]}})}}}function u(){e.defaults.adapter=c,l();try{localStorage.setItem(`token`,`0123456789abcdef`.repeat(4)),localStorage.setItem(`username`,`root`)}catch{}}export{u as installDemo};