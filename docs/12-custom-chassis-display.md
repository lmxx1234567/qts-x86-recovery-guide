# Customize the chassis preview

[Task index](../README.md#read-in-this-order)

**Optional after:** [storage acceptance](07-acceptance.md) and a verified [HAL bay map](05-bay-mapping.md#acceptance-table). For sensor/widget problems rather than drawings, use [hardware checks](07a-hardware-and-apps.md#cpu-motherboard-and-fan-readings).

Use a chassis drawing that matches your enclosure without changing the NAS model, network configuration or disk enumeration. This guide covers an **eight-bay enclosure with an ASRock Rack X570D4U-2L2T**, using the **TS-873A profile on QTS 6.1.0, build 20261007**. Complete storage recovery and verify the disks before making cosmetic changes.

The example provides eight front trays, power/reset buttons, two vertical front USB sockets and a rear panel with four business LAN ports. The dedicated IPMI connector remains separate. Four rear expansion covers describe the enclosure; the motherboard itself has three PCIe slots.

![Original QTS preview beside the custom front and rear](../assets/chassis/before-after-270px.png)

*Equal-width SVG renders of the original and custom previews.*

![Light and dark preview examples with neutral and selected states](../assets/chassis/transparent-light-dark.png)

*Example selections, not live device status. The dark view uses simulated theme rules.*

## 1. Prepare the drawings

Start with the [front](../assets/chassis/custom-front.svg) and [rear](../assets/chassis/custom-rear.svg) vector designs. These contain physical-position IDs and no visible labels. They are design sources, **not universal drop-in replacements**: prepare QTS-adapted copies with the native slot and network IDs before installation. For QTS integration, preserve each logical `hd_N` group and its direct child `rect`, use `ethernet_N` wrappers around the corresponding LAN shapes, and keep `.off` / `.on` state classes. QTS supplies the page-specific styles and click bindings.

Keep the background and unselected interior transparent. Let QTS control selection colors and theme strokes; do not add a full white canvas or use inline colors that override state styles. Some QTS pages intentionally fill an unselected slot, so a transparent source does not imply that every application state is transparent.

Check both large previews and small thumbnails. Retain a clear outer outline and lighter internal details. USB, HDMI, VGA, COM, fan vents and expansion covers should remain static unless you have verified a matching state source. Do not infer an installed PCIe card from a chassis cover.

## 2. Calibrate the ports and bays

Use the [board's official rear I/O diagram](https://download.asrock.com/Manual/X570D4U-2L2T.pdf) (printed page 12). The regular X570D4U is a different model. For this drawing, LAN2 is above LAN1 in the i210 pair, and LAN4 is above LAN3 in the X550 pair.

The following is an **example display layout**, not a guarantee of interface order on another installation:

| Physical connector | Example QTS label | Example interface | SVG selector |
|---|---|---|---|
| i210 upper, LAN2 | Adapter 2 | `eth1` | `ethernet_1` |
| i210 lower, LAN1 | Adapter 1 | `eth0` | `ethernet_0` |
| X550 upper, LAN4 | Adapter 4 | `eth5` | `ethernet_3` |
| X550 lower, LAN3 | Adapter 3 | `eth4` | `ethernet_2` |

The i210 pair in this example still needs physical verification. Check every port on your own host:

1. Record each QTS adapter's display name, Linux interface and native `physical_location` selector. Identify its controller with existing system information or read-only `ethtool -i <interface>` output.
2. Match the physical connector using cable labels or an existing switch port/MAC table. Keep address records private. Do not derive upper/lower order from MAC values, PCI function order or adapter numbering alone.
3. Set the SVG wrapper ID for that connector, then select each adapter in QTS and check that only the intended connector highlights. Correct the display mapping if necessary; do not rename real interfaces to fit the drawing.
4. If physical evidence is missing, leave that relationship unbound until it can be checked. No cable disconnection or network reconfiguration is needed for this display work.

“Adapter 4” is not Linux `eth4`. The IPMI RJ45 is not a fifth QTS business adapter: keep it outside the `ethernet_N` mapping. Independent BMC status is not implemented by these drawings.

For disks, retain `hd_0`–`hd_7` as logical SVG groups and verify their relationship to the existing [HAL bay mapping](05-bay-mapping.md). Do not assume `hd_0` means Disk 1: backend slot IDs can account for M.2, U.2 and other devices. Selecting a tray in the interface must not change the underlying disk order.

## 3. Back up and install the adapted SVGs

Use an existing authorized maintenance session. Only these display resources should change:

```text
/home/httpd/v3_menu/layout/ts_873a_0.svg
/home/httpd/v3_menu/layout/ts_873a_1.svg
```

1. Check the firmware/build, current SVG hashes, ownership/modes and `model_0.svg` / `model_1.svg` symlink targets against your reviewed baseline. Stop if they differ unexpectedly.
2. Save both originals, their hashes and metadata in a protected persistent directory; keep an independent copy off the NAS. Also preserve the current custom version before applying a later correction.
3. Stage each reviewed SVG in the same filesystem as its target. Preserve the original owner and mode, validate XML and IDs, and verify the staged hash before replacing anything.
4. Replace each file by atomic rename. The two-file operation is not a single transaction: if it fails partway, restore the saved pair and verify both hashes before continuing.
5. Leave the model symlinks, internal M.2 view (`ts_873a_2.svg`), product icons, JavaScript, CSS and model-list JSON unchanged.

Do not change the firmware model merely to obtain a different picture. This procedure does not require a NAS reboot, service restart or storage operation.

## 4. Verify the result

- Fetch both direct SVG URLs and both `/v3_menu/layout/model_0.svg` / `model_1.svg` aliases. Confirm HTTP success and matching hashes; this verifies delivery, not browser interaction.
- Reopen the relevant QTS panels or refresh the client. Check the front/rear previews, small layouts and the mobile light/dark appearance.
- Select and clear each adapter and tray. Confirm independent highlights, correct physical positions and intact tooltips. A green example in a rendered figure is not evidence of a connected cable or healthy disk.
- Check every page you use. Network details, storage and hardware previews can inject different styles; one working page does not prove all of them.

## 5. Restore after startup and handle updates

For automatic restoration, use a reviewed, host-specific guard through QNAP's [user-defined startup mechanism](https://www.qnap.com/en/how-to/faq/article/running-your-own-application-at-startup). This enables root execution at boot. Back up any existing autorun content, add only a distinct restoration block, and keep the guard, manifests and payloads in a root-owned directory that ordinary users cannot modify. The public design files are not a ready-made startup installer.

The guard should wait for resources without blocking startup, do nothing when the approved patch is already present, and restore only known original files whose firmware and frontend protocol checks match. It must retain backups and touch only the two SVGs. Check the firmware/build, model links, full SVG hashes and frontend JS/CSS/JSON hashes before permitting a restore.

After an upgrade, an unfamiliar firmware, frontend or SVG must **stop restoration rather than be overwritten**. The new vendor artwork can remain active until you review and adapt it. Inspect the guard's status before changing its baseline:

```sh
RUNTIME_DIR=/REPLACE/PROTECTED/runtime
case "$RUNTIME_DIR" in *REPLACE*) echo "Set your installation directory first"; exit 1;; esac
sudo cat "$RUNTIME_DIR/STATUS.txt"
sudo /bin/sh "$RUNTIME_DIR/guard.sh" --check
```

Set `RUNTIME_DIR` to your protected installation directory. `OK_ALREADY_APPLIED` means no replacement was needed; `STOP_NEEDS_REVIEW` means inspect the reported mismatch. Do not approve a new version simply to silence the check. Recheck the native IDs, styles, interactions and rollback copy first.

### Roll back or remove restoration

Disable the restoration block before a rollback that should remain in place. Require the expected current patch hash and matching backup hash, stage the saved originals with their metadata, replace the same two SVGs, and verify delivery again. Stop if the current files are an unfamiliar later version.

To remove startup restoration, mount the configuration through the official QNAP helper, back up the current autorun content and remove only your marked block. Preserve any other startup tasks. Disable the user-startup switch only when no remaining task needs it, and unmount the temporary configuration afterward. Keep the backups instead of deleting the recovery path.

## Compatibility scope

This example was checked on the stated QTS build for live resource delivery, native slot-protocol behavior and an installed guard's idempotent execution. Physical reboot and firmware-upgrade persistence are not covered by that validation. Use your own acceptance checks before relying on automatic restoration, and do not treat this configuration as a universal hardware profile.

**After installation:** complete [preview and selection checks](#4-verify-the-result). Before firmware maintenance, review [restoration compatibility and rollback](#5-restore-after-startup-and-handle-updates) alongside [general update planning](08-updates.md).
