# Command walkthrough: from downloads to recovery

This fills the operational gaps between the conceptual chapters. Run it in order, reading each gate. Commands target a **disposable Linux x86-64 build machine**, then a **maintenance boot on the destination NAS**. Do not paste the entire page into a shell. Commands in different sections run on different machines.

The complete example is the observed X77 DOM layout. Other hardware needs its own driver/HAL profile; other loader layouts need a reviewed adaptation of the partition steps. This command transcription and the new image helper have offline tests; the whole sequence has **not** been freshly rerun on physical hardware. The earlier installation/VM results are described separately in the case study.

## 1. Build machine and directory layout

Use Bash on a disposable Debian/Ubuntu x86-64 Linux VM with at least 20 GiB free space for build files; the separate QTS test VM needs additional space. A Mac can host this Linux VM, but do not run Linux device commands against macOS disks. Build dependencies are installed on the build VM, not on the recovering NAS:

```bash
sudo apt-get update
sudo apt-get install -y git curl unzip build-essential python3 e2fsprogs \
  gdisk util-linux mtools xorriso qemu-system-x86 qemu-utils ovmf
# Install your distribution's 7-Zip package with RAR extraction support
# only if the community loader is supplied as a RAR archive.
git clone https://github.com/lmxx1234567/qts-x86-recovery-guide.git
cd qts-x86-recovery-guide
mkdir -p private/input private/unpacked private/fw private/parts private/verify private/stage/boot
```

All following build commands run from this repository root. `private/` is ignored by Git. Never publish its reports or firmware. Keep paths free of spaces for the `debugfs` examples below. Commands assume Python 3.9 or newer and GNU userland. Keep the build shell stopped at any unexpected error; snippets are separate inspection gates, not one unattended script.

Download the selected official QNAP firmware ZIP, SystemRescue ISO and vendor checksum/signature files through their official sites. Obtain the community base loader separately through the provenance links in [sources](sources.md). Retain the download URL and hash locally. Do not use an unknown loader on original disks just because it has the same filename.

For the historical version, the official package URL was:

```bash
curl --fail --location --output private/input/TS-X77_20260731-5.2.10.3577.zip \
  https://download.qnap.com/Storage/TS-X77/TS-X77_20260731-5.2.10.3577.zip
sha256sum private/input/* > private/downloads.sha256
wc -c private/input/*
```

A locally computed hash is an identity record, not authentication. Use the publisher's signature/checksum verification instructions too. If the historical package is unavailable, do not silently substitute another family/build: restart the version-validation gate.

Extract the community archive in the disposable build VM, inspect its contents, and copy the **raw disk image** to `private/input/base.img`. Do not rename a QNAP update `.img` into `base.img`. Keep the source archive unchanged. Confirm `file private/input/base.img`, then inspect its partition table.

## 2. Extract the official firmware payload

The historical update package required PC1 extraction. Download and review the community source in the disposable VM; it is not bundled or covered by this repository's MIT license. Pin the revision you reviewed in your local record instead of relying indefinitely on `master`.

```bash
curl --fail --location --output private/pc1.c \
  https://raw.githubusercontent.com/mkke/qnap-recovery/master/pc1.c
sha256sum private/pc1.c
# Read the source before compiling/running it.
less private/pc1.c
```

The examined source reads four bytes into a `long`. The local experiment initialized that variable to avoid an uninitialized upper half on a 64-bit platform. Apply the narrowly checked edit only if the reviewed source matches:

```bash
python3 - <<'PY'
from pathlib import Path
p=Path('private/pc1.c');s=p.read_text()
old='long filesize, encrypted_len, block_size;'
if s.count(old)!=1: raise SystemExit('Source differs: review before adapting')
Path('private/pc1-local.c').write_text(s.replace(old,'long filesize, encrypted_len = 0, block_size;'))
PY
cc -O2 -fwrapv -fsigned-char -o private/pc1 private/pc1-local.c
unzip -l private/input/TS-X77_20260731-5.2.10.3577.zip
unzip -n private/input/TS-X77_20260731-5.2.10.3577.zip -d private/unpacked
private/pc1 d QNAPNASVERSION4 \
  private/unpacked/TS-X77_20260731-5.2.10.3577.img private/firmware.tgz
```

The extractor's exit code alone is insufficient (the examined `main` did not propagate every decryption error). Check the reported model/version and validate the decompressed archive. Some historical packages had trailing data; do not accept a corrupt compressed stream by ignoring all extraction errors.

