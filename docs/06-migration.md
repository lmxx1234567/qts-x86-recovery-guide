# 6. Recover the original QNAP disk set

[Task index](../README.md#read-in-this-order)

**Before normal storage startup:** complete [inventory/backups](01-inventory.md) and [all per-disk HAL mapping checks](05-bay-mapping.md#acceptance-table).

The storage procedure is shared by both release tracks. The original pool was recovered on 5.2 and later on 6.1; see [the version-specific evidence and limits](11-qts61-upgrade.md#1-compatibility-and-prerequisites).

## Choose the right branch

QNAP distinguishes an uninitialized destination receiving a complete old system disk set from an already initialized destination attaching another pool. The latter may use **Storage & Snapshots → Disks/VJBOD → Recover → Attach and Recover Storage Pool** (menu grouping varies by version). See [QNAP's migration FAQ](https://www.qnap.com/en-ca/how-to/faq/article/what-should-i-do-if-migrated-disks-are-not-shown-as-storage-pool-qnap-nas).

Those instructions describe supported QNAP appliances; they do not certify a generic PC. On the reference host, normal startup recovered the configuration and pool automatically after HAL mapping was corrected. If that happens, proceed directly to verification.

## Decide before clicking anything

| What you see | Next step |
| --- | --- |
| Destination was not initialized; complete original system disk set is present | Follow the controlled boot below and look for restored settings/pool. Do not pre-initialize it to unlock the desktop. |
| Original pool and volumes already appear | Skip manual recovery; verify membership and files. |
| Destination was already initialized independently; old pool appears absent | Review the manual attach branch below, first on a consistent recovery copy. |
| Smart Installation asks to erase/initialize original disks, or a tier/member is missing | Stop before confirmation. Preserve the display/logs and investigate the identity/mapping/metadata mismatch. |
| Pool is degraded, inactive, encrypted without keys, or reporting I/O errors | Do not use these healthy-set instructions as a repair recipe. Preserve or image the members and resolve that condition first. |

Both Qtier tiers are members of the pool. The SSD tier is not optional cache that can be discarded and recreated. Have the old login, encryption credentials/keys, disk worksheet and pool/RAID/volume inventory available before the first normal boot.

## Controlled first storage boot

1. Complete the VM and physical HAL gates. Stop any old recovery VM/service that can access the same disks. Do not allow two systems to manage the same pool.
2. Power down cleanly. Attach the complete identified QNAP set, preserving recorded ordering where possible. Keep unrelated disks out of any storage configuration.
3. Boot the chosen QTS entry deliberately with a console available. Normal QTS startup can assemble arrays and write system metadata automatically. This is the transition out of read-only inventory.
4. Observe startup logs and wait for services. In the case, full management startup took roughly 10–12 minutes. A mounted DataVol1 was progress, not complete acceptance.
5. Find the restored address and management port. Old settings may replace the temporary installer defaults. Log in with the old account; do not reset or initialize to solve an unfamiliar login screen.
6. If a wizard offers initialization, stop. Recheck HAL, firmware family, full disk membership and old system metadata. If an initialized destination offers attach/recover, review exactly which pool and disks are listed before proceeding on copies.

## Find the restored management address

Use the router's DHCP lease list and the NIC MAC recorded in your inventory, or the console. Old static addresses, VLANs and link aggregation may return with the old configuration. Keep the source NAS offline to avoid duplicate addresses; the BMC address is separate from the QTS address. Do not assume the case's IP or web port applies to your machine.

If you already have an authorized QTS shell, these commands only inspect configuration:

```sh
ip addr show
ip route
/sbin/getcfg System 'Web Access Port' -f /etc/config/uLinux.conf
/sbin/getcfg System 'Version' -f /etc/config/uLinux.conf
/sbin/getcfg System 'Build Number' -f /etc/config/uLinux.conf
netstat -lnt
```

Open the observed HTTP/HTTPS address and port from a computer on the appropriate network. If the old IP is on another subnet, use an isolated matching client network first; do not reset QTS network/configuration as a shortcut. If no NIC/link is present, return to driver/profile diagnosis. If services are still starting, watch the console rather than repeatedly power-cycling.

Log in with the original QNAP account. If shell checks are needed and SSH is disabled, an administrator can enable it under **Control Panel → Network & File Services → Telnet/SSH**, record its port, and apply the setting. From your workstation use `ssh -p PORT USER@ADDRESS` with the observed values. Verify the host identity before accepting a changed host key; do not blindly delete known-host records. See [QTS SSH instructions](https://docs.qnap.com/operating-system/qts/5.2.x/en-us/enabling-ssh-on-the-nas-61C229CD.html). Lack of a working account is a separate access issue, not permission to initialize/reset the disks.

## Manual attach branch: already initialized destination only

This follows [QNAP's documented branch](https://www.qnap.com/en-ca/how-to/faq/article/what-should-i-do-if-migrated-disks-are-not-shown-as-storage-pool-qnap-nas); it was not exercised in the case's automatic migration. Generic hardware still needs its own validation.

1. Use Storage & Snapshots → Storage → Disks/VJBOD. Open the More menu and choose Recover (some builds label the option Attach and Recover Storage Pool).
2. Let QTS scan. Compare the offered RAID configuration and member disks with your inventory, including every Qtier tier. If the complete expected set cannot be established, cancel instead of guessing.
3. Only for the confirmed recovery copy/set, choose Attach and wait. Do not select New Storage Pool, Initialize, Format or Create RAID as substitutes.
4. When recovery finishes, check pool readiness and all volumes, then perform the identity and file checks below. An empty result or failed attach needs diagnosis; do not retry with forced MD/LVM commands.

## Verify storage before applications

Compare `/proc/mdstat`, pool status, each RAID group's level/member identities, volume names/types, encryption state and Qtier tier membership with the baseline. Check system arrays as well as data arrays. Do not assume RAID numbers such as md1/md2 are universal.

The recovered case showed two SSDs in RAID1 and three HDDs in RAID5, with no degraded member or rebuild. Qtier showed both tiers and Idle/Automatic Data Tiering. A volume capacity threshold warning was not an array failure.

Read directories, then actual files from every volume. Compare pre-migration hashes where available. Validate shares, users, ACLs, extended attributes, encrypted content and application data separately. Export the important data to an independent destination before experimenting with updates or tuning.

## A concrete storage and file checklist

In Storage & Snapshots, select each pool and open its management/details view. Expand its RAID groups and volumes. Record a private table with pool name/capacity/status, RAID level and member serials, each Qtier tier, and volume name/type/capacity/encryption/lock status. Confirm the system-volume designation. Use Disks/VJBOD to cross-check each member against the physical worksheet; a pool number alone is not an identity.

Read-only shell evidence can supplement the UI:

```sh
cat /proc/mdstat
mount
df -h
ls -l /share
```

`/proc/mdstat` lists multiple system/data arrays. For example, `[3/3] [UUU]` indicates three expected and active RAID members in that array; an underscore is a missing member. Lines mentioning recovery/resync/reshape indicate background work, not completed acceptance. This does not establish Qtier consistency or file integrity. If the UI and shell disagree, retain both outputs and stop configuration changes.

For each volume, use File Station to open an existing share and download several known files to a separate workstation destination. Include files from different folders and larger files, not only directory listings. With an authorized shell, resolve an actual share path before hashing:

```sh
# Replace both names with observed existing paths, keeping quotes.
readlink -f '/share/EXISTING_SHARE'
sha256sum '/share/EXISTING_SHARE/EXISTING_FILE'
```

Compare with the pre-migration hash for that same file. On a Mac, `shasum -a 256 DOWNLOADED_FILE` checks the downloaded copy. Without a pre-migration baseline, matching recovered/downloaded hashes prove transfer agreement and readability, not unchanged pre-migration contents. Encrypted volumes need the original unlock credentials/key through their QTS management UI; do not create a replacement volume when one remains locked.

Test SMB access from a normal user account too: in macOS Finder use Go → Connect to Server with `smb://ADDRESS/SHARE`; on Windows enter `\\ADDRESS\SHARE` in Explorer. Confirm expected read/access-denied behavior without changing permissions just to make the check pass. A downloaded file does not test ACLs or extended attributes.

Copy the important files to an independent destination, check copy errors, and reopen/hash files there. A test download is only a sample, and a copy to another share on the same pool is not an independent backup. Do not run app reinstalls, cache creation, tier reconfiguration or updates until the recovery/export record is complete.

## Cross-architecture application follow-up

Restored storage and app data do not prove every QPKG can run on the destination CPU. The ARM64-to-x86 case retained unregistered app directories. See the [read-only application audit](07a-hardware-and-apps.md#arm64-apps-preserve-data-inventory-before-cleanup) for registration comparison, ELF size accounting and preservation before any reinstall or cleanup.

## What to avoid

Do not recreate a pool with the old disks, treat a missing SSD tier as optional cache, force generic LVM activation, restore stale VG metadata over a live pool, or run repair commands just because a UI is slow. A RAID UUID match alone does not establish a consistent Qtier transaction state.

Disconnect unrelated storage where practical and explicitly control which OS boots. An unintended boot into another installed OS can auto-import its pools even if QTS never selected those disks.

**Next:** [verify independent boot and complete data acceptance](07-acceptance.md). Export important data before optional hardware/app changes.
