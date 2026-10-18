# 2. Firmware, loader and dependencies

<!-- stage-navigation -->
[← Previous: Inventory and backup](01-inventory.md) · [Workflow index](../README.md#read-in-this-order) · [Next: VM validation →](03-vm-validation.md)
<!-- /stage-navigation -->

For concrete commands and environment prerequisites, use the [ordered command walkthrough](10-command-walkthrough.md). Read this chapter for its acceptance gates and limitations.


## Select a family, not a CPU marketing name

The observed profile was TS-877 / TS-X77, with QTS 5.2.10.3577 build 20260731 and kernel 5.10.60-qnap. This is a tested version, not a recommendation to install it forever. Check current security advisories and download availability at the [official download center](https://www.qnap.com/en/download).

A newer AMD-based QNAP does not automatically offer a better compatible image. Compare the kernel, storage/NIC drivers, HAL/model configuration, boot layout and updater behavior. The X77, X77U and X77AX packages examined during this work were not interchangeable merely because the kernel version string matched. An examined X77AX package also contained EFI/GRUB replacement material, making preservation of a custom boot path a separate test.

Record URL, retrieval date, exact filename, byte length and SHA-256 for every dependency. Verify vendor signatures/checksums where provided. A hash you calculate yourself identifies a file; it does not establish its authenticity.

## Dependency boundary

This repository contains original documentation and helper code. It does **not** contain the QNAP kernel, initramfs, firmware, patched binaries, or a third-party DOM/EFI image. The observed installation depended on a community `x77-dom` image. That dependency has not been independently audited here. Review its provenance and applicable license before using it; do not upload it into this repository.

A QNAP firmware `.img` inside a download ZIP is an **update package**, not a raw boot-disk image. Writing it directly to an SSD is not the procedure used here. Extraction in the experiment used the community qnap-recovery PC1 utility; see [sources](sources.md). Confirm the extractor handles integer widths correctly on your build platform and verify the extracted payload. Do not disable firmware signature checks to make an update appear successful.

## Build inputs

1. An independently obtained bootable DOM/EFI base image with known partition geometry.
2. Extracted official boot payload for one selected firmware version, including its associated signature/checksum files.
3. A hardware-specific `model.conf` and guarded early-init wrapper.
4. A diagnostic entry that stops before normal QTS initialization.
5. A separate support partition holding the overlay, outside both firmware update slots.
6. A bootable maintenance ISO and a way to deliver the locally built payload.

The original two firmware slots were p2/p3, support was p7, and EFI was p1. These numbers belong to that base image. Inspect yours; do not invent partitions or expand its GPT to use the SSD tail during recovery.

---

<!-- stage-navigation -->
[← Previous: Inventory and backup](01-inventory.md) · [Workflow index](../README.md#read-in-this-order) · [Next: VM validation →](03-vm-validation.md)
<!-- /stage-navigation -->