```bash
python3 - <<'PY'
import zlib
from pathlib import Path
raw=Path('private/firmware.tgz').read_bytes()
d=zlib.decompressobj(16+zlib.MAX_WBITS)
plain=d.decompress(raw)+d.flush()
if not d.eof: raise SystemExit('Incomplete gzip stream')
# zlib checks the gzip CRC. Trailing bytes are recorded, not parsed as payload.
print('Decompressed bytes:',len(plain),'Trailing bytes:',len(d.unused_data))
Path('private/firmware.tar').write_bytes(plain)
PY
tar -tf private/firmware.tar > private/firmware-members.txt
less private/firmware-members.txt
```

Extract only flat boot payload names, not arbitrary archive paths:

```bash
python3 - <<'PY'
import tarfile
from pathlib import Path
base={'bzImage','initrd.boot','rootfs2.bz','rootfs_ext.tgz','qpkg.tar'}
out=Path('private/fw');seen=set()
with tarfile.open('private/firmware.tar','r:') as t:
    for item in t:
        n=item.name.removeprefix('./')
        if '/' in n or not any(n==b or n.startswith(b+'.') for b in base): continue
        if not item.isfile() or n in seen: raise SystemExit('Unexpected type or duplicate: '+n)
        seen.add(n)
        with t.extractfile(item) as src, (out/n).open('xb') as dst: dst.write(src.read())
if not base.issubset(seen): raise SystemExit('Missing boot payload: '+str(base-seen))
print('Extracted:',sorted(seen))
PY
sha256sum private/fw/* > private/firmware-files.sha256
```

If the package layout differs, stop and inspect it. These commands do not authenticate firmware or replace the official updater's signature checks. Do not mix payload/signature files from different versions.

## 3. Record the base image layout

```bash
python3 tools/image_parts.py inspect private/input/base.img > private/geometry.json
cat private/geometry.json
sgdisk -v private/input/base.img
```

`image_parts.py` accepts regular files only, checks primary GPT CRC/bounds, and preserves partition length during replacement. It does not validate every backup-GPT field or filesystem; `sgdisk -v` and filesystem checks remain necessary.

For **this example only**, assert the layout before proceeding:

```bash
python3 - <<'PY'
import json
p=json.load(open('private/geometry.json'))
expected={1:(2048,32768),2:(34816,1048576),3:(1083392,1048576),
          5:(2131968,16384),6:(2148352,16384),7:(2164736,5535711)}
for n,(start,sectors) in expected.items():
    if (p[str(n)]['start'],p[str(n)]['sectors'])!=(start,sectors):
        raise SystemExit('Different loader layout: stop and adapt, do not force')
print('Observed example layout matches')
PY
cp --reflink=auto --no-clobber private/input/base.img private/qts-boot.img
python3 tools/image_parts.py extract private/qts-boot.img 1 private/parts/efi.fat
python3 tools/image_parts.py extract private/qts-boot.img 7 private/parts/support.ext
mdir -i private/parts/efi.fat ::/
mdir -i private/parts/efi.fat ::/grub
mcopy -i private/parts/efi.fat ::/grub/grub.cfg private/grub.original.cfg
```

If `::/grub/grub.cfg` is absent, inspect the actual base loader. Do not install an unrelated GRUB over it. Never reuse stale build output directories: exclusive-output helpers intentionally fail when files already exist.

## 4. Make separate VM and physical profiles

Start with the complete [VM case profile](../templates/case-vm-model.conf) for the VM topology below, or the [physical case profile](../templates/case-x570-model.conf) only as a structure reference for hardware adaptation. The incomplete generic model template is **not directly bootable**.

For the lab build:

```bash
cp templates/case-vm-model.conf private/model.conf
cp templates/init.example private/init
python3 - <<'PY'
from pathlib import Path
p=Path('private/init');s=p.read_text()
values={'REPLACE_BOOT_SERIAL':'QTSLABONLY0001',
        'REPLACE_EXACT_512_BYTE_SECTOR_COUNT':'134217728',
        'REPLACE_DOM_SECTORS':'16777216',
        'REPLACE_PARTITION_TABLE':'1 2048 32768\n2 34816 1048576\n3 1083392 1048576\n5 2131968 16384\n6 2148352 16384\n7 2164736 5535711'}
for k,v in values.items():s=s.replace(k,v)
p.write_text(s)
PY
sh -n private/init
python3 tools/pack_overlay.py --model private/model.conf --init private/init --output private/profile.cpio.gz
python3 tools/pack_overlay.py --model private/model.conf --init templates/diagnostic-init.example --output private/diagnostic.cpio.gz
```

