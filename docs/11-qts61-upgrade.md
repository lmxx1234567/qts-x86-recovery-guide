# QTS 6.1: upgrade procedure and verified results

[← Release choices](02a-release-tracks.md) · [Shared installation commands](10-command-walkthrough.md) · [Updates and rollback →](08-updates.md)

This chapter contains only the differences and the existing-installation branch. **New installation:** select the Beta variables and X73A profile in the shared walkthrough, complete its VM and physical gates, then recover the disk set using [chapter 6](06-migration.md). A preliminary 5.2 installation is not required for that path.

## 1. What actually ran

| Layer | Verified result | Limit |
|---|---|---|
| Lab update | TS-X73A 5.2.10.3577 → 6.1.0.3640 through QTS's native updater; kernel 5.10.60-qnap → 6.6.129-qnap | Manual update, not scheduled unattended installation |
| Lab disk-only cold start | New QEMU process booted its virtual NVMe through UEFI/GRUB, without a maintenance CD or direct kernel boot | One disposable static volume; not a Qtier simulation |
| Lab preservation | Both firmware slots updated; EFI/GRUB and support overlay survived; all seven DOM mappings matched; 32 MiB test-file hash unchanged | Exact examined build/layout only |
| Physical upgrade | Consistent offline boot backup; SATA disconnected; both firmware slots and the reviewed model/overlay updated; EFI and other boot partitions retained | An offline boot-image migration, not a cross-family in-place native update |
| Physical storage | Reconnected complete five-disk Qtier set; original login/management port returned; 18.17 TB pool, SSD RAID1 and HDD RAID5 Ready; original volumes mounted | Nine partial file reads succeeded; no full pre/post dataset checksum comparison |
| Physical monitoring | Native CPU + actual motherboard/fan readings validated; updated adapter saved to support overlay | Final monitoring/thermal follow-up has not had a subsequent physical cold-boot test |

The data disks were absent during boot-image writing, but normal QTS startup after reconnecting them is write-capable. A boot backup cannot undo later storage metadata or application migrations. The operator's choice to proceed without an independent bulk-data backup is not a general recovery recommendation.

### Recovered storage and monitoring

![QTS 6.1 pool and RAID groups Ready](../assets/screenshots/qts61-pool-ready.png)

Both original RAID groups are Ready: SSD RAID1 (3.63 TB) and HDD RAID5 (14.54 TB). In this view, `就绪` means Ready and `良好` means Good.

![QTS 6.1 Qtier tiers and schedule](../assets/screenshots/qts61-tiers-ready.png)

Qtier is Idle (`空闲`) with automatic data tiering retained. Both populated tiers are present; the unused middle tier is not a missing member.

![QTS CPU and motherboard temperatures after sensor repair](../assets/screenshots/qts61-temperature.png)

The dashboard reports CPU69°C and motherboard47°C at this sample. `系统` means System. This is a live-reading milestone, not a heat-shutdown test.

## 2. Test the native update in a disposable VM

Use the shared walkthrough with these **starting** variables in a fresh work directory:

```bash
FW_FAMILY=TS-X73A
FW_BUILD=20260731
FW_VERSION=5.2.10.3577
MODEL_TRACK=x73a
```

