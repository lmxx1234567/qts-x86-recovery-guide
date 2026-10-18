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

A read-only review of the live host, its boot-overlay sources and local update evidence on **2026-10-18** found the following. “Stored in the overlay” means it can be reapplied if that overlay still loads; it does not mean the modification remains compatible with a new firmware. No update setting was changed during the initial audit. **This table records the pre-unification state.** The later [unified package](07a-hardware-and-apps.md#unified-one-shot-restoration-package) adds independent recovery/notifications for sensors, the CPU widget, memory, cache eligibility, artwork and MyQNAP metadata; boot-path and privilege-policy boundaries still apply.

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

The initial 2026-10-18 audit found `v3_action_mode = 2` (`UPDATE_LATEST`) and native update schedules, contrary to an older local research policy. After the operator explicitly requested a change, the QTS firmware-update page was used to select **“Notify me, but do not automatically update firmware.”** Configuration readback confirmed `v3_action_mode = 1` and legacy `action_mode = 2`. No firmware installer/reboot process was running when checked. Arrays remained complete, with the existing resync continuing.

The configured notification/check time remains daily at 04:00. The UI reports that no firmware-update delivery rule is configured; no recipients or external channels were added. The notification-only policy prevents automatic firmware installation, but does not itself configure email or push delivery. See the [official policy description](https://docs.qnap.com/operating-system/qts/5.2.x/en-us/updating-the-firmware-automatically-4229F6D2.html). Application-update settings were not changed.

![Firmware settings: notify only, daily check at 04:00, and a warning that delivery rules are not configured](../assets/screenshots/firmware-notify-only.png)

The actual settings-page capture from 2026-10-18 shows **“通知我，但不自动更新”** (notify me, but do not automatically update). The explanatory text says updates will not install automatically. The warning below it concerns missing notification-delivery rules; it is not permission to install firmware. The crop excludes the desktop account, address bar and unrelated notifications. It records the saved policy, not an upgrade or reboot test.

### Priorities before the next update

1. Verify the actual update mode and retain a tested recovery route and consistent backups. The original storage safeguards remain the highest priority.
2. Stage the exact target firmware and verify overlay loading, boot-device exclusion, unrelated-OS isolation and all eight bay mappings before accepting production operation.
3. Recheck DIMM topology/cache candidates. Give artwork and metadata-cache helpers explicit compatibility checks and failure reporting before relying on them unattended; this audit did not add those protections.
4. Verify `[Sensor Repair]` status and real readings, then check applications and administrative access separately. Do not automatically restore sudo privilege changes.

## Proposed support for routine updates

**Restoration package implemented and installed; automatic firmware installation not deployed.** The goal is ordinary stable TS-X77 / QTS 5.2 maintenance releases without an exact-build allowlist or a new manual review for every changed binary. Major QTS migrations, cross-model firmware changes and unusual hardware/boot-layout changes are outside this target. “Most routine updates” is an engineering goal, not a measured success rate. Native firmware installation remains notification-only until this design is implemented and exercised.

### Keep one persistent adaptation package

Keep a versioned manifest and original project scripts in the existing support-partition overlay, separate from the two firmware slots. Describe each customization as a small independent module: prerequisites, detection, narrow apply operation, verification and rollback. Preserve the current early boot identity/geometry and disk-isolation guards. After QTS starts, run one bounded reconciliation pass and exit; do not introduce a resident service.

| Component | Routine-update behavior to implement |
|---|---|
| Boot and storage mapping | Validate the actual loader hook, required boot tools/modules and known host mapping. Unexpected EFI replacement or partition-writing behavior stops installation; it is not a cosmetic fallback. |
| Sensors | Keep board/KCS identity, exclusive-access and real-reading checks. Use interface/configuration probes and bounded helper-process tests for the supported release family instead of requiring all five binaries to retain identical hashes. Hashes remain evidence/fast paths, not the only compatibility criterion. A changed HAL still needs successful probes; simply deleting hash checks is not sufficient. |
| CPU dashboard row | Recognize supported widget structures; leave the new vendor widget untouched if the pattern changes. Sensor collection can remain working even if the optional dashboard row needs a later patch. |
| DIMM reporting | Re-read SMBIOS and derive slot offsets rather than assume old handles. Update only the memory section/cache after confirming the topology. Failure produces a reporting warning, not a guessed configuration. |
| Cache candidate mask | Confirm the accepted enclosure port IDs before restoring the mask. Never select disks or create a cache automatically. |
| Artwork | Check SVG slot IDs and target resource structure. Fall back to vendor artwork on mismatch; do not block firmware installation over a chassis picture. |
| MyQNAP index cache | Restore only the known repository entry and deduplicated scheduled task; validate runtime dependencies and XML. Keep the last valid index on fetch failure and report staleness. |
| Administrative preferences | Keep privilege policy separate. Do not infer permission to recreate passwordless sudo from a sensor/package repair. |

The implemented package isolates optional module failures and sends one summarized QTS notification identifying restored, skipped and failed components. On-disk backups and runtime rollback cover the project's own patches; they are not automatic firmware/storage downgrades.

### A small scheduled update command, not a second updater daemon

For future unattended installation, prefer one project-owned scheduled command while the native policy stays notification-only. Its steps are: discover a stable release in the supported family; download the original package; check model, package integrity, required drivers and boot/partition update behavior; confirm storage is healthy and not rebuilding, staging space and configured backups are available; then hand installation and signature verification to the official QTS update path. Avoid constructing another raw firmware writer.

Routine releases that pass these checks need not appear on an exact-version allowlist. Changed boot-critical behavior stops with a notice; optional mod incompatibility normally means skipping that mod. A scheduled script is not a background daemon. The scheduled installer, its maintenance window and any restart permission are **not enabled by the present notification-only request**.

After the normal upgrade restart, the one-shot package checks the boot/mapping outcome, arrays, volumes and service availability, then restores compatible optional modules. Before implementing an installer wrapper, verify the official entry point's completion/reboot semantics: do not assume there is a usable “after write, before reboot” hook. Preserve the overlay through the inspected update path rather than depend on an undocumented interception.

### Delivery sequence

1. **Completed:** consolidated the fixes into independent one-shot modules, passed 28 repository tests and live preflight/application/idempotence checks, and installed the hash-verified overlay with a rollback backup. No NAS reboot or firmware installation was performed. See [implementation and commands](07a-hardware-and-apps.md#unified-one-shot-restoration-package).
2. **Pending:** first validate the next authorized boot, then exercise one representative maintenance-release update on disposable storage, including hook survival, restored mods and skipped-module notifications. Reuse that integration coverage for structurally compatible releases rather than require a full clone test for every build.
3. **Not deployed:** add the scheduled installer only after the supported official update entry point and first update cycle have been verified, with a separately selected maintenance/reboot policy.

The existing local static auditor is a starting point, not this completed controller: it pins an installer-script hash, kernel details and an older hook pattern. Adapt its checks to the actual current boot path; do not present its current static pass as runtime or automatic-install readiness.

## Why two firmware slots are not rollback

The tested update rewrote p2 and p3 with the new firmware. They were not an old/new A/B rollback pair. The separate support partition's files survived this one update, but that is not a contractual guarantee from QNAP. EFI acquired additional files even when the existing loader and menu stayed unchanged.

A safe rollback may require both boot and storage state from a consistent point, and an older firmware may not understand newer metadata. Do not downgrade against a live migrated pool merely because an older boot image exists. Recover important files first.

Future automation should implement the gate above, including explicit compatibility evidence and a failure stop. A timer that downloads the newest package and reboots is not a validated recovery/update system.

---

<!-- stage-navigation -->
[← Previous: Hardware display and apps](07a-hardware-and-apps.md) · [Workflow index](../README.md#read-in-this-order) · [Back to project overview →](../README.md)
<!-- /stage-navigation -->
