# 3. Validate using disposable virtual disks

For concrete commands and environment prerequisites, use the [ordered command walkthrough](10-command-walkthrough.md). Read this chapter for its acceptance gates and limitations.


Use an isolated VM before attaching original disks. The case used 2 vCPUs, 8 GiB RAM, a 64 GiB virtual NVMe boot disk and a new 256 GiB SATA data disk, with autostart disabled and no physical passthrough. Use a private network to avoid duplicate source IPs/hostnames.

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

## Lessons

- In the tested TrueNAS configuration, `UEFI_CSM` actually took the legacy boot path. Select and verify UEFI rather than trusting a label.
- Using a bounded device-mapper view did not by itself remove the underlying NVMe from the installer. Verify the actual installer disk list.
- Treating the remaining SSD tail as a FLASH data device failed to produce a usable data disk. The final design uses a separate data pool.
- An initial update failed with FW004 because staging under `/mnt/HDA_ROOT` ran out of space. Retrying on a real data volume with sufficient space succeeded. FW004 can have other causes; inspect logs.