Complete extraction/build/VM initialization with a new test SATA disk. The X73A 5.2 package is [available here](https://download.qnap.com/Storage/TS-X73A/TS-X73A_20260731-5.2.10.3577.zip). Keep the VM away from original disk passthrough. Create a test volume and a test file **inside the VM**, replacing the mount path with its actual volume:

```sh
# In the disposable QTS guest, after verifying this is its NEW test volume:
TEST_DIR='/share/REPLACE_LAB_VOLUME/qts-upgrade-test'
case "$TEST_DIR" in *REPLACE*) echo 'Set the actual disposable test volume'; exit 1;; esac
mkdir -p "$TEST_DIR"
dd if=/dev/urandom of="$TEST_DIR/sample.bin" bs=1M count=32
sha256sum "$TEST_DIR/sample.bin"
uname -r
/sbin/getcfg System Version
/sbin/getcfg System 'Build Number'
/sbin/dmsetup table
cat /proc/mdstat
```

Save the hash and command output on the build host. Shut down the guest and copy **boot disk, data disk and UEFI variables together** as shown in walkthrough section 6. Before updating, inspect the offline boot image with `image_parts.py`; save its EFI partition, GRUB file and support-overlay hash. Do not expect firmware-slot hashes to remain equal after an update.

Restart the VM. Download the exact [6.1 Beta ZIP](https://download.qnap.com/Storage/TS-X73A/TS-X73A_20261007-6.1.0.3640.zip) on the build host, test/extract it and retain an untouched copy. In QTS open **Control Panel → System → Firmware Update → Manual Installation**, choose the extracted `TS-X73A_20261007-6.1.0.3640.img` and follow the updater's prompts. If your UI requests the ZIP instead, follow that build's file selector instructions. Keep vendor signature/model/version checks enabled. Do not overwrite model names in the running VM merely to defeat an updater rejection.

The recorded lab used the native command-line updater. For reproducing that exact route **only inside the disposable guest**, copy the unmodified `.img` to a verified test-volume path with enough free space, open an authenticated root console, and run:

```sh
# VM only. Keep another verified copy on the build host.
UPDATE_IMG='/share/REPLACE_LAB_VOLUME/TS-X73A_20261007-6.1.0.3640.img'
case "$UPDATE_IMG" in *REPLACE*) echo 'Set verified lab staging path'; exit 1;; esac
test -f "$UPDATE_IMG" || exit 1
sha256sum "$UPDATE_IMG"
# Compare with the independently retained package hash BEFORE invoking the updater.
/etc/init.d/update.sh "$UPDATE_IMG"
```

For this examined `.img`, SHA-256 was `c73c47801387ebbce7a8d02531b3eca956ae5995828b0ba4dcec4c48731efc8f`. This identifies our package, not future releases. The ZIP has a different hash. The passing run reported code-signing `fp_status=0 cert_status=0`, `Update Finished`, and `Upgrade from 5.2.10 to 6.1.0`; QTS progress was 3 with error 0. **Do not accept a shell exit of 0 alone.** One failed run returned 0 with missing input (`FW001`). Native cleanup consumed the staged file; if QTS explicitly asks for a retry, restore and hash-check a fresh input copy first. Do not keep retrying unexplained failures or disable signing checks.

After the updater completes, follow its restart instructions. Check the displayed version **and** `uname -r`. Then shut down fully, confirm QEMU exited, and launch a new process using the same disks/UEFI variables, with no ISO. Re-run the commands above and the sample hash. Offline-inspect the new EFI/GRUB/support files and both firmware slots. Gate passes only when the expected kernel, DOM geometry, boot exclusion, HAL mapping and test volume/hash all agree.

Online update discovery is a separate experiment: the isolated `restrict=on` QEMU network cannot reach QNAP. Do not call offline manual installation proof of automatic discovery or scheduled installation.

## 3. Upgrade an existing custom QTS installation

This is the reference **X77-to-X73A family change**. It is not a vendor-supported cross-model firmware update. Preserve the existing early-init identity/geometry guards, and use a copied boot image as the build base instead of installing a fresh community image over working configuration.

### 3.1 Record and shut down

While the original system still works, record its exact firmware/kernel, boot menu, device serials/geometry, `/sbin/dmsetup table`, bay-to-serial mapping, RAID/pool/tier/volume states and file hashes. Export configuration using QTS **Control Panel → System → Backup/Restore**, and retain private copies of the custom overlay/model and any application-specific settings. Configuration exports can contain secrets and are not data backups.

Stop writes and shut down normally. Confirm power is off before disconnecting the complete data set; photograph/label each cable and disk. Keep unrelated OS/data disks isolated. Boot SystemRescue in UEFI mode through virtual CD with `copytoram checksum nomdlvm ar_disable`.

### 3.2 Make a consistent offline boot backup

Identify `BOOT_ID`/`BOOT_DEV` with the exact serial, size, mounts, swap and holders checks in [walkthrough section 8](10-command-walkthrough.md#8-write-the-physical-boot-ssd-destructive-explicit-target). Mount an **independent backup destination**, not the boot SSD or an original pool member. Then:

```bash
# Rescue only; BOOT_DEV is the identity-verified whole boot SSD.
BACKUP_DIR='/mnt/REPLACE_INDEPENDENT_BACKUP/qts-before-upgrade'
case "$BACKUP_DIR" in *REPLACE*) echo 'Mount and select independent backup storage'; exit 1;; esac
mkdir -m 700 "$BACKUP_DIR"
findmnt -T "$BACKUP_DIR"
df -h "$BACKUP_DIR"
blockdev --getsize64 "$BOOT_DEV"
sgdisk -p "$BOOT_DEV" > "$BACKUP_DIR/partition-table.txt"
sgdisk --backup="$BACKUP_DIR/gpt.bin" "$BOOT_DEV"
efibootmgr -v > "$BACKUP_DIR/uefi.txt"
# Full clone: destination must have room for the entire SSD.
# If using a sparse backup, verify how the destination filesystem handles holes.
test ! -e "$BACKUP_DIR/boot-before.img" || exit 1
dd if="$BOOT_DEV" of="$BACKUP_DIR/boot-before.img" bs=4M conv=fsync status=progress || exit 1
cmp -n "$(blockdev --getsize64 "$BOOT_DEV")" "$BOOT_DEV" "$BACKUP_DIR/boot-before.img" || exit 1
sha256sum "$BACKUP_DIR/boot-before.img" > "$BACKUP_DIR/boot-before.img.sha256"
```

Stop on any failure. The physical case instead backed up the complete **8 GiB DOM span plus the last 1 MiB and GPT metadata**, after proving all boot partitions/configuration were inside that span; this was not a full 500 GB clone. Do not use that optimization without proving your own layout and unused tail. It does not reduce the need for independent data backups. Store another verified boot copy off the NAS.

### 3.3 Build on a copy, preserving the working boot contract

On the Linux build host, create a fresh private work directory. Retain the offline backup untouched, then copy it to `private/qts-boot.img`. Select the Beta firmware in walkthrough sections 1a–2 and extract it to `private/fw`. Inspect the copied image and assert the known geometry using section 3; extract p1 and p7 as `private/parts/efi.fat` and `private/parts/support.ext`. **Do not run the section-3 `cp base.img` line over this copied backup.**

Read the actual GRUB file to identify the support archive path. It may be `/profile.cpio.gz` in the public walkthrough or `/qtier-map.cpio.gz` in the original case. Use the same name in every read/write command below. For the public name:

```bash
mcopy -i private/parts/efi.fat ::/grub/grub.cfg private/grub.before.cfg
cat private/grub.before.cfg
debugfs -R 'dump /profile.cpio.gz private/profile.before.cpio.gz' private/parts/support.ext
sha256sum private/profile.before.cpio.gz
python3 tools/prepare_release_overlay.py --base private/profile.before.cpio.gz \
  --track x73a --disable-optional-mods --output private/profile.cpio.gz
cat private/profile.cpio.review.json
```

The conservative public candidate changes the examined model identity fields and removes only the recognized optional late-mod hook if present. All disk/boot identity and geometry guards remain byte-identical, as do other archive members. It does **not** remove unknown helpers, account rules, binary patches or diagnostic assumptions. Inspect your source first; an unfamiliar wrapper is a manual engineering task, not a reason to weaken the checks. The physical case retained its separately validated optional adapter instead. Re-enable optional monitoring only after release-specific tests in section 5.

For readers with a basic public overlay and no optional mods, the same command changes only the model. For private archives with other helpers, inspect those helpers and stop if they embed old kernel paths or unvalidated side effects. Build a new diagnostic archive with the selected model and `templates/diagnostic-init.example`; its module path follows `uname -r`.

```bash
# Extract only the model from the reviewed new archive (regular file, no execution).
python3 - <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, 'tools')
from build_mod_overlay import unpack
members = dict((n, d) for n, d, mode in unpack(Path('private/profile.cpio.gz').read_bytes()))
Path('private/model.conf').write_bytes(members['qts-profile/model.conf'])
PY
python3 tools/pack_overlay.py --model private/model.conf \
  --init templates/diagnostic-init.example --output private/diagnostic.cpio.gz
```

Build the two firmware-slot files and replace p2/p3 using **only the slot loop** in walkthrough section 5. In the offline support filesystem, remove just the previous overlay inode before writing the new archive, then read back:

```bash
debugfs -w -R 'rm /profile.cpio.gz' private/parts/support.ext
debugfs -w -R 'write private/profile.cpio.gz /profile.cpio.gz' private/parts/support.ext
# Inspect first. If /diagnostic.cpio.gz already exists, remove that inode only.
debugfs -R 'stat /diagnostic.cpio.gz' private/parts/support.ext
# Run the next rm only if the preceding stat confirmed this existing file:
# debugfs -w -R 'rm /diagnostic.cpio.gz' private/parts/support.ext
debugfs -w -R 'write private/diagnostic.cpio.gz /diagnostic.cpio.gz' private/parts/support.ext
e2fsck -fn private/parts/support.ext
python3 tools/image_parts.py replace private/qts-boot.img 7 private/parts/support.ext
```

`debugfs` exit status is not proof of success; the shared section-5 readback/`cmp` checks are required. Keep the original p1/GRUB if it already loads the reviewed overlay and offers a diagnostic entry. Otherwise edit only its menu configuration in the extracted p1 using the shared template and actual UUID/archive path, then write p1 back with the file helper. Do not replace EFI executables just to change a model. Keep p5/p6 and all other copied regions unchanged. Compare final p1/p5/p6 with their backup extractions (except an intentionally reviewed GRUB edit), and read back the new p2/p3/p7 exactly as in the shared walkthrough.

### 3.4 Install and reconnect

Package the validated regular-file candidate as the shared payload ISO. With data disks still disconnected, repeat the explicit boot-SSD identity/holder checks and write/readback procedure in walkthrough section 8. The shared writer handles both smaller boot-span candidates and full-size clone candidates: it clears a stale target tail only when that tail is strictly outside the image. For a full clone, verify `IMAGE_BYTES == BOOT_BYTES`; do not clear its tail separately. Never install the lab-profile image onto the physical host.

Boot from the SSD without virtual CD. With no data disks attached, Smart Installation is expected; do not initialize a replacement disk to get past it. Confirm kernel/firmware, boot identity and DOM mappings through diagnostics/authorized console. Shut down, reconnect the **complete** old QNAP set and verify every physical bay in the diagnostic entry. An unplugged Qtier SSD tier must be reconnected with the HDD tier.

Then boot normal QTS and follow the shared [migration](06-migration.md) and [acceptance](07-acceptance.md) steps. Original configuration can restore a different address, custom web port and old accounts. Wait for storage startup; do not reset the system because the initial installer address stopped responding. Stop on an initialization offer, missing member, unexpected pool or degraded tier.

## 4. Rollback boundary

Before the new firmware has booted with the original data set, restore the verified offline boot backup using the same explicit-target checks (and the recorded tail/GPT backup if you used a bounded backup). Recheck the old hash, original boot menu and version. Do not overwrite the wrong NVMe by trusting `nvme0` enumeration.

After normal 6.1 startup has touched the pool, **restoring the boot SSD alone is not a validated downgrade**. Stop writes, preserve the current disks, and use your independent recovery copy/export or a storage-aware recovery plan. Both update slots can be rewritten by the updater; the second slot is not a guaranteed previous-version backup.

## 5. Compatibility findings and fixes

| Area | Observed difference / pitfall | What to do |
|---|---|---|
| Device mapper | The bounded DOM design survived the tested kernel change | Compare all `dmsetup table` entries and backing identity; boot SSD must remain absent from data choices |
| HAL bay mapping | A scan can list disks even while reverse lookup fails | Require per-disk slot/serial lookup success. Physical bay swaps must be recorded, not “fixed” by guessed indices |
| Diagnostic module | Hard-coded `5.10.60-qnap` cannot load the 6.1 module | Use `/lib/modules/$(uname -r)/hal_netlink.ko` from the running firmware |
| Python | Optional adapters must tolerate installed Python 2.7/3.12 locations | Use a capability-tested runtime launcher; do not assume `/usr/local/bin/python` or a complete stdlib |
| HAL lifecycle | Startup took about 21 seconds; `daemon_mgr` can return 1 on a completed transition | Use bounded waits plus registration/PID/fresh-reading verification. Never kill the spawned monitor's process group on a client timeout |
| Sensor cache | CPU/system/fan cache can outlive a failed monitor; `TEMP_1` is the verified motherboard field | Verify an active monitor and fresh HAL readings against real BMC sensors; stale UI numbers are not success |
| CPU widget | 6.1 has a native temperature widget handling `cpuTempC` | Keep it intact; do not transplant the legacy 5.2 widget patch |
| Memory/cache eligibility | VM DIMM metadata may be incomplete; bay mask depends on the actual mapped slots | Verify SMBIOS/HAL readback. Synthetic VM fixtures never become production sensor/DIMM data |
| Artwork | Old TS-877 target SVG paths may disappear under X73A | Prefer native X73A artwork; skip stale cosmetic replacements without blocking storage |
| Container networking | Host-network qBittorrent bound internal bridges and caused repeated ICMP local-route warnings | Verify actual sockets/routes. In this case binding BT traffic to the real uplink stopped warnings; do not globally suppress kernel logging or copy the interface name onto another host |
| Thermal shutdown | Thresholds inherited from an appliance need review against actual hardware | Read config and the fresh HAL-loaded log; the case's operator-selected CPU91 is not a universal recommendation or a tested heat-shutdown event |

The public optional helper now includes the portable parts of these findings: capability-based release checks with protected mappings retained, available-Python selection, a 35-second monitor transition bound, preservation of a spawned monitor on client timeout, native 6.1 widget detection, mapped-bay cache masks and `TEMP_1` cache validation. These helpers are optional and still require a private board profile; they do not contain the production thermal override or broad sudo rule. This documentation revision tests the public changes offline; it does not claim a new physical boot of this exact public package.

Read-only monitoring checks on the destination:

```sh
sed -n '/\[SHUTDOWN TEMP\]/,/^$/p' /etc/hal_util.conf
grep 'SHUTDOWN TEMP CPU' /var/log/hal_daemon.log | tail -1
ps | grep '[h]al_daemon'
for p in /sys/class/hwmon/hwmon*; do
  echo "$p"; cat "$p/name"; cat "$p"/temp*_input 2>/dev/null
done
grep -E '^(CPUT_1|TEMP_1|FANR_1|FANR_2)[[:space:]]*=' /tmp/em/em_0.info
```

Do not automatically raise thresholds or restart protection during high load. The later one-off high-load change was explicitly operator-authorized; it is not part of installation. Passwordless sudo, private account rules, raw logs and host-specific overlays are not published as defaults.

[← Release choices](02a-release-tracks.md) · [Shared installation commands](10-command-walkthrough.md) · [Updates and rollback →](08-updates.md)
