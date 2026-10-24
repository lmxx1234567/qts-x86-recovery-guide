# Sources and provenance

[Task index](../README.md#read-in-this-order)

**Use with:** [release selection](02a-release-tracks.md) and [build-input requirements](02-firmware.md#build-inputs). Sources establish provenance, not hardware compatibility.

Reviewed while documenting the case on 2026-10-18. External pages and downloads can change. Official appliance documentation is context, not certification of generic x86 hardware.

## Primary documentation

- [QNAP NAS migration compatibility](https://www.qnap.com/en/nas-migration)
- [QNAP: migrated disks not shown as a pool](https://www.qnap.com/en-ca/how-to/faq/article/what-should-i-do-if-migrated-disks-are-not-shown-as-storage-pool-qnap-nas)
- [QNAP: moving data to a new NAS](https://www.qnap.com/en-us/how-to/faq/article/i-bought-a-new-qnap-nas-how-do-i-move-my-data-over-from-the-old-one)
- [QNAP download center](https://www.qnap.com/en/download)
- [QNAP security advisories](https://www.qnap.com/en/security-advisories)
- [SystemRescue boot options](https://www.system-rescue.org/manual/Booting_SystemRescue/)
- [GNU ddrescue manual](https://www.gnu.org/software/ddrescue/manual/ddrescue_manual.html)

## Community build dependencies

The community loader was obtained as [`x77-dom.img.rar` (file page)](https://drive.google.com/file/d/1g9cLcbQGZ8kRv7Cjorn_Ylc3mc8xrO2q/view) through the [linked distribution folder](https://drive.google.com/drive/folders/1lC-Gh0TF7ZxUy12YqoTg8nGEY7whfC6W). The archive contained a raw DOM image, not the official update package. Treat links and their current contents as untrusted dependencies; record the exact artifact hash you inspect. Availability or filename alone does not identify a safe image.

The [firmware chapter's download table](02-firmware.md#historical-downloads-used-in-the-first-52-case) records the exact official TS-X77 ZIP URLs and their inner `.img` filenames for both the final installation and the earlier VM test version.

- [Community x77 DOM discussion](https://blog.hx99.net/Tech/2015.html): provenance lead for the externally obtained loader, not an endorsement or an audited build recipe.
- [qnap-recovery PC1 utility](https://github.com/mkke/qnap-recovery/blob/master/pc1.c): extraction reference. Check licensing and platform integer-width assumptions. No copy is distributed here.

The public repo includes no vendor firmware or community loader binary. Reproducing the boot image requires separately obtaining and reviewing those inputs. Use the reference results for validation scope and the preview gallery for the fields to inspect.

## Release package references

Checked 2026-10-22:

- [Official stable 5.2 model feed](https://update.qnap.com/QTS_FW_5.2.0.xml): TS-X77 and TS-X73A both list 5.2.11.3652 / 20261014.
- [Official Beta model feed](https://update.qnap.com/QTS_FW_5.2.0_beta.xml): the examined 6.1 delivery source; its path name does not describe the target version.
- [QTS 6.1.0.3640 / 20261007 release notes](https://www.qnap.com/en/release-notes/qts/6.1.0.3640/20261007).
- [TS-X73A 6.1 official ZIP](https://download.qnap.com/Storage/TS-X73A/TS-X73A_20261007-6.1.0.3640.zip). Observed ZIP SHA-256: `0c04aa75a6c5b41e9e087eb7fe56d6f28c17a71943464b63d904f5a3a0f41571`. Extracted update `.img` SHA-256: `c73c47801387ebbce7a8d02531b3eca956ae5995828b0ba4dcec4c48731efc8f`.

These hashes identify the retrieved artifacts; they do not replace vendor verification. Private production logs, configuration exports and raw disk images are not source downloads. See [release choices](02a-release-tracks.md) for current versus tested versions.

**Continue with:** [build-input preparation](02-firmware.md#build-inputs), or return to the [task index](../README.md#read-in-this-order).