For the physical build, repeat in a fresh private work directory with the **real boot SSD serial and 512-byte-sector count** from rescue inventory, and the verified real controller/network/bay profile. Do not write the VM-profile image to the NAS. Include each required platform CAP/network field; copying only `[System Disk]` is insufficient. See [mapping](05-bay-mapping.md). Physical port mappings are established by hardware evidence, not a universal conversion from `ataN`.

## 5. Assemble firmware slots, support and GRUB

These commands touch **regular local files only**, not mounted partitions or physical disks. They follow the asserted layout above.

```bash
cp private/fw/* private/stage/boot/
for n in 2 3; do
  test ! -e "private/parts/slot$n.ext" || exit 1
  truncate -s 536870912 "private/parts/slot$n.ext"
  mke2fs -q -F -t ext2 -b 1024 -I 128 -m 0 -L "QTS_BOOT_PART$n" \
    -d private/stage "private/parts/slot$n.ext"
  e2fsck -fn "private/parts/slot$n.ext" || exit 1
  python3 tools/image_parts.py replace private/qts-boot.img "$n" "private/parts/slot$n.ext"
done
debugfs -w -R 'write private/profile.cpio.gz /profile.cpio.gz' private/parts/support.ext
debugfs -w -R 'write private/diagnostic.cpio.gz /diagnostic.cpio.gz' private/parts/support.ext
e2fsck -fn private/parts/support.ext
SUPPORT_UUID=$(blkid -p -s UUID -o value private/parts/support.ext)
test -n "$SUPPORT_UUID" || exit 1
```

If either support filename already exists, start with a fresh base copy or deliberately replace it in the offline partition file; `debugfs write` will not overwrite an existing inode. Its process exit status is not enough: read back below.

```bash
cat > private/grub.cfg <<EOF_GRUB
set default=0
set timeout=-1
insmod all_video
insmod part_gpt
insmod fat
insmod ext2
menuentry 'QTS diagnostic - no normal storage startup' --id qts-diagnostic {
 search --no-floppy --label --set=root QTS_BOOT_PART3
 search --no-floppy --fs-uuid --set=profile $SUPPORT_UUID
 linux /boot/bzImage root=/dev/ram0 rw console=tty0 rdinit=/sbin/init init=/sbin/init raid=noautodetect
 initrd /boot/initrd.boot (\$profile)/diagnostic.cpio.gz
}
menuentry 'QTS' --id qts-normal {
 search --no-floppy --label --set=root QTS_BOOT_PART3
 search --no-floppy --fs-uuid --set=profile $SUPPORT_UUID
 linux /boot/bzImage root=/dev/ram0 rw console=tty0 raid=noautodetect
 initrd /boot/initrd.boot (\$profile)/profile.cpio.gz
}
EOF_GRUB
mcopy -o -i private/parts/efi.fat private/grub.cfg ::/grub/grub.cfg
mcopy -i private/parts/efi.fat ::/grub/grub.cfg private/verify/grub.cfg
cmp private/grub.cfg private/verify/grub.cfg
python3 tools/image_parts.py replace private/qts-boot.img 1 private/parts/efi.fat
python3 tools/image_parts.py replace private/qts-boot.img 7 private/parts/support.ext
```

`timeout=-1` intentionally waits. Only after diagnostic and storage validation should the permanent menu default be changed to `qts-normal` with a short timeout. Do not leave a diagnostic environment automatically rebooting into an uncontrolled default OS.

Read back **from the final image**, including signatures and both overlays:

```bash
for n in 1 2 3 7; do
  python3 tools/image_parts.py extract private/qts-boot.img "$n" "private/verify/final-p$n"
done
cmp private/parts/efi.fat private/verify/final-p1
cmp private/parts/support.ext private/verify/final-p7
for n in 2 3; do
  cmp "private/parts/slot$n.ext" "private/verify/final-p$n" || exit 1
  for f in private/fw/*; do
    name=$(basename "$f")
    debugfs -R "dump /boot/$name private/verify/p$n-$name" "private/verify/final-p$n"
    cmp "$f" "private/verify/p$n-$name" || exit 1
  done
done
for name in profile diagnostic; do
  debugfs -R "dump /$name.cpio.gz private/verify/$name.cpio.gz" private/verify/final-p7
  cmp "private/$name.cpio.gz" "private/verify/$name.cpio.gz" || exit 1
done
sgdisk -v private/qts-boot.img
sha256sum private/qts-boot.img > private/qts-boot.img.sha256
stat -c '%s' private/qts-boot.img > private/qts-boot.img.bytes
```

