# 2. Firmware, loader and dependencies

<!-- stage-navigation -->
[← Previous: Inventory and backup](01-inventory.md) · [Workflow index](../README.md#read-in-this-order) · [Next: Choose a release →](02a-release-tracks.md)
<!-- /stage-navigation -->

For concrete commands and environment prerequisites, use the [ordered command walkthrough](10-command-walkthrough.md). Read this chapter for its acceptance gates and limitations.

## Select a family, not a CPU marketing name

Choose [Track A: current QTS 5.2 stable or Track B: QTS 6.1 Beta](02a-release-tracks.md) before downloading. The original installation used TS-877 / TS-X77, QTS 5.2.10.3577 and kernel 5.10.60-qnap; the later physical upgrade used TS-873A / TS-X73A, QTS 6.1.0.3640 and kernel 6.6.129-qnap. These are tested observations, not permanent version pins. Check current security advisories and download availability at the [official download center](https://www.qnap.com/en/download).

A newer AMD-based QNAP does not automatically offer a better compatible image. Compare the kernel, storage/NIC drivers, HAL/model configuration, boot layout and updater behavior. The X77, X77U and X77AX packages examined during this work were not interchangeable merely because the kernel version string matched. An examined X77AX package also contained EFI/GRUB replacement material, making preservation of a custom boot path a separate test.

Record URL, retrieval date, exact filename, byte length and SHA-256 for every dependency. Verify vendor signatures/checksums where provided. A hash you calculate yourself identifies a file; it does not establish its authenticity.

## Dependency boundary

This repository contains original documentation and helper code. It does **not** contain the QNAP kernel, initramfs, firmware, patched binaries, or a third-party DOM/EFI image. The observed installation depended on a community `x77-dom` image. That dependency has not been independently audited here. Review its provenance and applicable license before using it; do not upload it into this repository.

A QNAP firmware `.img` inside a download ZIP is an **update package**, not a raw boot-disk image. Writing it directly to an SSD is not the procedure used here. Extraction in the experiment used the community qnap-recovery PC1 utility; see [sources](sources.md). Confirm the extractor handles integer widths correctly on your build platform and verify the extracted payload. Do not disable firmware signature checks to make an update appear successful.

### Historical downloads used in the first 5.2 case

For current stable/Beta URLs and the exact shell variables used by both routes, use [Release selection](02a-release-tracks.md). The older links below explain the initial experiment; they are not the latest stable selection.

Use these older inputs only when reproducing the reference validation; they are not a recommendation to stay on an older release.

| Input | Download | Contents and role |
| --- | --- | --- |
| Community DOM base | [`x77-dom.img.rar` (Google Drive)](https://drive.google.com/file/d/1g9cLcbQGZ8kRv7Cjorn_Ylc3mc8xrO2q/view) | Archive containing the raw `x77-dom.img` boot-disk image; the starting point for the custom boot layout. |
| QTS 5.2.10.3577, build 20260731 | [Official TS-X77 ZIP](https://download.qnap.com/Storage/TS-X77/TS-X77_20260731-5.2.10.3577.zip) | Contains `TS-X77_20260731-5.2.10.3577.img`; used for the final installation and as the VM upgrade destination. |
| QTS 5.1.6.2722, build 20240402 | [Official TS-X77 ZIP](https://download.qnap.com/Storage/TS-X77/TS-X77_20240402-5.1.6.2722.zip) | Contains `TS-X77_20240402-5.1.6.2722.img`; the earlier version used in the VM upgrade test. |

The DOM archive was retrieved on 2026-10-17 from the [community distribution folder](https://drive.google.com/drive/folders/1lC-Gh0TF7ZxUy12YqoTg8nGEY7whfC6W), linked by the [source tutorial](https://blog.hx99.net/Tech/2015.html). Its extracted raw image was 3,942,645,760 bytes and dated 2022-06-10; the retrieval date is not its build date. See [sources and provenance](sources.md) for the extraction utility.

For example, download and inspect the final official package with:

```sh
curl --fail --location --output TS-X77_20260731-5.2.10.3577.zip \
  https://download.qnap.com/Storage/TS-X77/TS-X77_20260731-5.2.10.3577.zip
unzip -l TS-X77_20260731-5.2.10.3577.zip
unzip TS-X77_20260731-5.2.10.3577.zip -d firmware-5.2.10.3577
```

The resulting `.img` still needs the firmware extraction procedure in the [command walkthrough](10-command-walkthrough.md). It is **not** the raw DOM image to write to an SSD. Verify download availability and provenance before building.

## Build inputs

The six inputs have different sources: download the DOM base, firmware and rescue ISO; adapt the configuration and init scripts from this repository; then generate the overlays, boot menu and payload ISO locally. There is no single universal installer to download.

Prepare a disposable Linux x86-64 build VM first. The [build-machine setup](10-command-walkthrough.md#1-build-machine-and-directory-layout) lists packages, directories and space requirements. All `private/` paths below are relative to that checkout. Build and inspect regular image files there; physical SSD writing is a later, separate step.

### 1. DOM/EFI base image: obtain and inspect the boot-disk skeleton

**Obtain it:** download the community archive in the [table above](#historical-downloads-used-in-the-first-52-case), extract it with a RAR-capable tool in the build VM, and retain the original archive. Copy the extracted raw `x77-dom.img` to `private/input/base.img`. The base supplies the existing partition layout and EFI/GRUB loader. It is neither a maintenance ISO nor the official QNAP update package.

**Requirements and checks:**

- Record the source, archive and image hashes, byte lengths and extracted filenames. Inspect the source's provenance and licensing separately; this repository does not audit or distribute the loader.
- The destination needs a compatible x86-64 UEFI boot path. Secure Boot compatibility was not established. A file named `.img` is not evidence that it contains a bootable disk.
- This recipe assumes 512-byte logical sectors and the specific partition geometry checked in the walkthrough. A different base image or 4Kn target requires adapting the design, not bypassing those checks.
- Inspect both GPT and filesystems, locate the actual EFI executable and GRUB configuration, and preserve an untouched base copy. The image file must fit the intended boot SSD; that SSD is separate from the original pool members.

Start with these non-writing checks on the regular image file:

```sh
file private/input/base.img
sha256sum private/input/base.img
python3 tools/image_parts.py inspect private/input/base.img > private/geometry.json
cat private/geometry.json
sgdisk -v private/input/base.img
```

**Ready when:** the layout is recorded, partition checks are understood, and the existing loader/configuration can be read. Continue with [base-image inspection and copying](10-command-walkthrough.md#3-record-the-base-image-layout). Bootability is subsequently tested in the disposable VM; passing GPT inspection alone does not prove it.

### 2. Official boot payload: extract one complete firmware build

**Obtain it:** download the official ZIP for the selected stable/Beta family in [release selection](02a-release-tracks.md), unzip it, then extract its inner update `.img` using the reviewed PC1 utility. The [firmware extraction commands](10-command-walkthrough.md#2-extract-the-official-firmware-payload) cover obtaining and compiling the utility, its historical integer-width fix, gzip validation and extracting only the expected archive members.

The expected output in `private/fw/` for this case is:

| File | Role in this build |
| --- | --- |
| `bzImage` | QNAP Linux kernel loaded by GRUB. |
| `initrd.boot` | Vendor initial RAM filesystem, loaded before the local overlay. |
| `rootfs2.bz`, `rootfs_ext.tgz`, `qpkg.tar` | Remaining vendor system/application payload retained in the firmware slots. |
| Associated signature/checksum files present in the package | Kept alongside their corresponding payload, from the same build. |

**Requirements and checks:** use one exact family/build throughout; do not combine an old initramfs, a new kernel and unrelated signatures. The rescue kernel detecting a controller does not prove that the QNAP kernel has the same driver. Verify storage and network support with the selected QTS kernel in diagnostic boot. Keep signature checks enabled. PC1 returning without an error is insufficient: verify the compressed stream, archive contents, required files and recorded hashes. The narrowly checked source edit in the walkthrough applies to the examined extractor, not every future revision.

**Ready when:** all required payload and companion files have been extracted into a fresh directory, the reported model/build is correct, and extraction validation passes. The [assembly commands](10-command-walkthrough.md#5-assemble-firmware-slots-support-and-grub) copy this set into both firmware slots and read it back. Two identical populated slots are not an old-version rollback backup.

### 3. Hardware profile and early-init wrapper: adapt the templates

**Obtain them:** start with [the generic model template](../templates/model.conf.example), [the complete VM example](../templates/case-vm-model.conf), [the physical case example](../templates/case-x570-model.conf), and [the init wrapper](../templates/init.example). The generic template is incomplete; the complete examples describe their own hardware and must not be assumed portable.

`model.conf` tells QTS HAL how the platform presents controllers, bays, network devices and capabilities. Collect the target's PCI paths, controller-relative ports and disk identities using [bay mapping](05-bay-mapping.md), then build a separate physical profile. Map every intended bay, including expansion bays; mark empty bays unverified until tested with a known disposable disk. Do not equate Linux `sdX`, `sgN` or global `ataN` order with physical bay numbering. Sensor and cache capabilities need separate validation from disk visibility.

The wrapper runs before normal QTS init. In this NVMe design it finds the boot SSD by serial, checks its size and partition geometry, creates the expected DOM device-mapper views, installs the local `model.conf`, and then hands off to BusyBox init. Fill in:

- `BOOT_SERIAL`: the intended boot SSD's actual serial, not a data disk's serial.
- `BOOT_SECTORS`: its full size in 512-byte sectors, not its marketed GB capacity.
- `DOM_SECTORS`: the length of the emulated DOM view; validate it against the target size and mapped layout. This is distinct from full SSD capacity.
- `PARTITIONS`: the verified partition number, start and length table, in 512-byte sectors.

The supplied wrapper searches NVMe namespaces. A SATA/USB boot device needs a reviewed adaptation of discovery and mapping; changing only the serial is insufficient. VM serials, sizes and PCI paths are lab settings, not physical-machine defaults. The wrapper's checks constrain boot-device mapping; they do not make a normal QTS storage startup read-only.

Follow [profile preparation](10-command-walkthrough.md#4-make-separate-vm-and-physical-profiles), then pack the reviewed files:

```sh
sh -n private/init
python3 tools/pack_overlay.py --model private/model.conf --init private/init \
  --output private/profile.cpio.gz
```

**Ready when:** placeholders are resolved, shell syntax passes, and the generated overlay contains the intended configuration. The packer rejects unresolved `REPLACE_` markers, but does not validate hardware semantics. The required physical acceptance is correct disk identities and successful HAL reverse lookup, not merely successful packaging.

### 4. Diagnostic entry: generate a separate inspection boot path

**Obtain it:** combine your reviewed `private/model.conf` with [the diagnostic init template](../templates/diagnostic-init.example):

```sh
python3 tools/pack_overlay.py --model private/model.conf \
  --init templates/diagnostic-init.example --output private/diagnostic.cpio.gz
```

The diagnostic overlay replaces `/sbin/init`, loads the matching `hal_netlink` module, runs the scan and per-disk HAL queries, and stays stopped instead of starting normal QTS storage services. The normal overlay is separate. Follow the [GRUB assembly section](10-command-walkthrough.md#5-assemble-firmware-slots-support-and-grub) to create both menu entries with the vendor `initrd.boot` first and the appropriate local overlay second.

**Requirements and checks:** confirm that the target firmware contains the commands/modules used by the template. Capture the full console output externally; the template does not automatically save a log. Check every populated bay's model/serial, slot and reverse-query return value. A scan listing all disks while individual queries fail is a failed mapping gate. The diagnostic entry is intended to avoid normal storage startup, not a hardware write blocker or a guarantee against every possible kernel write.

**Ready when:** the diagnostic entry boots the intended kernel, runs the expected checks and remains stopped without falling through to normal QTS. Initially keep it as the default with an indefinite menu wait. Change to the normal default only after mapping and storage acceptance.

### 5. Support partition: reuse the inspected base layout and install overlays

**Obtain it:** this is an existing partition of the case's DOM base, not another download and not a new volume carved out of an original data disk. In this image, p1 holds EFI, p2/p3 are the firmware slots, and p7 holds the local support files. Other base images may differ.

The [assembly procedure](10-command-walkthrough.md#5-assemble-firmware-slots-support-and-grub) extracts p7 into the regular file `private/parts/support.ext`, writes `profile.cpio.gz` and `diagnostic.cpio.gz` into it, reads its filesystem UUID, and makes GRUB find it by that UUID. It then replaces the same partition-sized region in the candidate image. The helper preserves the original partition length.

**Requirements and checks:** confirm the filesystem type, free space and actual contents before writing. Do not format an unidentified support partition. Use a fresh build directory: `debugfs write` will not replace an existing file, and its process status alone is not enough to verify success. Read back the overlays from the final assembled image and compare them with their inputs; check that GRUB references the correct support UUID and firmware label.

Keeping the overlays outside p2/p3 separates them from the observed firmware-slot writes. It does not guarantee that every future updater leaves EFI, the partition table or p7 untouched. Validate each proposed update in a disposable VM and retain a full boot-image backup. Do not expand the GPT or turn the boot SSD's unused tail into a data volume during recovery.

**Ready when:** both overlays and GRUB configuration match their source files on readback, filesystem/layout checks pass, and the final boot image has a recorded byte length and hash. The support partition is not the QTS system volume that hosts applications on the recovered pool.

### 6. Maintenance ISO and payload delivery: prepare two different discs

**Obtain the bootable environment:** download the amd64 ISO and its checksum/signature from the [official SystemRescue download page](https://www.system-rescue.org/Download/), and follow its verification instructions. The case used `systemrescue-13.02-amd64.iso`. Test that the destination can boot it in UEFI mode through BMC virtual CD or local boot media and that the rescue environment can identify the boot SSD by serial.

**Generate the payload disc locally:** after building and reading back the physical candidate, follow [physical candidate and payload ISO](10-command-walkthrough.md#7-build-the-physical-candidate-and-payload-iso). `xorriso` packages `qts-boot.img` and `SHA256SUMS` into `qts-payload.iso`. This second ISO is a **non-bootable data disc**, not a QTS installer. The repository does not provide a prebuilt image containing vendor binaries.

For a BMC with one virtual CD slot, boot SystemRescue with `copytoram checksum nomdlvm ar_disable`, confirm it has loaded into RAM, then replace the rescue ISO with the payload ISO. Provide enough RAM for the rescue image and working space; the SystemRescue download page specifies at least 4 GB when caching into RAM. After switching media, inspect the actual CD device, mount it read-only and verify `SHA256SUMS` again. BMC session expiry can disconnect virtual media, and the device is not guaranteed to be `/dev/sr0`.

**Ready when:** rescue is running independently of the first disc, the payload is accessible and its checksum matches, and the intended disposable boot SSD is positively identified. Only then proceed to [physical writing](10-command-walkthrough.md#8-write-the-physical-boot-ssd-destructive-explicit-target). Original pool disks are not installation targets. Finally remove virtual media and verify an independent boot from the SSD; a successful boot with the rescue or payload disc still attached is not the final acceptance test.

---

<!-- stage-navigation -->
[← Previous: Inventory and backup](01-inventory.md) · [Workflow index](../README.md#read-in-this-order) · [Next: Choose a release →](02a-release-tracks.md)
<!-- /stage-navigation -->
