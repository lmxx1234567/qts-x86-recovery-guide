# 3. Validate using disposable virtual disks

[Task index](../README.md#read-in-this-order)

**Before you start:** prepare the [selected firmware and loader inputs](02-firmware.md#build-inputs). Build commands are in [walkthrough sections 1–6](10-command-walkthrough.md#1-build-machine-and-directory-layout).

Use the selected stable/Beta variables from [release selection](02a-release-tracks.md). The [6.1 VM update procedure](11-qts61-upgrade.md#2-test-the-native-update-in-a-disposable-vm) adds an actual native TS-X73A 5.2→6.1 update and cold start; it does not replace these common storage and boot gates.

For concrete commands and environment prerequisites, use the [ordered command walkthrough](10-command-walkthrough.md). Read this chapter for its acceptance gates and limitations.

Use an isolated VM before attaching original disks. The case used 2 vCPUs, 8 GiB RAM, a 64 GiB virtual NVMe boot disk and a new 256 GiB SATA data disk, with autostart disabled and no physical passthrough. Use a private network to avoid duplicate source IPs/hostnames.

## Build and start the lab in order

A boot image is needed before VM validation, even though physical installation is chapter 4. Complete walkthrough [sections 1–5](10-command-walkthrough.md#1-build-machine-and-directory-layout) using the **VM profile**, then run [section 6](10-command-walkthrough.md#6-run-the-disposable-qts-vm). Do not run the physical writer to prepare a VM.

1. On the Linux build host, confirm `/dev/kvm` exists and your account can use it. If the build host is itself a VM, nested virtualization must be available. An ARM Mac cannot use this x86 KVM command directly; use an x86-64 Linux host or separately validate an emulation setup.
2. Use the OVMF CODE/VARS pair installed on that host. Copy VARS once for this VM; reuse the same writable copy on subsequent boots so firmware settings persist. Never point the VM at a physical block device.
3. Launch the documented QEMU command. Its first entry is diagnostic and intentionally does not open the QTS web UI. Capture its HAL output, terminate only this disposable diagnostic VM through its host controls, relaunch it, and manually choose **QTS** for initialization.
4. Open `http://127.0.0.1:18080` on the machine running QEMU. If your browser is on another machine, use an SSH tunnel to that host, for example `ssh -N -L 18080:127.0.0.1:18080 BUILD_USER@BUILD_HOST`, then open the same URL locally. Replace both placeholders; do not expose this test service publicly.
5. Complete Smart Installation **only in this disposable lab**. Record the temporary account and settings. If storage creation is deferred, open Storage & Snapshots and create a test pool/volume on the sole disposable SATA disk. The boot NVMe must not be a selectable data target. If it is, stop and correct the profile.
6. In File Station, upload a known file from your workstation to a test share on the new volume. Record its original hash (`sha256sum test-file` on Linux or `shasum -a 256 test-file` on macOS). Download it to a separate local folder after each test and compare hashes. A visible filename alone is not a read test.

The example forwarding assumes QTS HTTP port 8080 and SSH port 22 inside the guest. If you change guest ports or force HTTPS, update the matching forwarding rule after shutdown; a stale forwarding rule is not evidence of a storage failure. The restricted network is intentional; upload firmware from the browser rather than relying on an internet update check in the guest.

## Save, restart and restore a checkpoint

Use QTS's shutdown action, wait until QEMU exits, then copy **boot.qcow2, data.qcow2 and vars.fd together** using the [checkpoint commands](10-command-walkthrough.md#6-run-the-disposable-qts-vm). Relaunch with the same command and existing files; do not repeat the `qemu-img create`, resize or initial VARS-copy steps. A complete process exit followed by a new launch is the lab's cold start.

To restore, stop QEMU, preserve the failed state under another directory, and copy all three files from the same checkpoint into the active VM directory. Never restore only the boot disk against newer storage state. Record which checkpoint and firmware each result belongs to. For the upgrade action itself, follow [manual update steps](11-qts61-upgrade.md#2-test-the-native-update-in-a-disposable-vm).

## Required sequence

1. Boot the candidate from its own UEFI/GRUB path. Remove QEMU `-kernel`, `-initrd` and `-append` shortcuts; otherwise you are not testing disk boot.
2. Verify the boot device identity and that the installer offers only the disposable SATA disk as data storage.
3. Save an offline snapshot of **both** virtual disks, partition geometry, GPT identifiers, EFI files and support overlay hashes.
4. Initialize only this disposable VM and create a test data volume. Write a known test file and record its size/hash.
5. Shut the VM down completely, then cold-start it. Verify login, configuration, volume and file.
6. Take another consistent checkpoint; run the official firmware update with sufficient staging space.
7. Check updater completion/status and signatures. Power off, then cold-start twice from disk without maintenance ISO or direct kernel parameters.
8. Compare partition geometry, EFI files, support files, runtime firmware version, pool and test file.

Do not modify backing images used by existing QCOW2 snapshots. A checkpoint of only the boot disk is not a consistent snapshot of the storage system. Never interpret a VM startup result as hardware-driver validation.

## Observed version path

QTS 5.1.6.2722 build 20240402 → 5.2.10.3577 build 20260731 succeeded through the official update path. Initialization and subsequent cold boots succeeded. A 1 MiB test file retained its checksum. The partition locations/GUIDs and first MiB remained unchanged. The updater rewrote both firmware slots; it preserved the adaptation files on the support partition in this test.

The EFI directory acquired additional official files. Existing EFI executable and GRUB configuration hashes stayed the same. Whole-filesystem hashes can change because of metadata even if all relevant files are identical. Compare both file manifests and geometry.

## Troubleshoot failed validation

- In the tested TrueNAS configuration, `UEFI_CSM` actually took the legacy boot path. Select and verify UEFI rather than trusting a label.
- Using a bounded device-mapper view did not by itself remove the underlying NVMe from the installer. Verify the actual installer disk list.
- Treating the remaining SSD tail as a FLASH data device failed to produce a usable data disk. The final design uses a separate data pool.
- For FW004, inspect the update log and free staging space. Staging under `/mnt/HDA_ROOT` can be too small; use a verified test-data volume with enough space. The code can have other causes.

**After the VM gates pass:** [collect the physical controller topology](05-bay-mapping.md#concrete-linux-topology-collection), then [build a separate physical candidate](04-build-and-install.md).
