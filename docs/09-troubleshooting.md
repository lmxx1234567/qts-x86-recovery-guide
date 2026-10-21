# 9. Troubleshooting: symptoms, causes and verified fixes

| Symptom | What it meant in this case | Action / acceptance |
|---|---|---|
| Linux sees all disks; QTS scan lists them; installer sees no usable disks | HAL reverse mapping failed (`ret=-1`, port 0) behind PCI bridges | Add verified controller `DEV_PATH`; require per-disk return 0 and correct slot |
| Trying PCI_SWITCH_PORT 0–31 changes nothing | Wrong hypothesis for this topology | Inspect full controller path; do not keep random settings |
| Correct model/serial in scan output | Identity enumeration only | Validate reverse lookup and actual installer/storage behavior |
| `hal_app` fails in minimal diagnostic init | Matching HAL module/runtime may be missing | Load matching `hal_netlink`; preserve complete output |
| Rescue sees NVMe0; another OS calls it NVMe1 | Enumeration changed | Select by verified serial/model/capacity, never remembered device name |
| Raw boot partition reports busy | DM mappings already own the underlying partitions | Use the appropriate mapped partition, e.g. dom7; inspect holders before changing anything |
| FLASH mapping of SSD tail is absent from installer | It did not behave as a usable data disk | Use dedicated boot SSD plus separate data storage |
| Boot tests pass only with QEMU direct kernel arguments | EFI/GRUB was bypassed | Remove shortcuts and cold-boot from the virtual disk |
| UEFI_CSM does not boot the expected EFI path | Tested VM used a legacy path | Select actual UEFI and verify firmware runtime |
| FW004 during update | This attempt exhausted staging space under HDA_ROOT | Read log; use sufficient data-volume staging; do not treat failure as successful update |
| QTS default GRUB entry changed, but old OS still boots | Firmware BootOrder still selected old disk | Set and read back permanent UEFI order; verify no BootNext dependence |
| efivarfs is an unknown filesystem | QTS kernel lacked support | Use suitable UEFI maintenance environment or firmware UI |
| Management port 8080 no longer responds | Old QNAP configuration restored a different port | Check console/listeners and old settings; no reset necessary |
| Network seems absent during boot | Services were still starting; full boot took minutes | Observe progress; distinguish refused connection from no route |
| One link works, old LACP bond has partner churn | Old bond/MTU settings did not match new wiring | Validate switch and NIC configuration separately; do not infer healthy LACP from reachable web UI |
| DataVol2 warning | Capacity threshold exceeded, RAID still healthy | Read the warning text before attempting RAID repair |
| KVM says invalid session or partial access | BMC authentication/control session expired or restricted | Re-login/relaunch KVM; verify media attachment again; no blind reset |
| ISO filename not found | Mounted payload name differed from script expectation | List mounted media; check exact file/hash rather than rerun a writer blindly |
| Diagnostic output scrolls off screen | Evidence incomplete | Capture to RAM or a verified non-data destination; do not claim eight-bay success from partial output |
| CPU temperature absent despite k10temp | Model profile hid the available native source | Case fix: `MAX_TEMP_NUM=1`, `CPU_TEMP_UNIT=DTS:1`; refresh HAL and verify real values |
| System temperature / fans absent | This kernel did not expose motherboard/BMC sensors locally | BMC readings exist separately; integration deferred, preserve independent fan management |
| Total memory 0 B, invalid slot/channel label | One-slot placeholder profile lacked a working DIMM source | Verify SMBIOS; configure DMI access, real channel/slot counts and BIOS-specific offsets |
| Disks 7/8 listed but not highlighted in the TS-877 front image | Six-large-plus-two-small artwork mismatched the slot presentation | Locally replace front artwork with an eight-large-bay resource; retain HAL mapping |
| SSD cache wizard lists no candidates | Cacheable port bitmap was zero | Case mask `0x1FE` covers verified slots 1–8; eligibility is not permission to erase disks |
| ARM64 apps missing after x86 recovery | Old directories survived without current registration; executable architecture differs | Inventory registration and ELF headers, preserve data and use compatible packages |

The HAL error above is **historical and resolved** in the final case. Current acceptance showed eight successful per-disk HAL lookups and a recovered Qtier pool. Some historical screenshots predate that fix; their captions state their limited meaning.

The later fixes above are documented in [hardware presentation and apps](07a-hardware-and-apps.md), including live verification, remaining limits and pending reboot verification.

## After a 5.2 → 6.1 change

Consult the [6.1 compatibility findings](11-qts61-upgrade.md#5-compatibility-findings-and-fixes) for hard-coded kernel paths, Python runtime selection, the 21-second HAL startup, stale sensor cache and the native CPU widget. A missing old SVG is cosmetic; a failed reverse disk lookup is a storage gate. Do not resolve either by repeatedly initializing the old disks.