Any missing file or mismatch blocks installation. A whole-image hash identifies this private build, not a universal known-good release.

## 6. Run the disposable QTS VM

Use [VM validation](03-vm-validation.md) for the full acceptance sequence. The following launch reproduces the case's PCI device addresses on a standalone Linux QEMU i440fx machine; it is a command translation, not a new validated hypervisor matrix.

```bash
mkdir -p private/vm
qemu-img convert -f raw -O qcow2 private/qts-boot.img private/vm/boot.qcow2
qemu-img resize private/vm/boot.qcow2 64G
qemu-img create -f qcow2 private/vm/data.qcow2 256G
ls /usr/share/OVMF/
# Use the matching non-Secure-Boot CODE/VARS pair installed by your distribution.
cp /usr/share/OVMF/OVMF_VARS_4M.fd private/vm/vars.fd
qemu-system-x86_64 -machine pc,accel=kvm -cpu host -smp 2 -m 8192 \
  -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd \
  -drive if=pflash,format=raw,file=private/vm/vars.fd \
  -device pci-bridge,id=labbridge,chassis_nr=1,addr=0x5 \
  -drive file=private/vm/boot.qcow2,if=none,id=qtsboot,format=qcow2 \
  -device nvme,drive=qtsboot,serial=QTSLABONLY0001,bus=labbridge,addr=0x0 \
  -device ich9-ahci,id=labahci,addr=0x7 \
  -drive file=private/vm/data.qcow2,if=none,id=qtsdata,format=qcow2 \
  -device ide-hd,drive=qtsdata,bus=labahci.0,serial=QTSLABDATA0001 \
  -netdev user,id=labnet,restrict=on,hostfwd=tcp:127.0.0.1:18080-:8080,hostfwd=tcp:127.0.0.1:10022-:22 \
  -device e1000e,netdev=labnet,addr=0x6 \
  -vga std -boot menu=on
```

No physical passthrough, direct kernel boot, public VNC listener or autostart is used. Run the graphical console locally on the build host; when accessing a remote build host, use its authorized console/SSH tunnel rather than exposing the forwarded ports. `/dev/kvm` access is a host prerequisite. If KVM is unavailable, resolve virtualization access or explicitly test a different accelerator; don't count an unbooted VM as passed.

Run diagnostic first. It stops indefinitely; power off the disposable VM through its host controls after capturing output, then start again and select normal QTS. Open `http://127.0.0.1:18080` **on the build host**. Initialize only the new SATA disk; verify the 64 GiB NVMe is absent from data choices. Follow the wizard, create a small test volume using the disposable SATA device, record a test file, and cold-boot. Update through QTS **Control Panel → System → Firmware Update → Manual Installation**, selecting the exact official update package supported by that UI. Record completion and run the same cold-boot checks. If an older-to-newer test is required, build the older boot image first; booting only the new version does not test an upgrade.

For consistent checkpoints, shut the VM down fully and confirm the QEMU process has exited before copying all state into a newly named checkpoint directory:

```bash
# Only after QEMU has stopped; choose a new name at each gate.
mkdir private/vm/checkpoint-before-update
cp --reflink=auto --sparse=always private/vm/boot.qcow2 private/vm/data.qcow2 \
  private/vm/vars.fd private/vm/checkpoint-before-update/
```

Save another checkpoint after initialization and after the verified update. Never copy a running QCOW2 as if it were a consistent backup. Resizing the virtual disk may leave the inherited GPT backup at the original image boundary; do not repair/expand it automatically during the update-preservation experiment.

## 7. Build the physical candidate and payload ISO

Create a separate checkout (for example, clone this repository into `qts-physical-build`), enter it, create the section-1 `private/` directories, and copy the previously reviewed `base.img` plus extracted `fw/` files there. Repeat sections 3–5 with the physical boot serial, size, full profile and tested firmware. Replace the lab profile values in section 4 rather than executing its lab substitution unchanged. Retain the VM candidate separately. Name the final **physical** image `qts-boot.img` only after readback verification. Package it without inventing a bootable ISO:

