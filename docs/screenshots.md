# Preview gallery

[Task index](../README.md#read-in-this-order)

**Reference only:** choose an image for the check you are performing; follow the [task index](../README.md#read-in-this-order) for the procedure.

Use these views to identify the fields to check on your own NAS. Screenshots show sampled state; they do not replace disk identity, file integrity or boot validation. English pages use English UI captures or text-free artwork. [Chinese UI captures](screenshots.zh-CN.md) are kept separately.

## Check hardware information

![QTS 5.2 CPU, memory topology and disk temperatures](../assets/screenshots/hardware-status-native-en.jpg)

Check total memory, populated/empty slots and each supported temperature against the actual hardware. This capture predates board-sensor integration; “Not Supported” is the state of that capture. Use [sensor verification](07a-hardware-and-apps.md#cpu-motherboard-and-fan-readings) for the current adapter checks.

## Check disk identity and selection

![Eight SATA disks in Storage & Snapshots](../assets/screenshots/eight-disks-native-en.jpg)

All eight positions are listed. “Free” means not allocated by QTS; it does not mean the disk contains no data or is safe to initialize.

![Eight-bay front preview and disk details](../assets/screenshots/eight-bay-preview-native-en.jpg)

Compare each selection with the accepted [HAL bay map](05-bay-mapping.md). A picture alone cannot establish physical slot order.

## Check Qtier membership

![SSD RAID1 and HDD RAID5 tiers in QTS 5.2](../assets/screenshots/qtier-native-en.jpg)

Both populated tiers are present and tiering is Idle. The unused middle tier is not a missing member. Verify pool/RAID membership and files using [storage acceptance](06-migration.md#a-concrete-storage-and-file-checklist); see [reference results](case-study.md) for the measured reboot and upgrade scope.

## Inspect cache eligibility without creating a cache

![Cache candidate list with no disks selected](../assets/screenshots/cache-candidates-native-en.jpg)

Zero disks are selected. Candidate visibility is a separate check from cache suitability or permission to erase a disk. Cancel after inspection; follow [cache eligibility guidance](07a-hardware-and-apps.md#ssd-cache-candidates-a-slot-capability-bitmap) before changing settings.

## Compare custom enclosure previews

![Original and custom front/rear artwork at equal width](../assets/chassis/before-after-270px.png)

![Light and simulated dark appearance](../assets/chassis/transparent-light-dark.png)

These are SVG renders with example selections, not live telemetry. The dark view uses simulated theme rules. Follow the [chassis guide](12-custom-chassis-display.md) to calibrate ports and trays, install adapted resources and verify actual QTS pages.

**Related:** [reference results](case-study.md) · [Chinese UI gallery](screenshots.zh-CN.md).
