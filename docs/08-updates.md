# 8. Updates and rollback

**Unattended automatic updating is not established by this project.** The observed official manual upgrade path succeeded in a disposable VM. That result does not prove that future firmware preserves the loader, overlay, drivers, HAL interfaces or data format.

Keep update notifications distinct from automatic installation. For recovery use, defer upgrades until data has been exported or backed up. For continued operation, evaluate security releases promptly through a staged workflow rather than leaving the machine indefinitely unpatched.

## Per-release gate

1. Download from the official source; record identity and inspect release notes and package contents.
2. Compare kernel/modules, init scripts, HAL libraries, EFI/GRUB and partition/updater logic against the tested version.
3. Back up the full boot SSD and configuration; make a consistent test copy/snapshot of the data disks. A boot backup alone cannot undo storage metadata changes.
4. Test the official update on an isolated copy. Keep official signature/version checks enabled and stage the package where space is sufficient.
5. Verify all bays, boot exclusion from data choices, both cold boots, pool/tier state and file hashes.
6. With a recovery route ready, schedule the production update and repeat acceptance. Keep the console available.

## Why two firmware slots are not rollback

The tested update rewrote p2 and p3 with the new firmware. They were not an old/new A/B rollback pair. The separate support partition's files survived this one update, but that is not a contractual guarantee from QNAP. EFI acquired additional files even when the existing loader and menu stayed unchanged.

A safe rollback may require both boot and storage state from a consistent point, and an older firmware may not understand newer metadata. Do not downgrade against a live migrated pool merely because an older boot image exists. Recover important files first.

Future automation should implement the gate above, including explicit compatibility evidence and a failure stop. A timer that downloads the newest package and reboots is not a validated recovery/update system.
