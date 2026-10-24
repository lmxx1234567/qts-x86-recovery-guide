# Reference hardware and validation scope

[Task index](../README.md#read-in-this-order)

**Reference only:** use the [task index](../README.md#read-in-this-order) for procedures; this result summary is not an installation sequence.

Use these results to choose a starting point, not as a compatibility list. Your own installation must pass the [acceptance checklist](../templates/acceptance.md). The reference recovery used a complete healthy disk set; it is not a repair recipe for missing members or damaged Qtier metadata.

## Hardware and storage layout

| Component | Reference configuration |
|---|---|
| Board / CPU / memory | ASRock Rack X570D4U-2L2T, Ryzen 5800X, 64 GiB ECC UDIMM |
| Dedicated boot | Samsung 980 500 GB NVMe; boot/firmware only |
| Original Qtier set | Two 4 TB SATA SSDs in RAID1 and three 8 TB SATA HDDs in RAID5 |
| Other storage | Three unrelated disks, excluded from QTS pool configuration |
| Bays | Eight populated SATA positions with successful HAL reverse queries |
| 5.2 baseline | TS-877 / TS-X77, 5.2.10.3577 build 20260731, kernel 5.10.60-qnap |
| 6.1 baseline | TS-873A / TS-X73A, 6.1.0.3640 build 20261007, kernel 6.6.129-qnap |

The two identical SSDs' physical 4/5 labels remained ambiguous; successful logical HAL queries do not resolve that physical-label uncertainty. Re-establish each position from labels/cables on your hardware.

## Validated results

| Area | Result | Scope |
|---|---|---|
| 5.2 lab | Native 5.1.6 → 5.2.10 update, initialization and repeated disk-only cold starts; 1 MiB file hash retained | Disposable VM |
| 6.1 lab | Same-family X73A 5.2.10 → 6.1 update and disk-only cold start; 32 MiB file hash retained | Disposable static volume, not Qtier |
| Boot preservation | Examined updates retained EFI/GRUB/support files and layout; both firmware slots changed | Exact tested builds and base layout |
| Physical 5.2 recovery | Old configuration returned automatically; complete SSD RAID1 and HDD RAID5, both volumes accessible; unattended reboot passed | No manual initialize or attach action |
| Physical 6.1 migration | Offline boot-image family change with SATA disconnected, followed by recovery of the same five-disk pool | Not an online native cross-family update |
| Qtier | 18.17 TB pool; 3.63 TB SSD tier and 14.54 TB HDD tier, Ready/Idle with automatic tiering | Status and sample readability checks |
| Hardware | CPU, motherboard and fan readings; 64 GiB/four-slot memory report; eight-bay artwork and cache candidates | Live checks, not thermal shutdown, ECC injection or cache-operation tests |
| Custom chassis | Transparent front/rear SVG delivery, native slot-protocol checks and guard idempotence | Current-state checks; startup/update persistence needs acceptance |

## Boundaries that matter for recovery

- No pre-migration hash baseline exists for the sampled physical files. The 5.2 full-file reads and 6.1 partial reads establish readability, not a complete integrity comparison.
- Physical unattended reboot was tested for the original storage setup. The final monitoring/chassis packages were checked live and offline; their complete cold-boot and firmware-upgrade paths are outside that validation.
- Scheduled automatic firmware installation, boot-SSD tail as data storage and future releases are unvalidated. Use [per-release gates](08-updates.md) before changing versions.
- Unrelated disks were not selected for QTS configuration, but an intermediate boot into their previous OS could have imported them. Disconnect unrelated storage when possible; do not infer zero writes from an unselected QTS disk list.
- ARM app directories surviving recovery do not prove x86 app compatibility. Preserve data and follow the [application inventory procedure](07a-hardware-and-apps.md#arm64-apps-preserve-data-inventory-before-cleanup).

## Apply the results

Start with [inventory](01-inventory.md), build a [disposable VM](03-vm-validation.md), and validate [every bay](05-bay-mapping.md) before storage startup. After recovery, export data and test [independent boot](07-acceptance.md). Optional [hardware](07a-hardware-and-apps.md) and [chassis](12-custom-chassis-display.md) changes come last.

**Related:** [preview gallery](screenshots.md) · [dependency sources](sources.md) · [acceptance checklist](../templates/acceptance.md).
