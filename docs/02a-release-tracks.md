# 2a. Choose QTS 5.2 stable or QTS 6.1 Beta

[← Previous: Firmware and loader](02-firmware.md) · [Workflow index](../README.md#read-in-this-order) · [Next: VM validation →](03-vm-validation.md)

Choose the release **before** extracting firmware or building a model profile. Both routes then follow the same [command walkthrough](10-command-walkthrough.md): obtain dependencies → extract payload → adapt the model → build → test VM → install boot SSD → verify bays → recover storage → accept an independent boot. You do not need to read two copies of those steps.

## Release choice and evidence

Checked on **2026-10-22** against the [official 5.2 feed](https://update.qnap.com/QTS_FW_5.2.0.xml) and [Beta feed](https://update.qnap.com/QTS_FW_5.2.0_beta.xml). A feed entry is download/discovery evidence, not a successful test on generic hardware.

| | Track A: current 5.2 stable | Track B: 6.1 Public Beta |
|---|---|---|
| Download selection at this check | **5.2.11.3652**, build **20261014** | **6.1.0.3640**, build **20261007** |
| Reference model / package family | TS-877 / **TS-X77** | TS-873A / **TS-X73A** |
| Official package | [5.2 TS-X77 ZIP](https://download.qnap.com/Storage/TS-X77/TS-X77_20261014-5.2.11.3652.zip) | [6.1 TS-X73A ZIP](https://download.qnap.com/Storage/TS-X73A/TS-X73A_20261007-6.1.0.3640.zip) |
| Runtime tested in this project | 5.2.10.3577 / 20260731; **5.2.11 has not been boot-tested here** | 6.1.0.3640 / 20261007, in VM and on the physical case host |
| Measured kernel | 5.10.60-qnap on tested 5.2.10; measure the selected newer build | 6.6.129-qnap on tested Beta |
| Why choose it | Stay on the stable branch; validate its newest maintenance release before recovering originals | Evaluate the newer kernel/features and accept Beta/application compatibility limits |
| Existing original Qtier pool | Recovered on the 5.2.10 case | Same complete five-disk pool recovered after the physical 6.1 boot upgrade |
| Scheduled unattended update | Not verified | Not verified; native **manual** 5.2→6.1 update passed in VM |

The Beta's [official release notes](https://www.qnap.com/en/release-notes/qts/6.1.0.3640/20261007) list a limited supported application set. Check every required app before selecting it. TS-873A being an official supported appliance does not make a custom PC supported. A similar CPU generation alone does not establish driver, HAL or storage compatibility.

The original X77 loader archive is still the **boot-layout base** for both reference routes. It is not a TS-X73A firmware package and does not determine which OS version gets installed. Obtain it through [dependency provenance](02-firmware.md#dependency-boundary); do not write the official update `.img` directly to an SSD.

## Find the newest release when following this guide later

1. Open the [QNAP Download Center](https://www.qnap.com/en/download), choose TS-877 for Track A or TS-873A for Track B, and choose **QTS** firmware. Do not select QuTS hero or QuTScloud.
2. Read that exact release's model list, upgrade prerequisites, known issues and app compatibility. Confirm its channel is stable or Beta as intended.
3. Record family, complete version, build date, HTTPS download URL, release-note URL, retrieval date, file size and SHA-256 in `private/`. Check publisher checksums/signatures when available.
4. Set the walkthrough's `FW_FAMILY`, `FW_BUILD`, `FW_VERSION` and `MODEL_TRACK` to that selection. Do not change a filename alone or mix extracted payload from older builds.
5. Repeat VM upgrade/initialization, disk-only cold boot, HAL reverse lookup and file-hash checks. A newer version is **unvalidated** until these pass; no script in this repository guarantees future firmware compatibility.

A dated feed can lag, have model-specific rollout rules, or use a misleading path name: the observed 6.1 Beta was advertised in `QTS_FW_5.2.0_beta.xml`. Use the model-specific Download Center rather than guessing feed URLs. Do not rewrite QTS update URLs to force a release.

## What differs in the model

| `[System Enclosure]` key | X77 reference | X73A reference |
|---|---|---|
| `MODEL` | `TS-877` | `TS-873A` |
| `DISPLAY_FIXED_MODEL_NAME` | absent | `TS-873A` |
| `CAP` | `0x1414db1c` | `0x4149b1c` |
| `CAP_EXT` | absent | `0x00040000` |

These values describe the examined reference models. Keep the destination's reviewed boot mapping, disk/network PCI addresses, bay count, geometry and boot serial. **Do not replace the whole model with a vendor appliance's file.** Use `tools/select_model.py` as shown in walkthrough section 4; it refuses unrecognized source identities. A successful edit is only a candidate, not firmware acceptance.

For a new installation, select one track and complete the shared walkthrough. For an already recovered custom X77 installation moving to X73A/6.1, use the [existing-installation procedure](11-qts61-upgrade.md#3-upgrade-an-existing-custom-qts-installation); changing only a live model name and submitting another family's update was not the production procedure used here.

## Version-specific follow-up

- **5.2:** older CPU widgets may need the narrowly checked optional display fix. The default path needs no artwork, fan shim, memory patch or cache-candidate modification to recover data.
- **6.1:** select modules using `uname -r`; the old hard-coded 5.10 path no longer works. The new CPU widget already understands native CPU readings; preserve it. Python locations and HAL startup timing changed. See [6.1 findings](11-qts61-upgrade.md#5-compatibility-findings-and-fixes).
- **Both:** optional sensor adaptation is board-specific. Never copy the case host's thermal shutdown thresholds, direct KCS addresses or synthetic VM readings into a different machine. Default boot and full storage acceptance are shared in [chapter 7](07-acceptance.md).

[← Previous: Firmware and loader](02-firmware.md) · [Workflow index](../README.md#read-in-this-order) · [Next: VM validation →](03-vm-validation.md)
