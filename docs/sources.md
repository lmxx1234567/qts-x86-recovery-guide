# Sources and provenance

Reviewed while documenting the case on 2026-10-18. External pages and downloads can change. Official appliance documentation is context, not certification of generic x86 hardware.

## Primary documentation

- [QNAP NAS migration compatibility](https://www.qnap.com/en/nas-migration)
- [QNAP: migrated disks not shown as a pool](https://www.qnap.com/en-ca/how-to/faq/article/what-should-i-do-if-migrated-disks-are-not-shown-as-storage-pool-qnap-nas)
- [QNAP: moving data to a new NAS](https://www.qnap.com/en-us/how-to/faq/article/i-bought-a-new-qnap-nas-how-do-i-move-my-data-over-from-the-old-one)
- [QNAP download center](https://www.qnap.com/en/download)
- [QNAP security advisories](https://www.qnap.com/en/security-advisories)
- [SystemRescue boot options](https://www.system-rescue.org/manual/Booting_SystemRescue/)
- [GNU ddrescue manual](https://www.gnu.org/software/ddrescue/manual/ddrescue_manual.html)

## Community dependencies from the experiment

The community loader was obtained as [`x77-dom.img.rar` (file page)](https://drive.google.com/file/d/1g9cLcbQGZ8kRv7Cjorn_Ylc3mc8xrO2q/view) through the [linked distribution folder](https://drive.google.com/drive/folders/1lC-Gh0TF7ZxUy12YqoTg8nGEY7whfC6W). The archive contained a raw DOM image, not the official update package. Treat links and their current contents as untrusted dependencies; record the exact artifact hash you inspect. Availability or filename alone does not identify a safe image.

The [firmware chapter's download table](02-firmware.md#downloads-used-in-this-case) records the exact official TS-X77 ZIP URLs and their inner `.img` filenames for both the final installation and the earlier VM test version.


- [Community x77 DOM discussion](https://blog.hx99.net/Tech/2015.html): provenance lead for the externally obtained loader, not an endorsement or an audited build recipe.
- [qnap-recovery PC1 utility](https://github.com/mkke/qnap-recovery/blob/master/pc1.c): extraction reference. Check licensing and platform integer-width assumptions. No copy is distributed here.

The public repo includes no vendor firmware or community loader binary. Reproducing the boot image requires separately obtaining and reviewing those inputs. The case study and screenshot journal document the observed results and their limitations.
