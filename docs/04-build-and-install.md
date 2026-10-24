# 4. Build a boot SSD and use virtual CD

<!-- stage-navigation -->
[← Previous: VM validation](03-vm-validation.md) · [Workflow index](../README.md#read-in-this-order) · [Next: Map every bay →](05-bay-mapping.md)
<!-- /stage-navigation -->

For concrete commands and environment prerequisites, use the [ordered command walkthrough](10-command-walkthrough.md). Read this chapter for its acceptance gates and limitations.

This chapter describes the complete build contract and installation sequence. It requires a compatible externally obtained base loader; the repository is not a standalone firmware distribution. Work on regular image files first. Never run image-building commands against original data disks.

## A. Inspect the base image

On an isolated Linux build machine, use `fdisk -l base.img` and `sgdisk -v base.img` to inspect a **regular file**. Record sector size, partition starts/lengths/types/GUIDs and filesystem labels. The walkthrough extracts partitions into regular files so no loop-device mount is needed. An untrusted image belongs in a disposable build VM.

The observed base used 512-byte sectors and these mappings:

| Partition | Start sector | Length (sectors) | Role in this case |
|---|---:|---:|---|
| 1 | 2048 | 32768 | EFI / GRUB |
| 2 | 34816 | 1048576 | Firmware slot |
| 3 | 1083392 | 1048576 | Firmware slot |
| 5 | 2131968 | 16384 | Existing small partition |
| 6 | 2148352 | 16384 | Existing small partition |
| 7 | 2164736 | 5535711 | Support / adaptation files |

The whole DOM view was 16777216 sectors (8 GiB). Preserve the base layout; do not paste this table into a different loader.

## B. Build a separate physical candidate

The VM image is not the physical installer: its serials, disk size, PCI addresses and bay profile are different. Use a separate checkout/work directory for the physical build. Keep the accepted lab files unchanged.

| Order | Run on | Action and exact commands | Expected result |
| --- | --- | --- | --- |
| 1 | Build VM | [Prepare the directories and inputs](10-command-walkthrough.md#1-build-machine-and-directory-layout); reuse the reviewed base and complete extracted firmware set | Fresh `private/` directory; recorded input hashes |
| 2 | Build VM | [Inspect and copy the base](10-command-walkthrough.md#3-record-the-base-image-layout) | Geometry matches the selected recipe; untouched base retained |
| 3 | NAS rescue/diagnostic, then build VM | [Collect actual topology](05-bay-mapping.md#concrete-linux-topology-collection), then [prepare the physical profile](10-command-walkthrough.md#4-make-separate-vm-and-physical-profiles) | Real boot serial/size and controller paths; no lab identities |
| 4 | Build VM | [Assemble and read back](10-command-walkthrough.md#5-assemble-firmware-slots-support-and-grub) | Both slots, both overlays and GRUB read back correctly; final hash recorded |
| 5 | Build VM | [Package the physical candidate](10-command-walkthrough.md#7-build-the-physical-candidate-and-payload-iso) | `qts-payload.iso` contains the verified image and checksums |

Chapter 2 explains [each input's requirements](02-firmware.md#build-inputs). The walkthrough owns the executable image-building commands so there is only one recipe to maintain. A successful packer run proves archive creation, not valid physical hardware mapping. If topology is still uncertain, build only a diagnostic candidate and repeat the mapping loop in chapter 5 before normal startup.

## C. Mount virtual media and enter rescue

1. Shut down the existing OS cleanly. Keep original data disks disconnected for boot-SSD writing where practical; identify any disks that remain attached. Connect the dedicated, erasable boot SSD.
2. Log into your BMC, open its remote console, and find **Virtual Media / CD/DVD** (names vary). Select the verified SystemRescue ISO and connect/start media. A selected filename is not enough: confirm media is reported connected.
3. Power on and use the motherboard's one-time boot menu, selecting the **UEFI** virtual optical drive. Do not guess the boot-menu key; use the board's POST screen/manual. If another OS starts, shut it down cleanly and correct the boot selection.
4. At the SystemRescue boot menu, edit the boot parameters using its displayed help and add `copytoram checksum nomdlvm ar_disable`. These options belong to SystemRescue, not the QTS menu. Wait for the rescue shell and check `test -d /sys/firmware/efi && echo UEFI`.
5. Inspect `cat /proc/cmdline`, `findmnt`, `lsblk`, `cat /proc/mdstat` and `swapon --show`. Confirm the intended options took effect and rescue is running from RAM. These settings do not replace inspection for mounted/active storage.
6. Replace the virtual media with `qts-payload.iso` only after rescue has loaded into RAM. Follow the [media mount/checksum commands](10-command-walkthrough.md#7-build-the-physical-candidate-and-payload-iso). This disc is data only; do not reboot expecting it to boot.

If the BMC disconnects, reauthenticate and check both console and media state before continuing. If the file picker cannot access your ISO, select it manually in the browser; do not work around it by choosing an unverified older payload.

## D. Write only the intended boot SSD

Run [the explicit-target writer sequence](10-command-walkthrough.md#8-write-the-physical-boot-ssd-destructive-explicit-target) in the NAS rescue shell as root. Read each gate before executing the next block. It checks identity, sector size, mounts/holders and image size, asks for the verified serial, clears stale tail metadata on that disposable target, writes, flushes and compares the full image-length range.

Before the destructive block, match **serial + model + exact byte capacity** against your physical build record. Use the whole-disk `/dev/disk/by-id/` link, not a `-partN` link. Names such as `nvme0n1` may change between boots. Any mount, swap, MD/LVM/DM holder or unknown disk identity blocks writing; do not automatically dismantle a pool to satisfy the check.

A completed `dd` progress line is not acceptance. The following `cmp` must exit successfully, and the reread partition table must match the candidate. If anything fails, keep the rescue session open, retain the error, and inspect the target before rebooting. Do not apply GPT expansion or filesystem growth as an automatic fix.

## E. First disk boot: diagnostics only

1. Flush/unmount the payload media, disconnect virtual CD, and use the firmware boot menu to select the dedicated SSD's UEFI loader. If it has no firmware entry, use the verified-entry procedure in [chapter 7](07-acceptance.md#two-defaults-to-set); keep GRUB's diagnostic default for now.
2. Select the diagnostic entry and capture its complete output. A stopped diagnostic console is expected, not a hung installer. If GRUB cannot find a label/UUID or kernel, return to rescue and compare the installed EFI/support files with the verified build.
3. To check original members, shut down before connecting the recorded disk set, then boot **diagnostic again**. Complete [all bay checks](05-bay-mapping.md) before choosing normal QTS. A powered-off diagnostic environment can be restarted through host controls after confirming normal storage services never started; do not use this as a general hard-reset instruction for running QTS.

**Exit condition:** written-range verification passes, the SSD boots without rescue media, and the physical diagnostic environment is available. Pool migration is a separate step; do not initialize original disks to get past a welcome page.

---

<!-- stage-navigation -->
[← Previous: VM validation](03-vm-validation.md) · [Workflow index](../README.md#read-in-this-order) · [Next: Map every bay →](05-bay-mapping.md)
<!-- /stage-navigation -->
