# 7a. Hardware presentation and cross-architecture apps

[Task index](../README.md#read-in-this-order)

**Optional after:** [storage and independent-boot acceptance](07-acceptance.md). Choose a section for your symptom; these changes are not prerequisites for recovery.

## Before you start

Complete storage recovery and export important data before optional hardware changes. A healthy pool does not verify sensors, DIMM topology, graphics or app compatibility. Use an authorized maintenance session and preserve the accepted boot overlay and configuration off the NAS.

The examples use the X570D4U-2L2T / Ryzen 5800X. The TS-877 examples describe QTS 5.2.10; for TS-873A / QTS 6.1, also apply the [release-specific checks](11-qts61-upgrade.md#5-compatibility-findings-and-fixes). The public profile is disabled by default and needs board-specific values. It does not discover those values for you.

## Custom enclosure previews

For a custom eight-bay enclosure on the TS-873A profile, follow the [chassis preview guide](12-custom-chassis-display.md). It covers artwork preparation, port and tray calibration, theme behavior, installation, verification and rollback without changing the hardware profile.

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

### Map real board sensors

SMBIOS type 38 identified a KCS interface at I/O address `0xca2`, with successive-byte register spacing. Read-only BMC queries were compared with the BMC sensor page. The accepted mapping on this board was:

| QTS field | Actual source | Example live reading |
|---|---|---|
| CPU temperature | Native `k10temp` / QTS `DTS:1` | 66°C |
| System temperature | BMC motherboard sensor 49 (`0x31`) | 47°C |
| System fan 1 | BMC FAN2, sensor 97 (`0x61`) | 1500 RPM |
| System fan 2 | BMC FAN3, sensor 98 (`0x62`) | 2100 RPM |

These are sampled values, not constants. BMC fan readings use a factor of 100 on this host, matching QTS's IPMI fan interpretation. Sensor numbers, scaling, labels and KCS addresses must be re-established on another board or after relevant firmware changes.

A small local Python adapter implements only the sensor-read subset needed by QTS. Its `ipmitool` entry point accepts `raw 0x04 0x2d` for the four explicitly allowed sensor IDs (49, 52, 97, 98); it is **not a general-purpose ipmitool**. It does not change PWM, fan mode, thresholds or BMC settings. It waits up to 0.5 seconds for the shared process lock so concurrent native temperature and fan readers can serialize. Each hardware transaction retains its three-second limit and refuses a busy KCS state or a newly present native kernel IPMI interface. It never resets KCS to recover a timeout. Direct KCS access is specific to this verified host; do not run an independent kernel/userspace KCS driver concurrently.

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

Preserve all unrelated model fields and disk mappings. QTS's `[Enclosure_0]` in `/etc/hal.conf` also needs matching `max_temp_num` and `max_fan_num` values. The monitoring daemon caches the model: changing the files or probing HAL alone does not prove that `/tmp/em/em_0.info` or the UI has updated. The current procedure may restart **only the hardware-monitor process**, through its standard `daemon_mgr` invocation, when those sensor settings change. It does not rescan storage or reboot the NAS. Do not probe `hal_daemon --help` as a read-only command: unsupported arguments can start or change the monitor.

The dashboard fix changes the recognized CPU-row condition to require a positive native `cpuTempC` value and removes the model-specific hiding class for that row. It only patches uniquely recognized old/new snippets in `qos-core-widget.js`; an unfamiliar widget is rejected. Refresh the browser cache if it still displays the old widget. No vendor JavaScript or compiled firmware is redistributed here.

### Verify fresh readings

Compare the dashboard with native CPU output and the BMC sensor page. Confirm the monitor is running and `/tmp/em/em_0.info` changes over successive samples. A cached temperature or green status icon does not prove a working sensor. Preserve independent BMC fan management; the adapter reads sensors and does not control cooling.

The legacy CPU-widget patch is only for a recognized 5.2 structure. QTS 6.1 already supplies a native CPU widget; leave it intact. [Chinese UI examples](screenshots.zh-CN.md#温度与风扇) show the actual before/after panel.

### Configure optional startup restoration

Use the optional package under `/qts-profile/mods` only after its individual modules pass preflight on your host. Source is in [tools/qts-mods](../tools/qts-mods/reconcile.py); [build_mod_overlay.py](../tools/build_mod_overlay.py) builds an overlay from a reviewed private base, host profile and locally obtained artwork. The package **does not install firmware, reboot the NAS, rebuild privilege rules, create caches or modify disk/pool mappings**.

The boot entry uses a bounded prerequisite wait with a 30-second settling check, performs one reconciliation pass and exits. There is no resident process or periodic mod watchdog. If configured, the MyQNAP module updates only the recognized existing metadata-refresh job; leave that module disabled if you do not use this repository integration.

| Module | Compatibility and recovery behavior |
|---|---|
| Sensors | Check host/KCS identity, exclusive access, real BMC/CPU readings and HAL symbols. Run native HAL probes in bounded subprocesses; after changes, compare HAL temperature/fan scaling with BMC and check the monitoring cache. Preserve unfamiliar/native IPMI tools. |
| CPU widget | Independently patch a uniquely recognized CPU-row condition and CSS class. Unknown UI structure is skipped even if sensor collection succeeds. |
| Memory | Match the configured physical bank/locator topology against fresh SMBIOS type-17 records and derive handle offsets. Restore only memory-model fields and stale DIMM cache sections, then verify HAL-populated sizes/offsets. |
| Cache candidates | Require the accepted eight-bay mapping; restore only the known port mask and verify it through HAL. Never select disks or create an SSD cache. |
| Artwork | Accept known vendor/prior asset hashes and expected IDs. The original front has six `hd` IDs plus two `ssd` IDs; the replacement has eight `hd` IDs. Unknown/new artwork is preserved and reported rather than overwritten. |
| MyQNAP index | Validate the local XML route, runtime dependencies and existing repository identity. Restore a missing known registration and replace/deduplicate only the known metadata cron entry, preserving unrelated jobs in both persistent and running crontabs. Fetch/validate a missing index when necessary; never install apps. |

The global gate checks host identity, protected boot/disk/network sections and PCI paths, then rechecks firmware identity before each module. Compatibility is based on the module's inspected structures and runtime checks, not a blanket promise for a version family. Unknown inputs are skipped. Fixed KCS addresses, sensor IDs and DIMM/cache layouts still need board-specific validation; changing the example profile alone is insufficient.

Each module backs up changed files in a root-only temporary directory, checks for concurrent changes and replaces files atomically. Verification failure rolls back its own changes, retains unrelated/concurrent changes, blocks that module for the rest of the boot and allows other modules to continue. DIMM rollback accounts for HAL's cache-population side effects. Sensor changes may restart only the hardware monitor; no whole-system restart is present.

The builder preserves early boot identity/geometry guards and protected disk/network sections. Review its output report: it replaces recognized legacy hooks and neutralizes optional memory/cache fields for checked restoration. Do not remove the existing boot guards or assume the runtime helper can repair a missing startup hook.

One summarized QTS System notification uses the **`[QTS Mods]`** prefix and lists each module's restored/OK/skipped outcome. Warnings identify incompatible or failed modules. Identical outcomes are suppressed within a boot. MyQNAP refresh failures preserve the last valid index and report failure/recovery separately. Notification rules and external recipients are not changed.

```text
/tmp/qts-mods/status.json       # Per-module results
/tmp/qts-mods-start.log         # Boot entry output
/tmp/qts-mods/backups/          # Runtime rollback copies; lost at reboot
```

On an adapted host with the package already installed, choose an existing Python runtime after verifying its required modules. Python paths differ by QTS release:

```sh
# Replace with the verified installed runtime path.
QTS_PYTHON=/REPLACE/VERIFIED/python
case "$QTS_PYTHON" in *REPLACE*) echo "Set the runtime path first"; exit 1;; esac
# Preflight: do not apply mod changes or fetch a missing index.
sudo "$QTS_PYTHON" /qts-profile/mods/reconcile.py --check
# Apply compatible modules once; no firmware installation or reboot.
sudo "$QTS_PYTHON" /qts-profile/mods/reconcile.py
```

The [example profile](../tools/qts-mods/profile.example.json) is disabled and incomplete. Keep the real profile private: populate exact protected model sections, board identity, PCI paths, known adapter hashes, physical DIMM locators, artwork hashes/IDs and the existing repository/cron definition. Vendor SVGs, firmware images, private identity and ready-to-flash host overlays are not distributed here. Build only after reviewing those inputs:

```sh
python3 tools/build_mod_overlay.py \
  --base private/boot-before.cpio.gz \
  --profile private/profile.json \
  --assets private/artwork \
  --output private/unified.cpio.gz
```

The builder writes a regular archive and review report; it never mounts or writes a boot device. Inspect the report, retain the old overlay off-device, and install through the identity, geometry and readback checks in [the build procedure](04-build-and-install.md). A file in `/tmp/qts-mods/backups/` is a runtime rollback copy, not a persistent backup.

### Recover a failed monitoring module

1. Read `/tmp/qts-mods/status.json` and `/tmp/qts-mods-start.log`. Preserve them before rebooting or retrying.
2. Check the registered monitor, actual process and fresh sensor cache together. `daemon_mgr` exit 0 or 1 alone is insufficient; the helper requires the requested state to be confirmed.
3. If a module is blocked after failure, inspect the cause and retained backup first. Do not clear failure markers or bypass compatibility checks merely to retry.
4. For an explicitly scoped sensor repair, run the installed reconciler with `--only-sensors --check` first. Apply with `--only-sensors` only after the mismatch is understood. Other optional modules remain untouched.
5. If updating an older unified archive, [patch_monitor_overlay.py](../tools/patch_monitor_overlay.py) replaces only the monitor reconciler and startup entry while preserving other members. Inspect its `--help`, build a new regular file, and use the same overlay backup/readback procedure.

The startup wait is bounded and skips unavailable prerequisites. Transaction failure restores that module's files before monitor recovery; unknown or concurrent changes are retained for review. If the monitor cannot recover, return to the accepted overlay and independent hardware monitoring rather than repeatedly restarting services.

![CPU, memory slots and SATA temperatures on QTS 5.2](../assets/screenshots/hardware-status-native-en.jpg)

*This English capture predates board-sensor integration. Its System temperature field does not describe the later adapter's capability.*

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

The TS-877 front image depicts six large bays and two smaller bays. An eight-SATA-bay map can therefore produce misleading highlights. Changing the entire model profile merely to obtain another picture could change unrelated hardware behavior.

For the 5.2 reference profile, **TS-873A front artwork** from the matching official `TS-X73A_20260731-5.2.10.3577` package supplied eight large bays. Extract artwork locally without installing another model's firmware. No vendor SVGs or firmware binaries are redistributed in this repository.

Under `/home/httpd/v3_menu/layout/`, the local replacements were:

| Source artwork | Existing target resource |
|---|---|
| `ts_873a_0.svg` | `ts_877_0.svg` |
| `TS-873A.svg` | `TS-877.svg` |
| `NAS-873A-G.svg` | `NAS-877-G.svg` |

Back up the actual target files and inspect any `model_0.svg` symlink first. Check that the front SVG contains the expected `hd_0` through `hd_7` elements and verify every populated slot's highlight against the already-accepted HAL map. Slots 7 and 8 were explicitly checked here. The device remains a TS-877 profile; only front/static artwork changed, not rear views, SATA mapping or physical chassis identity.

### Chassis artwork before and after

| Original TS-877 artwork | Patched eight-large-bay artwork |
|---|---|
| <img src="../assets/screenshots/chassis-artwork-before.png" width="230" alt="Original chassis drawing with six large bays and two smaller bays"> | <img src="../assets/screenshots/chassis-artwork-after.png" width="230" alt="Patched chassis preview with eight large bays"> |

*The original welcome-screen drawing and the adapted Storage & Snapshots preview are from different pages. Compare the bay arrangement, not page layout or scale. Verify selected slots against the HAL map after installation.*

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

Container layers and cross-platform packages can legitimately contain ARM binaries on an x86 system. Do not delete individual files from container layers. Keep unreadable or changing files in the audit's unresolved list; a partial scan cannot establish reclaimable space.

## Persist changes and verify them after boot

Editing `/etc/model.conf` or the live web root alone is insufficient on this RAM-root installation. The case's existing custom init copies a model profile out of its initramfs overlay; that source must be updated too. Web assets are extracted later, so the artwork helper waits for the actual target resources before copying the locally extracted replacements. Do not insert a late helper that blocks normal init indefinitely.

Keep the original boot guards, disk paths and unrelated-OS isolation intact. Before replacing an overlay, verify the boot disk's identity, size, partition geometry and device-mapper target; compare the old file's hash, retain a rollback copy, write a temporary file, read it back and rename it into place. Record the new hash privately. A whole-model rescan warning is not a successful acceptance result.

After installation, verify current readings, DIMM values, disk temperatures, highlights and cache-candidate eligibility. At the next planned reboot, repeat the checks and confirm the startup hook's status. Recheck after firmware or BIOS changes. If restoration skips an unknown structure, leave the vendor files intact and adapt the relevant module before enabling it again.

Keep credentials out of commands, logs and screenshots. Use existing authorized administrator access; passwordless sudo is not a prerequisite and no privilege-rule changes are part of this procedure.

## Validation scope

Reference-host live checks cover CPU/board/fan values, DIMM reporting, disk artwork and cache-candidate enumeration. Cache creation, ECC fault injection and thermal shutdown are not established by those checks. The repository tests use offline fixtures; final-package cold-boot and upgrade behavior require your own acceptance. See [reference results](case-study.md) for the boot/storage results separately.

**Related:** [custom chassis SVGs](12-custom-chassis-display.md) · [update and rollback checks](08-updates.md#persistent-adaptations-what-must-survive) · [troubleshooting](09-troubleshooting.md).
