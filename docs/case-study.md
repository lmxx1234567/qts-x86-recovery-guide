# Case study: one successful x86 Qtier recovery

## Later 6.1 milestone (2026-10-22)

The same physical build subsequently moved from X77/5.2 to X73A/6.1.0.3640, kernel 6.6.129-qnap. Its complete original five-disk Qtier set returned with both RAID tiers and volumes Ready. The VM native-update test, physical offline boot-image upgrade, monitoring repair and their limits are documented together in [QTS 6.1 upgrade and results](11-qts61-upgrade.md). The narrative below describes the original 5.2 recovery, not the later upgrade.


Recorded 2026-10-17–18. Identifying information is removed. This is one measured setup, not a support matrix.

| Component | Observed setup |
|---|---|
| Host | ASRock Rack X570D4U-2L2T, Ryzen 5800X, 64 GiB RAM |
| QTS profile | TS-877 / TS-X77 |
| Firmware | QTS 5.2.10.3577 build 20260731, kernel 5.10.60-qnap |
| Boot medium | Samsung 980 500 GB NVMe, dedicated boot/firmware role |
| Original Qtier set | 2 × 4 TB SATA SSD RAID1, 3 × 8 TB SATA HDD RAID5 |
| Other disks | Three unrelated ZFS disks; not selected for QTS configuration |
| Bay map | Eight populated positions, all HAL reverse queries successful after DEV_PATH fix |

## Sequence and result

1. Explored shared boot/data space on a single SSD in disposable VMs. Abandoned that requirement when the tail mapping did not become a usable data disk.
2. Validated dedicated virtual NVMe boot plus separate virtual SATA data storage, initialization, official firmware upgrade and repeated cold starts.
3. Built a hardware-specific boot image and wrote only the explicitly identified, erasable boot NVMe. Used BMC virtual CD for maintenance.
4. Inventoried original disks and metadata before normal storage startup. Correct scan order initially concealed broken HAL reverse lookup.
5. Added full controller paths. All eight reverse queries returned success; physical 4/5 identification retained a documented inference from partially covered labels.
6. Booted normal QTS. Old configuration and storage returned automatically; no manual initialize/attach operation was used.
7. Restored management access at the old custom port. A legacy LACP/MTU configuration required separate network interpretation; DNS and external HTTPS worked.
8. Set normal QTS in GRUB and QTS first in UEFI BootOrder, detached virtual CD, then verified an unattended reboot.

## Final observed state

- SSD RAID1: 2/2 members, `[UU]`; HDD RAID5: 3/3, `[UUU]`; no rebuild pending.
- Pool Ready, 18.17 TB reported total; Qtier Idle with Automatic Data Tiering.
- SSD tier 3.63 TB, 29.7% used; HDD tier 14.54 TB, 64.2% used.
- System DataVol1 Ready; DataVol2 at 80.07% had a capacity threshold warning, not degraded RAID.
- Both volumes mounted and existing shares/directories were accessible. Several full-file SHA-256 reads succeeded.

## Limits of the evidence

No pre-switch hash baseline existed for the sampled real files, so unchanged data is not proven by those reads. No full surface/data-integrity audit or physical post-migration tier-promotion benchmark was performed. A previous independent virtual Qtier experiment must not be conflated with this physical recovery.

No manual QTS formatting/configuration targeted the unrelated ZFS disks. An intermediate normal boot into the previous OS could have auto-imported them, so we do not claim zero disk writes. Physical unattended reboot and VM cold starts are distinct results. Future upgrades, other controllers, motherboard/fan integration and the boot SSD tail as data storage remain unverified. CPU and SATA disk temperature display was subsequently verified as described below.

## Later hardware and app follow-up (2026-10-18)

The [follow-up procedure](07a-hardware-and-apps.md) repaired CPU temperature display, the 64 GiB/four-slot memory report, the front eight-large-bay preview, and the slot 1–8 SSD-cache eligibility bitmap. QTS displayed both 32 GiB ECC UDIMMs and all eight disk temperatures. Board temperature remained Not Supported; DIMM manufacturer remained Unknown in QTS. No cache was created.

A read-only app audit found 18 unregistered directories (10.25 GiB), with 1.44 GiB of ARM64 ELF files. App data and binaries were retained; container-layer ARM64 content was tracked separately. This establishes leftover candidates, not that every directory was a previously enabled app.

The revised overlay was saved with a rollback copy and readback hash check. The artwork helper passed a live test, and md1/md2 remained complete. **No reboot was performed after these hardware changes.** These follow-up checks do not replace post-change boot validation.
