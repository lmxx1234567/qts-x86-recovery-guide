# 7. Independent boot and data acceptance

<!-- stage-navigation -->
[← Previous: Recover the disk set](06-migration.md) · [Workflow index](../README.md#read-in-this-order) · [Next: Hardware display and apps →](07a-hardware-and-apps.md)
<!-- /stage-navigation -->

For concrete commands and environment prerequisites, use the [ordered command walkthrough](10-command-walkthrough.md). Read this chapter for its acceptance gates and limitations.


## Two defaults to set

**GRUB:** back up the actual configuration on the boot SSD. Choose the normal QTS entry by its verified position or stable menu ID, and set a short visible timeout. Our menu had diagnostic first and normal QTS second, so `default=1`, `timeout=3` selected QTS. Do not copy that index to a different menu.

**UEFI:** confirm the QTS boot entry points to the dedicated SSD's EFI partition GUID and `/EFI/BOOT/BOOTX64.EFI` (the observed loader path). Make it first in permanent BootOrder while preserving other entries. `BootNext` only affects one boot and is not proof of a permanent default.

Inspect using `efibootmgr -v` from a maintenance environment booted in UEFI mode. If creating an entry is necessary, identify the disk and EFI partition first; an example pattern is `efibootmgr --create --disk VERIFIED_BOOT_DEVICE --part VERIFIED_ESP_NUMBER --label QTS --loader '\EFI\BOOT\BOOTX64.EFI'`. The placeholders must be replaced after inspection. Set BootOrder using the actual entry numbers and read it back. Do not delete the other OS entry.

QTS in our case lacked efibootmgr and efivarfs support. Mounting efivarfs failed; installing the command alone would not fix missing kernel support. Use the firmware UI or a suitable UEFI-booted maintenance OS. Booting the other installed OS just to change NVRAM can auto-import its storage; prefer maintenance media when protecting unrelated pools.

## Apply the defaults with an explicit check after each change

Use [walkthrough section 10](10-command-walkthrough.md#10-make-qts-the-default-and-test-without-media) for the EFI mount/edit commands. Confirm `test -d /sys/firmware/efi` succeeds in rescue; otherwise reboot rescue in UEFI mode before using `efibootmgr`.

1. Record `efibootmgr -v` and the dedicated SSD's partition UUID (`lsblk -o NAME,MODEL,SERIAL,PARTUUID`). Match the UEFI entry's GPT partition identifier to the SSD's EFI partition, not its friendly label alone.
2. Copy the existing GRUB configuration to an independent workstation/backup destination before editing. A second file on the same SSD helps undo an edit but is not an off-device backup.
3. Change only the intended default/timeout in the verified configuration. For the generated menu use `set default=qts-normal` and `set timeout=3`; confirm a menu entry actually has `--id qts-normal`. Retain the diagnostic entry.
4. In `efibootmgr -v`, identify the four-digit entry numbers. For example, **only if** QTS is `0007` and the other entries in order are `0002,0000`, `efibootmgr -o 0007,0002,0000` sets the permanent order. Use your actual numbers and preserve all entries. If a stale BootNext is present, `efibootmgr -N` removes that one-time override. Read the state again.
5. If `efibootmgr` cannot access EFI variables, use the motherboard firmware's boot-priority interface to select the same verified SSD. Do not infer success from running the command without checking its result.

**Ready to test:** the GRUB file is read back and unmounted, UEFI order is recorded, and BMC virtual media is disconnected. These settings alone do not prove a successful unattended boot.

## Unattended reboot test

Detach virtual CD and verify the BMC reports media inactive. Shut down/reboot normally, with no boot hotkey and no manual GRUB selection. Capture the resulting runtime OS/version, correct boot SSD identity, management access and storage checks. A BMC power confirmation dialog is not proof of reboot completion.

Then perform a full shutdown/start test when safe. Distinguish a normal reboot from a power-off cold boot in your report; our VM had repeated cold boots, while the final physical acceptance record demonstrated an unattended reboot.

## Record two distinct boot results

Use QTS's account/power menu to choose Restart and wait for the console and management service to return. Do not press a boot hotkey or choose a GRUB entry. Log in again, record the firmware/build and `uptime`, and repeat chapter 6's pool/member/tier/volume/file checks. If firmware lands in rescue, the wrong OS or diagnostics, the default-boot test failed even if manually selecting QTS works.

For a cold-start test, use QTS Shut Down, wait for the console and BMC to confirm the host is off, then power on through BMC or the physical button. Do not remove power while QTS is running. Repeat the same checks and record this separately from Restart. If an update or rebuild is in progress, postpone this test rather than force a power cycle.

Copy [the acceptance record](../templates/acceptance.md) to a private location and fill in evidence filenames and unresolved items. Mark tests not performed as pending, not passed. Only the results observed on your hardware belong in your acceptance record; the case's results are examples.

## Data acceptance

Use the [acceptance checklist](../templates/acceptance.md). At minimum record:

- Firmware/build and management web/SSH availability.
- Every expected RAID member, no unexpected rebuild, pool and Qtier health.
- Both tier identities and capacities, system volume, every data volume and shares.
- File size/hash comparisons with the source baseline; if absent, label checks as post-recovery readability only.
- Backup/export completion and any remaining warnings.

A GUI saying Ready does not validate every file. A few sample hashes do not validate an entire filesystem. In our case sample full-file reads succeeded, but there was no recorded pre-switch hash baseline for those files.

## Hardware and app acceptance

Continue with [hardware presentation and cross-architecture apps](07a-hardware-and-apps.md). Verify CPU/disk temperatures, real DIMM topology, front-preview highlights and cache eligibility separately from storage recovery. Record live verification and post-change reboot verification as distinct results. A missing App Center entry is not proof that its data has disappeared.

## Screenshot evidence

![Qtier after unattended reboot](../assets/screenshots/qtier-after-default-reboot-en.png)

See the [full screenshot journal](screenshots.md) for context and translations.

---

<!-- stage-navigation -->
[← Previous: Recover the disk set](06-migration.md) · [Workflow index](../README.md#read-in-this-order) · [Next: Hardware display and apps →](07a-hardware-and-apps.md)
<!-- /stage-navigation -->
