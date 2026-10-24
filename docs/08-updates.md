# 8. Updates and rollback

[Task index](../README.md#read-in-this-order)

**Before updating:** retain the [accepted boot/storage baseline](07-acceptance.md) and review the [target release](02a-release-tracks.md). Hardware cosmetic changes are not a prerequisite.

Use the same update discipline for [both release tracks](02a-release-tracks.md). A successful boot of a newer image, a native manual update, update discovery, and scheduled unattended installation are **four different results**.

## What has been verified

- The original X77 5.1→5.2 manual update and independent boot were tested in a disposable VM.
- The later X73A 5.2.10→6.1.0.3640 native manual update passed signing checks, preserved the EFI/support boot path and test file, and cold-booted kernel 6.6.129-qnap. Both firmware slots changed.
- The physical X77→X73A change used an offline boot-image upgrade with SATA disconnected, followed by original Qtier recovery. It was not a test of native cross-family updating with the pool online.
- The newest stable selection checked on 2026-10-22 is 5.2.11.3652. It has not been boot-tested here.
- **Scheduled automatic firmware installation has not been verified on either route.** Optional adapter persistence is not a guarantee that the next updater preserves the boot path or storage format.

Detailed procedure and evidence live in [the 6.1 chapter](11-qts61-upgrade.md); shared construction/installation commands live in [the walkthrough](10-command-walkthrough.md). Do not duplicate or improvise the physical writer during an update.

## Per-release sequence

1. Check the exact model's official download page/feed and release notes. Record family, full version/build, package hash and channel. Do not silently switch families when checking for a new release.
2. On the build host, extract the package using the shared procedure. Compare kernel modules, boot payload, init scripts, HAL interfaces, EFI/GRUB material and update-slot behavior. Confirm NIC/storage driver support by PCI ID and then by runtime discovery.
3. Export configuration; retain an offline, verified boot backup and independent recoverable data copy. Boot/configuration backups cannot reverse changes made to an attached pool by the new system.
4. On a disposable copy, test initialization if this is a new install, and **the native updater** if evaluating an upgrade. Save all VM disks and UEFI state only after the VM has stopped.
5. Require update completion in QTS, expected runtime version/kernel, correct DOM/boot exclusion, each bay's reverse lookup, complete tiers/RAID/volumes and matching file hashes.
6. Power off the VM and start a fresh process from its disk with no ISO/direct-kernel shortcut. Verify all the above again, plus any optional adapters and required applications.
7. Schedule the physical operation, keeping console access and a recovery route available. Follow the existing-installation branch for a family change, then repeat physical storage and application acceptance.

## Notifications versus installation

For manual upgrade control, choose **“Notify me, but do not automatically update firmware”** under **Control Panel → System → Firmware Update**, if offered by your build. Verify the displayed setting instead of copying undocumented numeric configuration values. Notification delivery requires its own configured recipients/rules; see the [Chinese UI example](screenshots.zh-CN.md#更新通知).

Configure notification delivery separately if you want email/push alerts. A check schedule is not an installation schedule. Read [QNAP's automatic-update policy](https://docs.qnap.com/operating-system/qts/5.2.x/en-us/updating-the-firmware-automatically-4229F6D2.html) and the current UI before changing it. Application auto-updates are a separate setting and need their own compatibility review, particularly on Beta.

The observed 6.1 Beta appeared in the official `QTS_FW_5.2.0_beta.xml` feed. This verifies discovery metadata only. Do not force a different URL, skip signatures, or enable unattended updates merely because that feed offers a newer version.

## Persistent adaptations: what must survive

| Component | Required acceptance after update |
|---|---|
| EFI/GRUB and support overlay | Actual disk boot loads the intended official initrd and reviewed overlay; compare offline hashes and menu paths |
| Early boot guards / DOM | Exact boot identity, size, partition geometry and bounded mappings still pass; unrelated disks remain excluded |
| Data bays | Every physical disk has a valid HAL reverse slot/serial mapping; scanning alone is insufficient |
| Optional monitoring | Real readings, active service and fresh cache agree; return code or a stale dashboard alone is insufficient |
| DIMM/cache/artwork | Check actual semantics; skip unknown cosmetic changes rather than blocking storage or guessing slot masks |
| Apps | App Center availability, installed architecture, service health, data/permissions and a real workload check |
| Administrative access | Preserve a separate recovery console; do not silently restore broad sudo rules as part of hardware repair |

The public optional helpers are reference tooling, not a universal board adapter. A minimal boot/storage candidate can disable the recognized optional startup hook with `prepare_release_overlay.py` while retaining the boot guards. Re-enable only the modules tested for your hardware and release. Keep unknown binary/UI structures unchanged. A version number is evidence, not proof of compatibility; removing a version-prefix gate without retaining identity and semantic checks is not an adaptation strategy.

## Optional monitoring and thermal policy

The optional sensor adapter serializes and bounds KCS reads and verifies fresh readings. Preserve exclusive access; do not add another kernel/userspace KCS reader alongside it. Use the [monitoring troubleshooting steps](07a-hardware-and-apps.md#recover-a-failed-monitoring-module) when restoration fails.

`thermal.py` and `patch_thermal_overlay.py` are a separately invoked, host-gated CPU90 reference policy, not part of default startup. Do not copy a temperature threshold from the reference host or weaken thermal protection to pass a test. Determine safe limits from your hardware and cooling requirements, then validate any policy separately from reporting.

## Rollback

Retain an off-device copy of the original firmware payload, EFI/configuration, complete reviewed overlay, partition geometry and verified boot backup. Neither the other firmware slot nor a renamed archive is an independent backup.

Before original data disks have been exposed to new normal startup, an offline boot restore can return the boot environment to the recorded state. After pool/system-volume/app metadata changes, restore of the boot SSD alone is **not a validated downgrade**. Preserve the current disks, stop further writes and recover using an independently consistent data copy or export. Do not repeatedly alternate firmware versions against the only surviving pool.

**Next:** for the X77 → X73A / 6.1 change, follow [the existing-installation procedure](11-qts61-upgrade.md#3-upgrade-an-existing-custom-qts-installation); otherwise apply the per-release gates above. Finish with [storage and boot acceptance](07-acceptance.md).