```bash
mkdir -p private/payload
cp private/qts-boot.img private/payload/qts-boot.img
(cd private/payload && sha256sum qts-boot.img > SHA256SUMS)
xorriso -as mkisofs -r -J -V QTS_PAYLOAD -o private/qts-payload.iso private/payload
sha256sum private/qts-payload.iso
```

This ISO is a **data disc**. First boot SystemRescue ISO in UEFI mode with `copytoram checksum nomdlvm ar_disable`; confirm rescue is loaded in RAM, then use BMC virtual media to replace the ISO with `qts-payload.iso`. Inspect `lsblk -o NAME,TYPE,LABEL,SIZE,MOUNTPOINTS` to find the virtual CD. Mount its actual device read-only, e.g. `sudo mount -o ro /dev/sr0 /mnt` if inspection identified sr0. Then `(cd /mnt && sha256sum -c SHA256SUMS)`. Do not assume the BMC preserved media attachment after a session expiry.

## 8. Write the physical boot SSD (destructive, explicit target)

Before using the physical candidate, verify x86-64 UEFI boot support and the candidate EFI loader's trust requirements in your firmware. Secure Boot compatibility was not validated; do not assume a community loader is signed. Verify SATA/NVMe/NIC PCI IDs against the selected QTS kernel, not only the rescue kernel.

Run in **SystemRescue on the destination NAS**, not on the build host. Original QNAP data disks should remain disconnected at this stage. A different installed OS disk may remain only if its identity and exclusion are explicit. The following intentionally requires manual identity confirmation; it is not an auto-detect installer.

```bash
lsblk -b -o NAME,PATH,TYPE,SIZE,MODEL,SERIAL,WWN,MOUNTPOINTS
ls -l /dev/disk/by-id/
# Set the exact observed whole-disk by-id link, never a -partN link.
BOOT_ID='/dev/disk/by-id/REPLACE_VERIFIED_BOOT_SSD_ID'
case "$BOOT_ID" in *REPLACE*) echo 'Set the actual identity first'; exit 1;; esac
BOOT_DEV=$(readlink -f "$BOOT_ID")
test -b "$BOOT_DEV" || exit 1
# This loader is a 512-byte logical-sector image; 4Kn requires a different design.
test "$(blockdev --getss "$BOOT_DEV")" = 512 || exit 1
test "$(lsblk -dn -o TYPE "$BOOT_DEV")" = disk || exit 1
lsblk -b -o NAME,TYPE,SIZE,MODEL,SERIAL,MOUNTPOINTS "$BOOT_DEV"
udevadm info --query=property --name="$BOOT_DEV" | grep -E 'ID_MODEL=|ID_SERIAL=|ID_WWN='
findmnt
swapon --show
cat /proc/mdstat
lsblk -nr -o KNAME "$BOOT_DEV" | while read -r node; do
  echo "Holders for $node:"
  ls -l "/sys/class/block/$node/holders/"
done
```

Stop if any target child is mounted, swap-active, held by MD/DM/LVM, or used by another process. Do not automatically stop an array to make the writer proceed. Check `fuser -v "$BOOT_DEV"` plus each target child as appropriate. Compare serial, model and exact bytes with the private physical build manifest. The image wrapper must contain this same identity.

With checks complete and the target's entire contents intentionally disposable, keep this shell session and run:

```bash
IMAGE=/mnt/qts-boot.img
(cd /mnt && sha256sum -c SHA256SUMS) || exit 1
IMAGE_BYTES=$(stat -c '%s' "$IMAGE")
BOOT_BYTES=$(blockdev --getsize64 "$BOOT_DEV")
test "$IMAGE_BYTES" -gt 0 && test "$IMAGE_BYTES" -le "$BOOT_BYTES" || exit 1
EXPECTED_SERIAL=$(lsblk -dn -o SERIAL "$BOOT_DEV" | xargs)
test -n "$EXPECTED_SERIAL" || exit 1
printf 'Erase boot SSD %s (%s bytes). Type its verified serial: ' "$BOOT_DEV" "$BOOT_BYTES"
read -r CONFIRM_SERIAL
test "$CONFIRM_SERIAL" = "$EXPECTED_SERIAL" || exit 1
# Recheck that the identity link has not changed since inspection.
test "$(readlink -f "$BOOT_ID")" = "$BOOT_DEV" || exit 1
# Clear stale backup-GPT/signature bytes only at this erasable target's tail.
# The image is smaller than the SSD in this design; enforce a non-overlapping tail.
test "$BOOT_BYTES" -gt "$((IMAGE_BYTES + 1048576))" || exit 1
test "$((BOOT_BYTES % 512))" -eq 0 || exit 1
dd if=/dev/zero of="$BOOT_DEV" bs=512 seek="$((BOOT_BYTES / 512 - 2048))" count=2048 conv=notrunc,fsync status=progress || exit 1
dd if="$IMAGE" of="$BOOT_DEV" bs=4M conv=notrunc,fsync status=progress || exit 1
sync
# Compare exactly the written image length; the unused SSD tail is not in the image.
cmp -n "$IMAGE_BYTES" "$IMAGE" "$BOOT_DEV" || exit 1
blockdev --rereadpt "$BOOT_DEV"
lsblk -o NAME,SIZE,FSTYPE,LABEL,PARTUUID "$BOOT_DEV"
```

