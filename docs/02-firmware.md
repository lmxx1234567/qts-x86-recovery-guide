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

These are the specific inputs used in the experiment, not a compatibility guarantee for other hardware or a recommendation to use an older release.

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

The resulting `.img` still needs the firmware extraction procedure in the [command walkthrough](10-command-walkthrough.md). It is **not** the raw DOM image to write to an SSD. Both official ZIP URLs returned HTTP 200 when checked on 2026-10-19; future availability and community download permissions may change.

## Build inputs

Follow [walkthrough sections 1–5](10-command-walkthrough.md) to obtain or create each item below. Inputs 3–5 are built locally, not additional vendor downloads. Select the firmware once; the remaining workflow is shared.

1. An independently obtained bootable DOM/EFI base image with known partition geometry.
2. Extracted official boot payload for one selected firmware version, including its associated signature/checksum files.
3. A hardware-specific `model.conf` and guarded early-init wrapper.
4. A diagnostic entry that stops before normal QTS initialization.
5. A separate support partition holding the overlay, outside both firmware update slots.
6. A bootable maintenance ISO and a way to deliver the locally built payload.

The original two firmware slots were p2/p3, support was p7, and EFI was p1. These numbers belong to that base image. Inspect yours; do not invent partitions or expand its GPT to use the SSD tail during recovery.

---

<!-- stage-navigation -->
[← Previous: Inventory and backup](01-inventory.md) · [Workflow index](../README.md#read-in-this-order) · [Next: Choose a release →](02a-release-tracks.md)
<!-- /stage-navigation -->
