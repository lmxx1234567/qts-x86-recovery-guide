# First-reader audit (2026-10-18)

The initial guide explained the architecture but required unstated engineering knowledge at several steps. This revision adds an [ordered command walkthrough](10-command-walkthrough.md) and a regular-file-only partition helper.

| Initial gap | Added material |
|---|---|
| Build OS and dependencies unspecified | Linux x86-64 build environment, packages, directory layout, machine boundaries |
| Firmware extraction only named a utility | Source review, narrowly checked 64-bit fix, compilation, extraction, gzip CRC and selected-file validation |
| Image partition offsets described but no copying method | GPT inspection/extract/replace helper with bounds, CRC, length and readback checks |
| Generic profile omitted platform fields | Complete VM example plus hardware profile reference and explicit adaptation gates |
| Diagnostic archive not connected to a menu | Two archives, full GRUB menu, explicit diagnostic rdinit, no automatic continuation |
| No runnable VM example | QEMU topology, firmware variables, isolated networking, disk-only boot, UI initialization/update steps |
| Virtual CD payload creation absent | xorriso packaging, rescue copy-to-RAM and media replacement sequence |
| Physical writer deferred to an unspecified tool | Explicit-target manual commands, identity/holder/mount gates, 512-byte-sector check, full written-range comparison |
| Default boot and access verification vague | EFI edit sequence, UEFI order guidance, restored-port and storage/file checks |

## Validation performed for this revision

- Offline tests cover archive paths/modes, unresolved templates, manifest checks, Markdown links and shell syntax.
- New GPT helper tests cover bounded replacement, readback, corrupt header CRC, wrong-size input, and rejection of symlinks/non-regular devices.
- The helper successfully inspected the actual retained base image without modifying it.
- The documented payload-selection/decompression logic matched all 21 retained firmware files byte for byte; the gzip stream had 2541 trailing bytes, separately identified rather than blindly ignoring extraction errors.
- No NAS disks, settings, pools or boot entries were changed. The standalone Linux/QEMU command transcription has not been freshly boot-tested by this documentation revision.

## Remaining boundary

A first-time reader with Linux administration skills can now follow a concrete reference path rather than inventing the missing build commands. This is still not a universal unattended installer: a compatible external loader, firmware driver support, actual hardware mapping and an explicit recovery decision are prerequisites. Unknown hardware must stop at diagnostics. A failed or incomplete disk set needs its own recovery analysis; the guide must not prescribe forced recovery as a generic next step.