These are manual root-level commands, not a race-proof writer. Keep disks/cables stable and other storage managers inactive during the operation. If any command fails, stop and inspect; do not continue with a partial image. Do not run `sgdisk -e`, grow filesystems, initialize the SSD tail or format data disks as a cleanup step.

Detach payload CD. Boot the physical diagnostic entry, verify every intended bay, then follow [migration](06-migration.md). If the diagnostic cannot see original member disks because they are disconnected, shut down and attach the recorded set before the diagnostic-only pass. Do not select normal QTS until the mapping gate is satisfied. Normal QTS startup is write-capable.

## 9. First storage boot, access and verification commands

After the gate, select normal QTS. Do not click Smart Installation on old disks. Wait for boot progress. If the web port changes after old configuration is restored, an authorized console can read:

```sh
/sbin/getcfg System 'Web Access Port' -f /etc/config/uLinux.conf
ip -br addr
ip route
ss -lnt     # if unavailable on this build, use netstat -lnt
cat /proc/mdstat
mount
df -h
```

Command availability varies; use the console's installed alternatives rather than installing packages during recovery. Inspect **Storage & Snapshots** for the original pool, RAID groups, member identities, volumes and both Qtier tiers. The manual “Attach and Recover Storage Pool” branch applies to a previously initialized destination, not automatically to every migration. See the decision branch in [chapter 6](06-migration.md); if QTS proposes initialization, stop.

Use a known existing file on each recovered volume:

```sh
# Replace the path locally; never paste private names into public reports.
sha256sum '/share/REPLACE_VOLUME/REPLACE_EXISTING_FILE'
```

Compare with the pre-migration manifest, or state that this is a post-recovery read check only. The read-only manifest tool can be run from a maintenance/build environment that already has legitimate access to the recovered files; do not assume Python is installed on QTS.

## 10. Make QTS the default and test without media

In a UEFI-booted maintenance environment, identify the boot SSD again and mount **its EFI partition only**, using its actual by-id partition link. Back up `/grub/grub.cfg` off-device. Change the generated menu's `set default=0` to `set default=qts-normal` and `set timeout=-1` to `set timeout=3`, then read the file back and unmount it. Check that the `qts-normal` menu ID exists before changing the default.

```bash
# Replace with the verified EFI partition link for the dedicated boot SSD.
ESP_ID='/dev/disk/by-id/REPLACE_BOOT_ID-part1'
case "$ESP_ID" in *REPLACE*) echo 'Set verified EFI partition'; exit 1;; esac
mkdir -p /mnt/qts-efi
mount "$ESP_ID" /mnt/qts-efi
cp /mnt/qts-efi/grub/grub.cfg /mnt/qts-efi/grub/grub.before-default.cfg
# Inspect/edit with the editor available in your maintenance environment.
nano /mnt/qts-efi/grub/grub.cfg
cat /mnt/qts-efi/grub/grub.cfg
sync
umount /mnt/qts-efi
efibootmgr -v
```

If absent, create QTS's UEFI entry using the inspected whole boot device and ESP number (chapter 7 gives the pattern). If present, reuse it. Record the original BootOrder; place the verified QTS entry first while preserving others:

```bash
# Example only: replace ALL numbers with this machine's existing entries.
# efibootmgr -o QTS_ENTRY,OTHER_ENTRY_1,OTHER_ENTRY_2
# If a stale BootNext is listed, remove that one-time override:
# efibootmgr -N
efibootmgr -v
```

Detach virtual CD, then reboot normally without manual menu selection. Confirm web/SSH, runtime version, every RAID member, tiers, volumes and files again. Record a full power-off/start separately if performed. Keep the off-device boot backup and independent data backup before considering updates.
