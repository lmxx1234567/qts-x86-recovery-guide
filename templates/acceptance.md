# Private recovery acceptance record

Date / operator:
Source QTS build / model / storage family:
Target hardware / PCI IDs / boot mode:
Loader provenance / byte length / SHA-256:
Firmware source / byte length / SHA-256:
Boot SSD serial / model / capacity:
Clone or backup location and consistency point:

- [ ] Complete disk set, keys and old settings recorded
- [ ] All physical bay identities checked, inferred entries marked
- [ ] Boot SSD excluded from installer data list
- [ ] HAL scan and every reverse query pass
- [ ] VM initialization, upgrade and cold boots pass
- [ ] Boot image full written-range readback verified
- [ ] Original/recovery-copy ownership exclusive to one system
- [ ] Correct RAID levels, UUIDs, members and event state
- [ ] Pool, Qtier tiers, all volumes and system volume verified
- [ ] Shares, permissions, encryption and application data checked
- [ ] File hashes compared to source baseline (or limitation stated)
- [ ] Independent backup/export completed
- [ ] Permanent UEFI BootOrder and GRUB default verified
- [ ] Virtual CD detached, no BootNext dependency
- [ ] Physical unattended reboot passes
- [ ] Physical power-off/start passes (separate from reboot)

## Post-recovery hardware and apps (separate from storage acceptance)

- [ ] CPU temperature agrees with a real kernel/HAL source
- [ ] Every supported disk temperature is visible
- [ ] Unsupported motherboard/fan sensors explicitly recorded; independent cooling retained
- [ ] Total memory and populated/empty DIMM topology agree with SMBIOS
- [ ] Front preview and selected-slot highlights agree with the HAL map
- [ ] Cacheable slot bitmap checked without selecting or initializing data disks
- [ ] App registration compared with retained directories; architecture and scan errors recorded
- [ ] App data preserved before any compatible-package restore test
- [ ] Revised overlay backed up, installed on verified boot device and read back
- [ ] All hardware follow-up checks repeated after an authorized reboot

Warnings / unresolved items:
Evidence filenames (private):
