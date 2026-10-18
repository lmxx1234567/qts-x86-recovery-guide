# Screenshot journal

All images are original captures with irreversible solid-color redactions. Original private files are not included. Each English reading-guide image adds a clearly separated translated/explanatory caption; it is not a recreated English QTS interface. Console text is already predominantly English. Historical failures are labeled, not presented as final success.

Chinese UI glossary: 存储池 = Storage Pool; 空闲 = Idle; 自动数据分层 = Automatic Data Tiering; 超高速 = Ultra-high-speed tier; 容量 = Capacity tier; 已用 = Used; 总计 = Total; 下移/上移 = Move down/up; RAID 组 = RAID Group.

## 980 Independent Grub

Early boot menu: diagnostic first, normal QTS second. This was not the final default configuration.

![Early boot menu: diagnostic first, normal QTS second. This was not the final default configuration.](../assets/screenshots/980-independent-grub-en.png)

[Redacted original](../assets/screenshots/980-independent-grub.png)

## 980 Write Verified

Dedicated boot SSD image written and read back successfully. Earlier lines show a payload filename mismatch.

![Dedicated boot SSD image written and read back successfully. Earlier lines show a payload filename mismatch.](../assets/screenshots/980-write-verified-en.png)

[Redacted original](../assets/screenshots/980-write-verified.png)

## Arrays Readonly Complete

Historical inspection: MD RAID1 and RAID5 assembled read-only. This is not proof that later QTS startup is read-only.

![Historical inspection: MD RAID1 and RAID5 assembled read-only. This is not proof that later QTS startup is read-only.](../assets/screenshots/arrays-readonly-complete-en.png)

[Redacted original](../assets/screenshots/arrays-readonly-complete.png)

## Bmc Login Required

BMC login required. Re-authenticate and reopen KVM; do not reset the NAS merely to fix a session.

![BMC login required. Re-authenticate and reopen KVM; do not reset the NAS merely to fix a session.](../assets/screenshots/bmc-login-required-en.png)

[Redacted original](../assets/screenshots/bmc-login-required.png)

## Bmc Powered Off

BMC power controls. Verify the actual host power state after a shutdown request.

![BMC power controls. Verify the actual host power state after a shutdown request.](../assets/screenshots/bmc-powered-off-en.png)

[Redacted original](../assets/screenshots/bmc-powered-off.png)

## Bmc Session Expired

BMC session expired. Console and virtual-media state must be checked after re-login.

![BMC session expired. Console and virtual-media state must be checked after re-login.](../assets/screenshots/bmc-session-expired-en.png)

[Redacted original](../assets/screenshots/bmc-session-expired.png)

## Bmc Timeout Limit

BMC web/session timeout settings. Available limits depend on BMC firmware.

![BMC web/session timeout settings. Available limits depend on BMC firmware.](../assets/screenshots/bmc-timeout-limit-en.png)

[Redacted original](../assets/screenshots/bmc-timeout-limit.png)

## Eight Bay Hal Verified

HISTORICAL FAILURE: scan order was correct, but reverse lookup still returned -1 / port 0. Later fixed with DEV_PATH.

![HISTORICAL FAILURE: scan order was correct, but reverse lookup still returned -1 / port 0. Later fixed with DEV_PATH.](../assets/screenshots/eight-bay-hal-verified-en.png)

[Redacted original](../assets/screenshots/eight-bay-hal-verified.png)

## Kvm Partial Access

KVM partial-access/session issue. Console control permissions are separate from QTS health.

![KVM partial-access/session issue. Console control permissions are separate from QTS health.](../assets/screenshots/kvm-partial-access-en.png)

[Redacted original](../assets/screenshots/kvm-partial-access.png)

## Pool Vg1 Hdd Metadata

Historical metadata inspection: HDD-side VG metadata and read-only MD arrays. Identifiers redacted.

![Historical metadata inspection: HDD-side VG metadata and read-only MD arrays. Identifiers redacted.](../assets/screenshots/pool-vg1-hdd-metadata-en.png)

[Redacted original](../assets/screenshots/pool-vg1-hdd-metadata.png)

## Pool Vg1 Metadata

Historical metadata inspection: VG/PV layout. Matching metadata alone does not prove complete data integrity.

![Historical metadata inspection: VG/PV layout. Matching metadata alone does not prove complete data integrity.](../assets/screenshots/pool-vg1-metadata-en.png)

[Redacted original](../assets/screenshots/pool-vg1-metadata.png)

## Qtier After Default Reboot

AFTER UNATTENDED REBOOT: Qtier Idle; Automatic Data Tiering; SSD 3.63 TB / 29.7%; HDD 14.54 TB / 64.2%.

![AFTER UNATTENDED REBOOT: Qtier Idle; Automatic Data Tiering; SSD 3.63 TB / 29.7%; HDD 14.54 TB / 64.2%.](../assets/screenshots/qtier-after-default-reboot-en.png)

