# 8. Updates and rollback

<!-- stage-navigation -->
[← Previous: Hardware display and apps](07a-hardware-and-apps.md) · [Workflow index](../README.md#read-in-this-order) · [Back to project overview →](../README.md)
<!-- /stage-navigation -->

**Unattended automatic updating is not established by this project.** The observed official manual upgrade path succeeded in a disposable VM. That result does not prove that future firmware preserves the loader, overlay, drivers, HAL interfaces or data format.

Keep update notifications distinct from automatic installation. For recovery use, defer upgrades until data has been exported or backed up. For continued operation, evaluate security releases promptly through a staged workflow rather than leaving the machine indefinitely unpatched.

## Per-release gate

1. Download from the official source; record identity and inspect release notes and package contents.
2. Compare kernel/modules, init scripts, HAL libraries, EFI/GRUB and partition/updater logic against the tested version.
3. Back up the full boot SSD and configuration; make a consistent test copy/snapshot of the data disks. A boot backup alone cannot undo storage metadata changes.
4. Test the official update on an isolated copy. Keep official signature/version checks enabled and stage the package where space is sufficient.
5. Verify all bays, boot exclusion from data choices, both cold boots, pool/tier state and file hashes. Repeat the [hardware follow-up checks](07a-hardware-and-apps.md): native CPU temperature source, DIMM topology, cache-port mask and late-loaded web artwork. Re-derive DMI handle offsets after BIOS changes.
6. With a recovery route ready, schedule the production update and repeat acceptance. Keep the console available.

## Existing modification audit

A read-only review of the live host, its boot-overlay sources and local update evidence on **2026-10-18** found the following. “Stored in the overlay” means it can be reapplied if that overlay still loads; it does not mean the modification remains compatible with a new firmware. No update setting was changed during this audit.

| Modification | Persistence mechanism | Update failure mode / existing protection |
|---|---|---|
| Dedicated NVMe boot, bounded DOM mappings and unrelated-OS NVMe exclusion | EFI/GRUB loads the custom overlay; its early init checks device identity/geometry, creates DOM mappings and detaches the designated unrelated controller | **Highest consequence.** A replaced boot menu, omitted overlay, changed kernel/tool support or changed device topology can break boot or bypass intended isolation. The sensor checker cannot protect this earlier stage. Guarded init stops on its checked mismatches, but cannot enforce anything if it is never loaded. |
| Eight-bay SATA mapping | Full hardware-specific model copied by early init | Overlay survival restores the file, but changed PCI paths, HAL interpretation or model support can invalidate it. No automatic bay-by-bay acceptance or repair exists. |
| DIMM channels/slots and DMI offsets | `[System Memory]` in the overlay model | Depends on HAL's DMI decoder and SMBIOS handle offsets. Firmware may change decoding/cache behavior; BIOS changes may change offsets. No automatic compatibility gate or targeted DIMM-cache cleanup is installed. |
| SSD-cache candidate bitmap | `SYSTEM_DISK_CACHEABLE_BITMAP` in the overlay model, interpreted into HAL state | A new HAL may change/ignore the mask or cache stale values. Recheck candidates, but do not create a cache as a diagnostic. No automatic compatibility check exists. |
| Eight-large-bay artwork | Bounded startup helper copies three locally extracted SVGs after target paths appear | It checks **existence only**, not version, SVG structure or slot-ID semantics. Renamed paths cause timeout; reused paths with changed semantics could receive stale artwork. Only a temporary status file records the result; no QTS warning is implemented for this helper. |
| CPU/motherboard/fan integration and CPU dashboard row | New one-shot sensor check in the boot overlay | Compatible losses can be restored; unknown dependencies/layouts stop with a QTS warning. A removed overlay/hook prevents both repair and notification. Not upgrade/reboot-tested. |
| MyQNAP local metadata-cache workaround | Refresh/validation scripts in a private volume directory, a six-hour cron entry, local XML under `/etc/config/rssdoc`, and a third-party repository entry pointing to that XML | Script files can survive while the cron entry, repository registration, local web route, Python/curl dependency or metadata schema changes. Refresh preserves the last valid index on failure, so stale results may hide a broken refresh. No independent restart/upgrade self-check or QTS failure notification was found in this task. This is an index workaround, not proof of third-party package safety or compatibility. |
| Passwordless sudo customization | Runtime include directory `/usr/etc/sudoers.d` | Not present in the audited boot overlay. On this RAM-root installation it has no demonstrated reboot/update persistence. A replacement sudo configuration or reset runtime root may remove it. Keep an alternate administrator access route; do not silently recreate privilege rules as a sensor repair. |

The full model is copied as a unit by the existing early-init design. Consequently, the new sensor compatibility check does **not** protect the earlier disk, memory, cache or artwork adaptations, even when it reports success. Changes to these components need their own acceptance evidence, not just a working dashboard.

### Current automatic-update setting

The live `[Auto Firmware Update]` configuration contained `v3_action_mode = 2`. In this exact firmware's `desktop/Enum.js`, `2` maps to `UPDATE_LATEST`; `FwSettingNotice.js` treats it as an enabled automatic-update mode. Native `auto_update` scheduled entries were also present. Thus the live configuration selects **automatic updates to the latest release**, despite an older local research policy recording automatic installation as disabled. This establishes the configured mode, not that a particular update has already run or will complete.

The audit did not disable updates, change application-update policy, reboot or modify storage. Given the boot/mapping dependencies above, use notification-only or manually staged firmware installation until the exact update path is validated. Selecting a different mode is a separate operational change. Recheck the live UI/configuration rather than treating the old local policy file or the mere existence of a cron entry as authoritative.

### Priorities before the next update

1. Verify the actual update mode and retain a tested recovery route and consistent backups. The original storage safeguards remain the highest priority.
2. Stage the exact target firmware and verify overlay loading, boot-device exclusion, unrelated-OS isolation and all eight bay mappings before accepting production operation.
3. Recheck DIMM topology/cache candidates. Give artwork and metadata-cache helpers explicit compatibility checks and failure reporting before relying on them unattended; this audit did not add those protections.
4. Verify `[Sensor Repair]` status and real readings, then check applications and administrative access separately. Do not automatically restore sudo privilege changes.

## Why two firmware slots are not rollback

The tested update rewrote p2 and p3 with the new firmware. They were not an old/new A/B rollback pair. The separate support partition's files survived this one update, but that is not a contractual guarantee from QNAP. EFI acquired additional files even when the existing loader and menu stayed unchanged.

A safe rollback may require both boot and storage state from a consistent point, and an older firmware may not understand newer metadata. Do not downgrade against a live migrated pool merely because an older boot image exists. Recover important files first.

Future automation should implement the gate above, including explicit compatibility evidence and a failure stop. A timer that downloads the newest package and reboots is not a validated recovery/update system.

---

<!-- stage-navigation -->
[← Previous: Hardware display and apps](07a-hardware-and-apps.md) · [Workflow index](../README.md#read-in-this-order) · [Back to project overview →](../README.md)
<!-- /stage-navigation -->
