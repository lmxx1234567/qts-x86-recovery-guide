# 7a. Hardware presentation and cross-architecture apps

<!-- stage-navigation -->
[← Previous: Independent boot and acceptance](07-acceptance.md) · [Workflow index](../README.md#read-in-this-order) · [Next: Updates and rollback →](08-updates.md)
<!-- /stage-navigation -->

After storage acceptance, check the hardware pages separately. A recovered pool does not prove correct temperature reporting, DIMM topology, enclosure artwork or SSD-cache eligibility. The observations below apply to **QTS 5.2.10.3577 on the case X570D4U-2L2T / Ryzen 5800X**, using a TS-877 profile.

These fixes were verified in the running system on 2026-10-18 and saved into its boot overlay. **The revised overlay has not yet passed a reboot or cold-start test.** The earlier unattended reboot proves the original storage/boot setup, not these later changes. No cache was created and no application files were deleted.

## CPU, motherboard and fan readings

Two separate problems produced a dashboard with only a zero-valued system-temperature row:

- The TS-877 adaptation did not map the motherboard temperature or fans. The BMC already exposed real readings, but there was no usable native Linux IPMI device or `ipmitool` in this installation.
- The dashboard widget created its CPU row only for the `TS-X82` model family. A working native CPU sensor did not by itself make that row visible under this profile.

Read the native temperature sources before changing sensor counts:

```sh
for h in /sys/class/hwmon/hwmon*; do
    [ -d "$h" ] || continue
    cat "$h/name"
    for f in "$h"/temp*_label "$h"/temp*_input; do
        [ -f "$f" ] && { printf '%s: ' "$f"; cat "$f"; }
    done
done
```

The kernel exposes `k10temp` Tctl and Tccd1. CPU reporting uses QTS's existing `DTS:1` source, not a fabricated BMC replacement. Run `/sbin/get_cpu_temp` with appropriate privileges: an unprivileged zero did not establish a missing sensor. All eight SATA disks already provided their own temperatures; those sources were unchanged.

### Case-specific BMC integration

SMBIOS type 38 identified a KCS interface at I/O address `0xca2`, with successive-byte register spacing. Read-only BMC queries were compared with the BMC sensor page. The accepted mapping on this board was:

| QTS field | Actual source | Example live reading |
|---|---|---|
| CPU temperature | Native `k10temp` / QTS `DTS:1` | 66°C |
| System temperature | BMC motherboard sensor 49 (`0x31`) | 47°C |
| System fan 1 | BMC FAN2, sensor 97 (`0x61`) | 1500 RPM |
| System fan 2 | BMC FAN3, sensor 98 (`0x62`) | 2100 RPM |

These are sampled values, not constants. BMC fan readings use a factor of 100 on this host, matching QTS's IPMI fan interpretation. Sensor numbers, scaling, labels and KCS addresses must be re-established on another board or after relevant firmware changes.

A small local Python adapter implements only the sensor-read subset needed by QTS. Its `ipmitool` entry point accepts `raw 0x04 0x2d` for the four explicitly allowed sensor IDs (49, 52, 97, 98); it is **not a general-purpose ipmitool**. It does not change PWM, fan mode, thresholds or BMC settings. It uses a lock, a bounded transaction timeout and refuses a busy KCS transaction or a newly present native kernel IPMI interface. Direct KCS access is specific to this verified host; do not run an independent kernel/userspace KCS driver concurrently.

The resulting live sensor fields are:

```ini
[System Enclosure]
MAX_TEMP_NUM = 2
CPU_TEMP_UNIT = DTS:1
SYSTEM_TEMP_UNIT = IPMI:49
MAX_FAN_NUM = 2

[System FAN]
FAN_UNIT = IPMI
FAN_1 = I97
FAN_2 = I98
```

Preserve all unrelated model fields and disk mappings. QTS's `[Enclosure_0]` in `/etc/hal.conf` also needs matching `max_temp_num` and `max_fan_num` values. The monitoring daemon caches the model: changing the files or probing HAL alone does not prove that `/tmp/em/em_0.info` or the UI has updated. The current procedure may restart **only the hardware-monitor process**, through its standard `daemon_mgr` invocation, when those sensor settings change. It does not rescan storage or reboot the NAS. During diagnosis an unsupported `hal_daemon --help` invocation unexpectedly restarted the monitor; standard arguments were restored. Do not use daemon help probing as a read-only diagnostic.

The dashboard fix changes the recognized CPU-row condition to require a positive native `cpuTempC` value and removes the model-specific hiding class for that row. It only patches uniquely recognized old/new snippets in `qos-core-widget.js`; an unfamiliar widget is rejected. Refresh the browser cache if it still displays the old widget. No vendor JavaScript or compiled firmware is redistributed here.

### Lightweight automatic recovery after an update

The installed overlay now starts a **one-shot check**, not a resident daemon or scheduled task. It waits at most ten minutes for QTS prerequisites, waits another 30 seconds for startup to settle, then checks once and exits. It never downloads firmware or initiates a reboot.

Before writing, the check requires all of the following:

- The verified motherboard identity/KCS layout and native CPU source, valid real sensor readings, and no competing native IPMI device.
- QTS 5.2 and exact approved hashes for the HAL/INI libraries, hardware monitor, monitor launcher and Python runtime. A newer release is accepted only if these dependencies still match; changed binaries require review, not automatic allowlist expansion.
- Recognized model/HAL sensor fields and unique widget patterns. It refuses an unknown or vendor-supplied `ipmitool` rather than overwriting it.
- Stable files and firmware identity across preflight checks. A firmware version change during the same boot is not patched concurrently with the update.

Only after these checks can it restore the adapter, sensor fields and widget. Changed files are backed up in a root-only temporary directory and replaced atomically. Verification failure restores files still owned by the attempted patch, blocks further automatic repair for that boot and reports the failure. Monitor restart is bounded; no disk, RAID, pool or fan-control commands are part of this repair. The boot overlay keeps the pre-sensor model profile and applies sensor changes **after** compatibility checks; it does not unconditionally inject sensor settings or replace a future native IPMI tool before checking it.

Failures appear through QTS's native `notice_log_tool`, under the **`[Sensor Repair]`** prefix, as System-facility warnings for the administrators group. Notification records were written and read back. External delivery or pop-ups depend on existing QTS notification rules; no rules were changed. Repeated identical status is suppressed within the boot. The status file and boot output are:

```text
/tmp/qts-sensor-check/status.json
/tmp/qts-sensor-start.log
```

On the adapted host, an operator can run a read-only compatibility check:

```sh
sudo /usr/local/bin/python /qts-profile/sensor-check/check.py --check
```

The scripts are host-specific installed artifacts, not commands available on a stock QTS installation. This chapter documents the implementation; it is not a universal auto-installer. The temporary backups disappear at reboot; retain the separate boot-overlay backups off-device too.

**Validation:** twelve offline tests covered idempotence, preservation of storage/network sections, rejection of unfamiliar inputs, native-tool preservation, same-boot firmware drift, successful application and failure rollback. Live preflight passed; repeated checks reported no further changes. The actual one-shot entry point completed and exited. CPU, motherboard and both fan rows were visible, and arrays remained complete (`[UU]`, `[UUU]`) with the pre-existing resync continuing. No reboot or firmware upgrade was performed to validate this new hook.

**Limit:** if an updater removes the custom overlay or its boot-loader hook entirely, the check cannot run or notify. It protects only the sensor adaptation, not the other modifications listed in the [update audit](08-updates.md#existing-modification-audit). Successful runtime checks do not establish unattended-upgrade safety.

The following earlier hardware-page capture shows the CPU, DIMMs and disk temperatures; it predates the later motherboard/fan dashboard repair:

![CPU, 64 GB memory, four DIMM slots and eight disk temperatures](../assets/screenshots/hardware-status-native-en.jpg)

## Memory: 0 B in QTS while Linux sees 64 GB

Read `/proc/meminfo` and `dmidecode -t 16 -t 17` with sufficient privileges. The physical setup has four sockets across two channels, with two 32 GiB Micron ECC UDIMMs operating at 3200 MT/s. Linux saw the memory, but the adaptation profile still declared one channel and one slot without a working DIMM source. QTS consequently showed `0 B (63 GB usable)` and an invalid slot/channel label.

The native HAL supports SMBIOS reads using `DIMM_ACCESS = DMI`. The verified configuration was:

```ini
[System Memory]
MAX_CHANNEL_NUM = 2
MAX_SLOT_NUM = 4
DIMM_ACCESS = DMI
SLOT1_ADDR = 1-1, 0x0
SLOT2_ADDR = 1-2, 0x2
SLOT3_ADDR = 2-1, 0x5
SLOT4_ADDR = 2-2, 0x7
```

Here the first pair is the one-based channel/DIMM label. The hexadecimal value is an **offset from the first type-17 SMBIOS handle**, not an I2C address in this DMI mode. This BIOS reported handles `0x17`, `0x19`, `0x1c`, `0x1e`; subtracting `0x17` gives `0`, `2`, `5`, `7`. Re-derive these from your firmware. A BIOS change can invalidate the offsets even if the DIMMs have not moved.

Back up `/etc/platform.conf` before invalidating only stale `[DIMM n]` sections; do not overwrite its platform identity or other sections. Let HAL repopulate the records, then refresh Hardware Information. The verified result was **64 GB (63 GB usable), four slots, empty / 32 GB / empty / 32 GB**, with ECC/UDIMM labels. The QTS decoder still displays manufacturer `Unknown`, although SMBIOS identifies Micron. This verifies reporting, not an ECC fault-injection test.

## Eight large bays: artwork is separate from disk mapping

The TS-877 front image depicts six large bays and two smaller bays. Our eight disks were correctly enumerated as ordinary SATA bays, but two highlights did not match that drawing. Changing the entire model profile merely to obtain another picture could change unrelated hardware behavior.

Instead, we used the **TS-873A front artwork**, which has eight large bays side by side, from the official `TS-X73A_20260731-5.2.10.3577` firmware. This was local resource extraction, not installation of another model's firmware. No vendor SVGs or firmware binaries are redistributed in this repository.

Under `/home/httpd/v3_menu/layout/`, the local replacements were:

| Source artwork | Existing target resource |
|---|---|
| `ts_873a_0.svg` | `ts_877_0.svg` |
| `TS-873A.svg` | `TS-877.svg` |
| `NAS-873A-G.svg` | `NAS-877-G.svg` |

Back up the actual target files and inspect any `model_0.svg` symlink first. Check that the front SVG contains the expected `hd_0` through `hd_7` elements and verify every populated slot's highlight against the already-accepted HAL map. Slots 7 and 8 were explicitly checked here. The device remains a TS-877 profile; only front/static artwork changed, not rear views, SATA mapping or physical chassis identity.

![All eight disks in Storage & Snapshots](../assets/screenshots/eight-disks-native-en.jpg)

![Eight-bay front preview and selected disk details](../assets/screenshots/eight-bay-preview-native-en.jpg)

The `Free` label in the disk list means QTS has not allocated those disks; **bays 6–8 still contain unrelated data and are not safe to initialize**.

## SSD-cache candidates: a slot capability bitmap

An empty cache wizard was traced to `SYSTEM_DISK_CACHEABLE_BITMAP = 0x0`, despite QTS identifying SSDs. In this firmware the bitmap describes **eligible enclosure port/slot IDs**, not SSD serial numbers. With verified slots numbered 1–8:

```ini
[System Enclosure]
SYSTEM_DISK_CACHEABLE_BITMAP = 0x1FE
```

`0x1FE` sets bits 1 through 8. The running HAL value is `[Enclosure_0] cache_port_bitmap` in `/etc/hal.conf`; it must agree with the model after refresh. Back up both files before a live change. Do not transplant this mask onto a different numbering scheme or expose the boot SSD as a data/cache candidate.

The wizard then listed disks again: the pool members were In Use, and the Intel SSDs in slots 6 and 7 appeared as candidates. HDD rows may also be listed; that does not make an HDD eligible for SSD caching. The bitmap only removes a port restriction—disk type, health and existing allocation still matter. No disk was selected and the wizard was cancelled. **Cache operation, performance and data safety were not tested.** Qtier's SSD tier remains real pool storage, separate from this feature.

![SSD-cache wizard with zero disks selected](../assets/screenshots/cache-candidates-native-en.jpg)

## ARM64 apps: preserve data, inventory before cleanup

The old NAS used ARM64 while the new host is x86-64. An ARM64 executable cannot run natively as an x86-64 QPKG executable. However, architecture alone does not explain every missing App Center entry: registration, enable state, package availability and version compatibility also need checking. Restored pool data does not establish successful app migration. QNAP's [supported migration guidance](https://www.qnap.com/en-us/how-to/faq/article/i-bought-a-new-qnap-nas-how-do-i-move-my-data-over-from-the-old-one) applies to compatible appliances, not this generic host.

A read-only audit should:

1. Keep a private copy of `/etc/config/qpkg.conf`. Compare each registered `Install_Path`, resolved to its real path, with the existing `.qpkg` directories on every relevant volume.
2. Label unmatched directories as **unregistered legacy candidates**, not proven previously enabled apps. Old versions and duplicate directories can exist.
3. Inspect regular files' ELF headers without executing them. Honor the ELF endianness byte; `e_machine` is at bytes 18–19: 183 is AArch64, 40 is ARM, 62 is x86-64. Skip symlinks and deduplicate hard-linked inodes within each app.
4. Report ELF logical bytes separately from whole-directory bytes, compressed archives, data and models. Record permission errors or files disappearing during the scan. Logical sizes are not a promise of reclaimable physical space.
5. Back up app data/configuration before installing a compatible x86-64 package and testing its own restore procedure. Do not simply re-enable the old ARM package or bulk-delete `.qpkg`.

The case scan found **18 unregistered directories totaling about 10.25 GiB**, of which **1.44 GiB** was ARM64 ELF content. Registered Container Station also contained about 972 MiB of ARM64 files in container layers; another registered package bundled a cross-platform ARM64 binary. Those are not automatically obsolete files. Do not delete individual files from container layers. One Container Station read error limited that part of the scan; the remaining app scans had no read errors. All app data and binaries were retained. The full path/file inventory stays private.

## Persist changes and verify them after boot

Editing `/etc/model.conf` or the live web root alone is insufficient on this RAM-root installation. The case's existing custom init copies a model profile out of its initramfs overlay; that source must be updated too. Web assets are extracted later, so the artwork helper waits for the actual target resources before copying the locally extracted replacements. Do not insert a late helper that blocks normal init indefinitely.

Keep the original boot guards, disk paths and unrelated-OS isolation intact. Before replacing an overlay, verify the boot disk's identity, size, partition geometry and device-mapper target; compare the old file's hash, retain a rollback copy, write a temporary file, read it back and rename it into place. Record the new hash privately. A whole-model rescan warning is not a successful acceptance result.

In this case the new overlay was read back successfully and the artwork helper was manually tested. Both data arrays remained complete (`[UU]`, `[UUU]`). The later sensor-check overlay was also backed up and hash-verified on the dedicated boot device. **A future authorized reboot still needs to verify the sensor-check hook, CPU/motherboard/fan readings, DIMM values, all disk temperatures, bay highlights and cache candidate list again.** Recheck these after firmware or BIOS updates too.

Administrative access was verified through SSH and `sudo -n`. Keep credentials out of commands, logs and screenshots. Passwordless administrator access is not required to follow this guide; it was an operator choice in this case, and its reboot persistence was not tested. No sudoers rule or private account details are included here.

---

<!-- stage-navigation -->
[← Previous: Independent boot and acceptance](07-acceptance.md) · [Workflow index](../README.md#read-in-this-order) · [Next: Updates and rollback →](08-updates.md)
<!-- /stage-navigation -->
