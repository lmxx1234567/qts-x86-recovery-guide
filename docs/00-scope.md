# 0. Scope and recovery decisions

<!-- stage-navigation -->
[← Project overview](../README.md) · [Workflow index](../README.md#read-in-this-order) · [Next: Inventory and backup →](01-inventory.md)
<!-- /stage-navigation -->

## Identify the storage family first

| Source | Applicability |
|---|---|
| QTS, Linux MD/LVM/ext4, including Qtier | Covered by this guide; validate the exact source and destination |
| QuTS hero / ZFS | Different recovery stack; do not apply the QTS Qtier assembly procedure |
| QuTScloud | Different product and licensing/deployment model; not a substitute firmware image |
| Legacy static volume or encrypted volume | Inventory its actual layout and keys; this Qtier case does not validate it |
| Missing/failing members or inconsistent metadata | Image first; do not force assembly or allow an automatic rebuild on originals |

The goal is access to data. Keeping QTS as a permanent operating system is optional. If a supported replacement QNAP is available, evaluate that route first. If only file extraction is needed, a controlled recovery environment and a separate destination may be preferable.

## Use the examples safely

The [reference results](case-study.md) describe one tested build. Procedures and example profiles still need the runtime checks specified in each chapter. Treat any unverified feature as unavailable until you test it.

Generic means the method is portable: inventory, adapt, test, recover, verify. It does not mean the sample PCI paths, model profile, disk geometry or firmware can be copied to every x86 machine.

## Three independent identities

Record physical bay, immutable drive identity (serial/WWN), and OS device path separately. `/dev/sda`, `/dev/sg0` and `/dev/nvme0n1` can change between boots and operating systems. The machine's UEFI boot entry and GRUB's default menu entry are also separate settings.

## Stop conditions

Stop before normal QTS storage startup if a member is missing, serials do not match, HAL reverse lookup fails, or a recovery dialog proposes initialization. Stop after startup if the wrong disks appear in the pool, a rebuild starts unexpectedly, tier membership differs, or encrypted data cannot be unlocked with known keys. Preserve logs and return to copies; do not improvise `mdadm --create`, `--force`, `pvcreate`, `vgcfgrestore` or filesystem repair on originals.

---

<!-- stage-navigation -->
[← Project overview](../README.md) · [Workflow index](../README.md#read-in-this-order) · [Next: Inventory and backup →](01-inventory.md)
<!-- /stage-navigation -->
