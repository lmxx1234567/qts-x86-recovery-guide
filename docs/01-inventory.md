# 1. Inventory, copies and recovery baseline

<!-- stage-navigation -->
[← Previous: Scope and decisions](00-scope.md) · [Workflow index](../README.md#read-in-this-order) · [Next: Firmware and loader →](02-firmware.md)
<!-- /stage-navigation -->

## Before removing disks from the source

If the source is usable, export configuration, record QTS version/build and model, photograph bay labels, and save storage screenshots showing RAID groups, pool, volumes, Qtier tiers, encryption and any SSD cache. Export encryption keys and verify passwords locally. Note management ports, static IPs, VLANs, bonding, MTU, users, ACLs, shares and application dependencies.

Shut down cleanly before moving the complete set. A Qtier SSD is a data-bearing tier, not disposable cache. Write-back cache is another dependency; determine its state before removing it. Label each disk and each cable. Do not rely on capacity or two visually identical SSD labels.

Use [bay-map.example.csv](../templates/bay-map.example.csv) and [acceptance.md](../templates/acceptance.md). Keep real serials, paths and credentials outside the public repository.

## Maintenance environment

Boot a verified SystemRescue ISO in UEFI mode. In the observed workflow, kernel options were:

```text
copytoram checksum nomdlvm ar_disable
```

`copytoram` permits removing/replacing the virtual CD after loading. `nomdlvm` disables SystemRescue's automatic MD/LVM activation; `ar_disable` disables autorun. These options are not a hardware write blocker. Check the actual kernel command line and active arrays/mounts. [SystemRescue documents these options](https://www.system-rescue.org/manual/Booting_SystemRescue/).

```sh
cat /proc/cmdline
cat /proc/mdstat
findmnt
lsblk -b -o NAME,PATH,TYPE,SIZE,MODEL,SERIAL,WWN,FSTYPE,MOUNTPOINTS
lspci -nnk
```

Run `sudo python3 tools/inventory.py > /path/on/separate-storage/inventory.json` from this repository. The collector reads device metadata; its output destination must not be an original recovery disk. It does not assemble arrays, mount filesystems, import pools or run SMART tests. Check recorded return codes: an unavailable command is missing evidence.

For an explicitly identified member partition, `mdadm --examine /dev/disk/by-id/VERIFIED_ID-part3` reads the MD superblock. Partition 3 was the data member in our case, **not a universal assumption**. Record RAID UUID, role, event counter, level and member count for all disks. Reading partition tables and RAID superblocks is different from activating an array. Generic LVM tools may not understand QNAP-specific Qtier metadata; do not activate or repair it casually.

## Copies and hashes

Make consistent full-disk clones/images with a tool suited to device health. GNU ddrescue with a persistent mapfile is appropriate for failing media, but source and destination selection must be reviewed separately; this repo intentionally does not guess them. Keep originals offline after imaging. Do not expose originals and their UUID-identical clones to an auto-assembling OS together.

A GPT backup or copies of the first few GiB are **not a data backup**. A prior experiment preserved metadata regions, but these were not full clones and can become stale after tier movement. They do not justify a general rollback promise.

If the old system is readable, hash representative files before shutdown. Use the same relative paths after recovery and compare size and SHA-256. Read large files and examples from every volume; check ACLs and application-specific data separately. A hash first computed after migration proves readability, not unchanged data.

---

<!-- stage-navigation -->
[← Previous: Scope and decisions](00-scope.md) · [Workflow index](../README.md#read-in-this-order) · [Next: Firmware and loader →](02-firmware.md)
<!-- /stage-navigation -->