[Redacted original](../assets/screenshots/qtier-after-default-reboot.png)

## Qtier Restored Verified

RECOVERED POOL: Qtier Idle; Automatic Data Tiering; RAID1 SSD tier and RAID5 HDD tier visible.

![RECOVERED POOL: Qtier Idle; Automatic Data Tiering; RAID1 SSD tier and RAID5 HDD tier visible.](../assets/screenshots/qtier-restored-verified-en.png)

[Redacted original](../assets/screenshots/qtier-restored-verified.png)

## Qts After Eight Bay Boot

Historical smart-install welcome page before successful recovery. Do not initialize original disks from this page.

![Historical smart-install welcome page before successful recovery. Do not initialize original disks from this page.](../assets/screenshots/qts-after-eight-bay-boot-en.png)

[Redacted original](../assets/screenshots/qts-after-eight-bay-boot.png)

## Qts Baremetal Web

Initial QTS web welcome page with boot SSD. Web availability alone does not validate a recovered pool.

![Initial QTS web welcome page with boot SSD. Web availability alone does not validate a recovered pool.](../assets/screenshots/qts-baremetal-web-en.png)

[Redacted original](../assets/screenshots/qts-baremetal-web.png)

## Qts Default Boot Order

Permanent UEFI BootOrder now selects QTS first. Virtual CD shows 0 KB / inactive. Subsequent reboot was verified.

![Permanent UEFI BootOrder now selects QTS first. Virtual CD shows 0 KB / inactive. Subsequent reboot was verified.](../assets/screenshots/qts-default-boot-order-en.png)

[Redacted original](../assets/screenshots/qts-default-boot-order.png)

## Qts Restored Hostname Login

QTS console login after the old configuration returned. Private hostname removed.

![QTS console login after the old configuration returned. Private hostname removed.](../assets/screenshots/qts-restored-hostname-login-en.png)

[Redacted original](../assets/screenshots/qts-restored-hostname-login.png)

## Qts Uefi Name

Historical UEFI entry naming and one-time BootNext selection. BootNext is not a permanent default.

![Historical UEFI entry naming and one-time BootNext selection. BootNext is not a permanent default.](../assets/screenshots/qts-uefi-name-en.png)

[Redacted original](../assets/screenshots/qts-uefi-name.png)

## Reconnected Disk Inventory

Read-only device inventory after reconnecting disks. Serial column removed; device names can change between boots.

![Read-only device inventory after reconnecting disks. Serial column removed; device names can change between boots.](../assets/screenshots/reconnected-disk-inventory-en.png)

[Redacted original](../assets/screenshots/reconnected-disk-inventory.png)

## Sata Port Mapping

Linux by-path controller/port links. These must be correlated with physical bays and QTS HAL reverse queries.

![Linux by-path controller/port links. These must be correlated with physical bays and QTS HAL reverse queries.](../assets/screenshots/sata-port-mapping-en.png)

[Redacted original](../assets/screenshots/sata-port-mapping.png)

## Raid Sda3

Historical MD member examination: RAID level, size, role and event counters. Device letters are case-specific; UUIDs removed.

![Historical MD member examination: RAID level, size, role and event counters. Device letters are case-specific; UUIDs removed.](../assets/screenshots/raid-sda3-en.png)

[Redacted original](../assets/screenshots/raid-sda3.png)

## Raid Sde3

Historical MD member examination: RAID level, size, role and event counters. Device letters are case-specific; UUIDs removed.

![Historical MD member examination: RAID level, size, role and event counters. Device letters are case-specific; UUIDs removed.](../assets/screenshots/raid-sde3-en.png)

[Redacted original](../assets/screenshots/raid-sde3.png)

## Raid Sdf3

Historical MD member examination: RAID level, size, role and event counters. Device letters are case-specific; UUIDs removed.

![Historical MD member examination: RAID level, size, role and event counters. Device letters are case-specific; UUIDs removed.](../assets/screenshots/raid-sdf3-en.png)

[Redacted original](../assets/screenshots/raid-sdf3.png)

## Raid Sdg3

Historical MD member examination: RAID level, size, role and event counters. Device letters are case-specific; UUIDs removed.

![Historical MD member examination: RAID level, size, role and event counters. Device letters are case-specific; UUIDs removed.](../assets/screenshots/raid-sdg3-en.png)

[Redacted original](../assets/screenshots/raid-sdg3.png)

## Raid Sdh3

Historical MD member examination: RAID level, size, role and event counters. Device letters are case-specific; UUIDs removed.

![Historical MD member examination: RAID level, size, role and event counters. Device letters are case-specific; UUIDs removed.](../assets/screenshots/raid-sdh3-en.png)

[Redacted original](../assets/screenshots/raid-sdh3.png)
