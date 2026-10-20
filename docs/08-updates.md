# 8. Updates and rollback

<!-- stage-navigation -->
[← Previous: Hardware display and apps](07a-hardware-and-apps.md) · [Workflow index](../README.md#read-in-this-order) · [Back to project overview →](../README.md)
<!-- /stage-navigation -->

**Unattended automatic updating is not established by this project.** The observed official manual upgrade path succeeded in a disposable VM. That result does not prove that future firmware preserves the loader, overlay, drivers, HAL interfaces or data format.

Keep update notifications distinct from automatic installation. For recovery use, defer upgrades until data has been exported or backed up. For continued operation, evaluate security releases promptly through a staged workflow rather than leaving the machine indefinitely unpatched.

**Latest case result (2026-10-20):** CPU90 and real motherboard/fan sampling passed live acceptance and were saved to the boot overlay. Cold boot and firmware upgrade remain untested. Detailed acceptance and rollback records are at the end of this page.

## Per-release gate

1. Download from the official source; record identity and inspect release notes and package contents.
2. Compare kernel/modules, init scripts, HAL libraries, EFI/GRUB and partition/updater logic against the tested version.
3. Back up the full boot SSD and configuration; make a consistent test copy/snapshot of the data disks. A boot backup alone cannot undo storage metadata changes.
4. Test the official update on an isolated copy. Keep official signature/version checks enabled and stage the package where space is sufficient.
5. Verify all bays, boot exclusion from data choices, both cold boots, pool/tier state and file hashes. Repeat the [hardware follow-up checks](07a-hardware-and-apps.md): native CPU temperature source, DIMM topology, cache-port mask and late-loaded web artwork. Re-derive DMI handle offsets after BIOS changes.
6. With a recovery route ready, schedule the production update and repeat acceptance. Keep the console available.

## Perform the manual update on the test copy

Start with a stopped, consistent checkpoint of the test VM's boot disk, data disks and UEFI variables. Record the current version, healthy storage state and test-file hash. An already degraded or rebuilding pool is not an appropriate update experiment.

1. Download the exact target model/build ZIP to the computer running the browser. Extract the official update `.img` from the ZIP. For this UI operation use that update package, **not** the PC1-extracted kernel files and not `qts-boot.img`.
2. In QTS, open **Control Panel → System → Firmware Update → Manual Installation**. Choose Browse, select the extracted update package, verify the displayed version, then start Update System. This is the [official manual update workflow](https://docs.qnap.com/operating-system/qts/5.2.x/en-us/updating-the-firmware-manually-F347B63B.html); follow any version-specific prerequisites instead of bypassing them.
3. Keep the console available and allow installation and its requested restart to complete. If validation fails, retain the error/log and stop. Do not disable signature checks, delete system files to make room or force a restart during firmware writing. Check space on the actual staging volume; the earlier FW004 space failure does not mean every FW004 has that cause.
4. Log in again and read the actual runtime version/build. A successful upload or a changed download filename is not evidence that the update booted. Run chapter 3's two cold starts and file/hash checks; compare geometry, EFI and support-file manifests against the checkpoint using readback on **stopped disk-image copies**.
5. If a gate fails, keep the failed VM state for analysis and restore all checkpoint components together. Do not use a boot-only rollback against newer data metadata. Promote the procedure to production only after the intended update path has passed and independent data backups are available.

For recovery work, keep native firmware installation notification-only in the firmware-update settings and read the saved selection back. Checking for updates and delivering email/push notifications are separate settings. The restoration package discussed below restores some local adaptations; it does not make an untested firmware update safe or automatically reversible.

## Adaptation compatibility is separate from firmware installation

The [one-shot restoration package](07a-hardware-and-apps.md#unified-one-shot-restoration-package) and its component checks are documented with the hardware/app procedures. It is not an updater or a full rollback system. Keep three boundaries explicit:

- EFI/GRUB, early-init device mapping and all bay identities must work before optional repairs can run. If the overlay or startup hook is lost, its repair scripts and notifications cannot protect the boot path.
- A surviving overlay can reapply a file without proving it remains compatible. Recheck actual HAL behavior, DIMM topology, sensor readings and application access after the update. A working CPU widget is not storage acceptance.
- Package rollback covers its own changes, not QTS firmware or pool metadata. Administrative privilege customizations need separate deliberate management; do not recreate passwordless sudo as part of a display repair.

## Case policy: notification-only

The initial 2026-10-18 audit found `v3_action_mode = 2` (`UPDATE_LATEST`) and native update schedules, contrary to an older local research policy. After the operator explicitly requested a change, the QTS firmware-update page was used to select **“Notify me, but do not automatically update firmware.”** Configuration readback confirmed `v3_action_mode = 1` and legacy `action_mode = 2`. No firmware installer/reboot process was running when checked. Arrays remained complete, with the existing resync continuing.

The configured notification/check time remains daily at 04:00. The UI reports that no firmware-update delivery rule is configured; no recipients or external channels were added. The notification-only policy prevents automatic firmware installation, but does not itself configure email or push delivery. See the [official policy description](https://docs.qnap.com/operating-system/qts/5.2.x/en-us/updating-the-firmware-automatically-4229F6D2.html). Application-update settings were not changed.

![Firmware settings: notify only, daily check at 04:00, and a warning that delivery rules are not configured](../assets/screenshots/firmware-notify-only.png)

The actual settings-page capture from 2026-10-18 shows **“通知我，但不自动更新”** (notify me, but do not automatically update). The explanatory text says updates will not install automatically. The warning below it concerns missing notification-delivery rules; it is not permission to install firmware. It records the saved policy, not an upgrade or reboot test.

## Proposed support for routine updates

**Restoration package implemented and installed; automatic firmware installation not deployed.** The goal is ordinary stable TS-X77 / QTS 5.2 maintenance releases without an exact-build allowlist or a new manual review for every changed binary. Major QTS migrations, cross-model firmware changes and unusual hardware/boot-layout changes are outside this target. “Most routine updates” is an engineering goal, not a measured success rate. Native firmware installation remains notification-only until the remaining update integration tests and installer workflow are completed.

### Keep one persistent adaptation package

Keep a versioned manifest and original project scripts in the existing support-partition overlay, separate from the two firmware slots. Describe each customization as a small independent module: prerequisites, detection, narrow apply operation, verification and rollback. Preserve the current early boot identity/geometry and disk-isolation guards. After QTS starts, run one bounded reconciliation pass and exit; do not introduce a resident service.

| Component | Routine-update behavior to implement |
|---|---|
| Boot and storage mapping | Validate the actual loader hook, required boot tools/modules and known host mapping. Unexpected EFI replacement or partition-writing behavior stops installation; it is not a cosmetic fallback. |
| Sensors | Keep board/KCS identity, exclusive-access and real-reading checks. Use interface/configuration probes and bounded helper-process tests for the supported release family instead of requiring all five binaries to retain identical hashes. Hashes remain evidence/fast paths, not the only compatibility criterion. A changed HAL still needs successful probes; simply deleting hash checks is not sufficient. |
| CPU dashboard row | Recognize supported widget structures; leave the new vendor widget untouched if the pattern changes. Sensor collection can remain working even if the optional dashboard row needs a later patch. |
| DIMM reporting | Re-read SMBIOS and derive slot offsets rather than assume old handles. Update only the memory section/cache after confirming the topology. Failure produces a reporting warning, not a guessed configuration. |
| Cache candidate mask | Confirm the accepted enclosure port IDs before restoring the mask. Never select disks or create a cache automatically. |
| Artwork | Check SVG slot IDs and target resource structure. Fall back to vendor artwork on mismatch; do not block firmware installation over a chassis picture. |
| MyQNAP index cache | Restore only the known repository entry and deduplicated scheduled task; validate runtime dependencies and XML. Keep the last valid index on fetch failure and report staleness. |
| Administrative preferences | Keep privilege policy separate. Do not infer permission to recreate passwordless sudo from a sensor/package repair. |

The implemented package isolates optional module failures and sends one summarized QTS notification identifying restored, skipped and failed components. On-disk backups and runtime rollback cover the project's own patches; they are not automatic firmware/storage downgrades.

### A small scheduled update command, not a second updater daemon

For future unattended installation, prefer one project-owned scheduled command while the native policy stays notification-only. Its steps are: discover a stable release in the supported family; download the original package; check model, package integrity, required drivers and boot/partition update behavior; confirm storage is healthy and not rebuilding, staging space and configured backups are available; then hand installation and signature verification to the official QTS update path. Avoid constructing another raw firmware writer.

Routine releases that pass these checks need not appear on an exact-version allowlist. Changed boot-critical behavior stops with a notice; optional mod incompatibility normally means skipping that mod. A scheduled script is not a background daemon. The scheduled installer, its maintenance window and any restart permission are **not enabled by the present notification-only request**.

After the normal upgrade restart, the one-shot package checks the boot/mapping outcome, arrays, volumes and service availability, then restores compatible optional modules. Before implementing an installer wrapper, verify the official entry point's completion/reboot semantics: do not assume there is a usable “after write, before reboot” hook. Preserve the overlay through the inspected update path rather than depend on an undocumented interception.

### Delivery sequence

1. **Completed:** consolidated the fixes into independent one-shot modules, passed 28 repository tests and live preflight/application/idempotence checks, and installed the hash-verified overlay with a rollback backup. No NAS reboot or firmware installation was performed. See [implementation and commands](07a-hardware-and-apps.md#unified-one-shot-restoration-package).
2. **Pending:** first validate the next authorized boot, then exercise one representative maintenance-release update on disposable storage, including hook survival, restored mods and skipped-module notifications. Reuse that integration coverage for structurally compatible releases rather than require a full clone test for every build.
3. **Not deployed:** add the scheduled installer only after the supported official update entry point and first update cycle have been verified, with a separately selected maintenance/reboot policy.

The existing local static auditor is a starting point, not this completed controller: it pins an installer-script hash, kernel details and an older hook pattern. Adapt its checks to the actual current boot path; do not present its current static pass as runtime or automatic-install readiness.

## Why two firmware slots are not rollback

The tested update rewrote p2 and p3 with the new firmware. They were not an old/new A/B rollback pair. The separate support partition's files survived this one update, but that is not a contractual guarantee from QNAP. EFI acquired additional files even when the existing loader and menu stayed unchanged.

A safe rollback may require both boot and storage state from a consistent point, and an older firmware may not understand newer metadata. Do not downgrade against a live migrated pool merely because an older boot image exists. Recover important files first.

Future automation should implement the gate above, including explicit compatibility evidence and a failure stop. A timer that downloads the newest package and reboots is not a validated recovery/update system.

---

<!-- stage-navigation -->
[← Previous: Hardware display and apps](07a-hardware-and-apps.md) · [Workflow index](../README.md#read-in-this-order) · [Back to project overview →](../README.md)
<!-- /stage-navigation -->

### 2026-10-20 cold-start sensor investigation (deployment pending)

On the inspected QTS 5.2.10 build, the running `hal_daemon` maps to
`/sbin/hal_util` and loads `/lib/libuLinux_hal.so`. Its 11:29:23 log explicitly
reports shutdown thresholds CPU/system/disk/power of 85/70/60/55 C. These are
observed loaded settings, not proposed settings. Static inspection found the
DTS reader's k10temp `temp1_input` path (millidegrees converted to integer C);
on this host that input is labelled Tctl. CPU overheat handling can call
`Shutdown_System()`, so orderly shutdown alone does not exclude thermal protection.
No threshold, protection, fan-control, or voltage change is part of this patch.

The deployed `reconcile.py` and `start` matched commit
`f0f77c0434b84829cab1783e6933d4dfbb9f3ef5`. This boot's sensor transaction rolled
back after a daemon-manager timeout. Its output also included three
`sh: python: command not found` errors. The startup PATH omitted `/usr/local/bin`,
where the verified Python interpreter resides. The patch restores that directory
(and `/usr/local/sbin`) to the explicitly controlled startup PATH. The exact
producer of those three messages is still unproven; this is not a claim that PATH
alone caused the timeout. Native initialization scripts contain bare Python
calls, while the compatibility scripts use absolute interpreter paths.

Lifecycle calls now log begin/return/confirmation/failure with time, elapsed time,
full action, registration, process IDs and captured output. Timeout remains a
failure even when state appears to match. On timeout only the manager client is
terminated, not its process group: a newly spawned hardware monitor must not be
killed as a descendant. Generic diagnostic probes retain process-group cleanup.
Stop-failure recovery does not issue a duplicate start when the monitor is already
registered and running. Existing transaction rollback restores mapping files
before attempting runtime recovery; an unsuccessful transaction stays blocked.

Unit and simulated lifecycle tests cover these paths. Applying sensor mappings
still requires a stop/start of the hardware monitor, temporarily interrupting QTS
monitoring and potentially its userspace thermal response. Deployment and live
verification are pending explicit approval of that interruption. Do not remove
the boot's `sensors.blocked` marker or activate this patch automatically. A future
approved deployment must back up live files, verify their expected hashes, apply
only the sensor module, confirm fresh CPU/system/fan cache and BMC scaling, and
verify the loaded thresholds remain unchanged. Persistent overlay installation
and cold-start validation are separate pending steps.

This morning's rollback is not evidence of the state during the three previous
shutdowns. Their cause remains unresolved; do not increase thresholds as a
workaround for sensor compatibility.

Approved live attempt at 11:53 on October 20 did not pass. Preflight discovered
that the old HAL process had inherited `/tmp/qts-mods/lock` on fd 3; the updater
therefore reported another check despite no reconcile process running. Subprocess
launches now use `close_fds=True` (required for the deployed Python 2 environment).
After a single approved stop to release that inherited lock, the sensor-only
transaction started HAL with the new mappings. The start client timed out at
20 seconds, while a HAL process existed but registration still said `stop`.
The transaction restored the original mapping and restarted HAL successfully.
No repeated activation was attempted. The new PATH eliminated the previously
observed bare-Python error in this attempt but did not resolve the start timeout.

Recovery PID 12117 loaded the unchanged 85/70/60/55 C thresholds at 11:54:10.
The complete hal_util.conf SHA256 remained
`103550d6e8f1ffd9c15b2df55b1ef803c152688f8b148382e19916954e7e149c`.
At 11:55 the monitor was active, but the CPU cache still reported 67 C while
native Tctl was 60.875 C; continuous cache freshness is not yet established.
The live scripts include the new diagnostics and fd-isolation fix; the sensor
failure marker remains. No persistent boot overlay was changed, so live and boot
versions must be reconciled only after a successful repair. Backup:
`/mnt/HDA_ROOT/.qts-sensor-fix-20261020/before.tar`.


### 2026-10-20 offline synchronous-start investigation

The subsequent work is local only; it has not been deployed. Static inspection
of the captured binaries narrows the startup timeout beyond the IPMI read adapter:

- `daemon_mgr` takes its four-argument `start` branch at 0x404b64, executes the
  supplied command synchronously through `system()` at 0x404de3 (ordinary
  non-LD_PRELOAD branch), and only later reaches registration handling at
  0x404f58. Its return value of 1 is not itself failure. A monitor PID can exist
  before this sequence finishes, as the failed activation actually showed.
- The captured HAL `-f` option selects mode 2 at 0x41be57; it does not mean
  foreground mode. HAL calls its daemonization helper at 0x41beb0. The helper
  forks at 0x41a7ab and exits the parent at 0x41a7b9; the child redirects standard
  descriptors and calls setsid. A PPID=1 shortcut exists. This ordering means
  a later child sensor initialization stall alone does not explain the manager
  continuing to wait for the original parent. Exit handlers, pre-fork work,
  and the manager's later steps remain possible; none is proven the cause.
- Before that fork, the main path synchronously runs
  `/sbin/da_util --enable_by_cfg value=1` and `/sbin/mpath_util check_module`,
  initializes HAL IPC (including blocking fcntl locking), writes monitor mode
  through the INI library, and prepares logging. The saved evidence does not
  identify which stage the failed process reached. These helpers have NOT been
  executed as diagnostics, because their side effects are not established.
- The adapter's supported temperature/fan path is
  HM read -> ipmi_sys_get_temperature/ipmi_sys_get_fan_speed ->
  comm_sys_send_ipmi -> hal_qnap_secure_popen -> `/sbin/ipmitool` -> kcs_read.
  Native secure_popen reads until EOF and qnap_pclose waits for its child.
  The adapter itself starts no subprocess, prints one hex line on success or
  an error to stderr and exits nonzero. The KCS transport uses a nonblocking
  lock and a three-second polling deadline; it performs no retries or reset.
  Kernel I/O calls themselves are not forcibly timed out. This is not a proof
  that every possible HAL IPMI command is supported: control/other commands
  are intentionally rejected, and the allowlist has not been expanded.
- The reconciler captures stdout/stderr in a temporary regular file, not a
  pipe; it waits for the manager client, not for EOF from a daemon descendant.
  The previously observed inherited updater lock was independently fixed with
  close_fds=True. New real-process tests verify both this descriptor boundary
  and the daemon-return / synchronous-wait cases, beyond the earlier mocked
  lifecycle tests. Adapter tests verify stream closure, native argument format,
  unavailable readings, and refusal of control commands without hardware access.

A local diagnostic patch attaches best-effort process metadata to lifecycle
CommandTimeout before killing the client. It captures the client, descendants,
and detached HAL (PID/PPID/name/state/wchan/syscall number), omits argv,
environment, memory and syscall arguments, bounds the scan, and does not allow
capture failure to prevent rollback. This preserves the evidence currently lost
when the failed HAL is stopped and its log replaced. It does not increase the
20-second timeout, accept a PID as success, change mappings or protection values,
or claim to fix the unproven native startup cause. Live activation remains paused.

Further read-only copies of da_util, mpath_util, hal_app and mpath_lib.so refined
that pre-fork branch (none was executed): current Disk Data Collection Enabled
is 1. da_util's enable_by_cfg handler (0x404b3f) calls two hal_app commands with
enable=0 then enable=1 (0x404b00), then its own enable handler (0x404baf).
The latter calls logging helper 0x4065f1, which synchronously runs bare
`python /usr/local/bin/da_util.pyc da_log_msg ...` (0x4066e0).
hal_app dispatches the command at 0x43aea4 to se_sys_set_disk_data_collection
(loaded HAL library 0x149830). That function edits the disk-data-collection
configuration/crontab and calls da_util --enable. Thus the disable/enable pair
plus outer enable can account for three bare-Python logging calls on the normal
branch. This is a concrete candidate source for the previous three errors;
there is still no captured failed-process trace proving attribution or timeout
causality. The adapter's own interpreter is an absolute path.

mpath_lib.so check_module (0x2f12) selects the modules.list symlink and, on one
branch, executes daemon_mgr multipathd stop. Neither helper is a harmless read
probe; do not run it independently to diagnose this issue. The known command
handlers above do not directly call the adapter. Dynamic constructors and the
remaining native registration/config-lock paths have not been fully excluded.

Validation after the offline additions: 59 tests passed, including five real
process/snapshot cases and three adapter protocol cases; git diff --check passed.
No NAS file, monitoring state, power operation, or protection setting was changed
in this offline investigation. Copies of binaries and selected read-only config
values were the only NAS accesses.

### 2026-10-20 CPU threshold attempt: rolled back, persistence withheld

The separately authorized CPU-only 85 -> 90 C transaction failed during the
first `daemon_mgr start` call's 20-second deadline. It restored the exact original
85/70/60/55 C configuration and successfully started a replacement HAL, PID
23917. Its fresh 13:03:10 NAS log explicitly reports those original thresholds.
The failed attempt did not activate the IPMI adapter or change sensor mappings.
Therefore the startup timeout also occurs with the CPU-only configuration;
IPMI activation is not a necessary condition for this failure. This does not
identify the native wait site or prove that the two failures have the same cause.

Read-only observations from NAS-clock 13:04:12 through 13:05:12 confirmed that
PID 23917 remained present, all four thresholds stayed unchanged, and the CPU
cache advanced from 59 to 55 C with its modification time increasing by about
60 seconds. Instantaneous Tctl ranged from 55.125 to 76.750 C. These observations
confirm resumed CPU sampling, not full hardware monitoring or long-term stability.
Motherboard temperature and fan readings remain absent.

The live thermal.py file is dormant, with thermal.blocked and a failed status
record preventing another same-boot attempt. The original configuration backup
is `/mnt/HDA_ROOT/.qts-thermal-backups/20261020-130248-NB2azw/`.
No thermal startup hook or persistent overlay was installed. The locally built
thermal90.cpio.gz is an uninstalled candidate, not a successful deployment.
Neither reboot nor firmware-update survival has been tested or established.

The local suite now passes 65 tests, including six CPU-policy/overlay tests.
The earlier process-snapshot diagnostic patch remains local and undeployed.
Its activation still requires resolution of the pending authorization; the
reminder about missing motherboard/fan data does not authorize another live
restart. Do not install persistence for this failed startup strategy or extend
the timeout without evidence. Capture the native wait chain on an authorized
diagnostic attempt before choosing a repair.

### 2026-10-20 authorized single diagnostic activation

After explicit approval for one diagnostic activation and its brief monitoring
interruption, the 65-test suite passed again. The tested timeout-process snapshot
patch was deployed to the live reconciler, preserving its file mode. Backup:
`/mnt/HDA_ROOT/.qts-diagnostic-20261020/` (manifest and original files).
No boot overlay changed.

The single attempt stopped HAL at NAS-clock 13:23:18 and reached its unchanged
20-second start deadline at 13:23:38. The snapshot taken before killing the
manager client recorded:

| PID | Parent | Name | State | syscall | wchan |
| --- | --- | --- | --- | --- | --- |
| 26096 | 26069 | daemon_mgr | S | 61 (x86-64 wait4) | 0 |
| 26099 | 26096 | hal_daemon | S | 35 (x86-64 nanosleep) | 0 |

Registration was still `stop`. No IPMI/helper descendant was present in this
snapshot. Thus the native HAL process itself was sleeping while the manager
waited for it, rather than the snapshot showing a manager waiting on a detached
fully initialized monitor. wchan=0 gives no usable kernel symbol. No arguments,
environment or process memory were captured. A single snapshot does not provide
a userspace call stack or exclude earlier helper activity.

Static analysis identifies a particularly relevant pre-daemonization candidate:
`thread_get_msqid` at 0x413307 calls msgget for key 0x48414c55 with CREATE|EXCL.
An EEXIST result returns -1. Main at 0x41bdcf then calls `clear_ipc` (0x413b85),
which removes that queue and reads HAL_Monitor_Get_Mode in a sleep loop. If mode
is not 2, its post-increment compare executes 21 one-second sleeps before logging
"wait util stop fail". Main then retries queue creation regardless of that
clear_ipc return value. This all precedes option processing and daemonization.
HAL_Monitor_Get_Mode reads [Global] Service Mode from /etc/hal.conf; a subsequent
read-only check found mode 0 and the current monitor's queue with that exact key.
This is consistent with a stale queue causing a normal native cleanup wait to
outlast our 20-second client deadline. It also fits the immediate rollback start
after the first process has removed the old queue. It remains a hypothesis:
the failed process's call stack, EEXIST result, and mode during its wait were
not captured. Do not label the precise branch proven or silently lengthen the
deadline, change Service Mode, remove IPC objects, or retry activation.

Automatic rollback restored model.conf, hal.conf, hal_util.conf and absence of
/sbin/ipmitool; all original hashes/existence matched the backup manifest.
The rollback start completed in 0.116 seconds with HAL PID 27002 and a fresh
13:23:39 log loading 85/70/60/55 C. Seven read-only samples over the next minute
confirmed PID/registration health and CPU cache advancement from 67 to 53 C,
with mtime advancing 60.038 seconds. Tctl ranged 53.625–72.750 C.
The sensor failure marker remains; the deployed diagnostic code is inert until
another explicit reconciliation. The one-attempt guard is consumed. CPU90
and motherboard/fan restoration remain incomplete, with persistence withheld.

### Conditional startup grace proposal (offline only)

Read-only follow-up at NAS-clock 13:27:09 again found Service Mode 0, the
0x48414c55 queue (id 14) used by PID 27002, and the original loaded thresholds.
There are no clear_ipc messages in the retained HAL logs. Static inspection also
shows normal HAL teardown writes mode 2 at 0x41c504, while the -f startup option
writes mode 0 only after clear_ipc. This supports the interpretation of mode 2
as the native stopped condition; it does not establish why that condition was
not reached during our earlier stop.

The proposed local native_start_window.py is a policy prototype, not integrated
with run_result, thermal.py, or startup scripts, and has NOT been deployed:

- Keep the normal command deadline at 20 seconds. Stop and unrelated commands
  never receive grace.
- Permit a single extension to an absolute 25-second startup deadline only for
  the exact daemon_mgr/hal_daemon start invocation and the three captured binary
  hashes, on x86-64.
- Immediately after a confirmed stop, capture the baseline: no HAL PID,
  registration stop, mode 0, and an existing queue. During startup require two
  complete snapshots in the last second before deadline, at least 0.2 seconds
  apart: the queue is now absent, mode remains 0, registration remains stop,
  and exactly the manager in wait4 plus its direct HAL child in nanosleep are
  present. Missing/contradictory evidence, a helper or a competing HAL denies
  the extension. This is an observed phase signature, not proof of a particular
  userspace instruction. The old failed-attempt snapshot alone is insufficient
  because it lacks the contemporaneous queue transition.
- Do not renew the extra time. Preserve both phase evidence and the final
  pre-kill snapshot. Wait uses monotonic elapsed time, not NAS wall-clock time.
  Kill only the manager client on expiry; restore configuration before a bounded
  monitor recovery, as in the tested transaction.
- Return code 0/1 is not readiness. Require fresh single HAL PID, registration
  start, a newly written log confirming the expected four thresholds, and a
  fresh cache before reporting success. Sensor and CPU-threshold acceptance
  remain independent.

Proposed lifecycle budgets, including their state-confirmation polling, are
20s stop + at most 25s start + 15s fresh-threshold-log readiness. One rollback
may consume the same 60s budget, yielding at most 120s of planned lifecycle
waiting from the first stop through recovery. Normal successful startup is
expected near the native 21s wait, but has not been measured. CPU cache freshness
is then observed for up to 65s with a running, threshold-confirmed HAL. Sensor
probes must run after that readiness and retain their existing separate bounds.
These are proposed control-flow limits, not a guarantee of recovery by 120s:
an OS/device failure or failed recovery must be reported and stop further work.
The phase grace itself adds at most 5s per start, or 10s across attempt plus
rollback. No live timeout has been increased in this work.

Nine additional offline tests exercise the captured 21-sleep loop, its fit in
the 25s window, no-grace cases, stale/insufficient/contradictory snapshots,
unexpected binaries/architecture/mode/queue/helper states, fixed nonrenewable
expiry, rollback ordering and readiness requirements. All 74 tests pass; diff
checking passes. Integration still needs to implement the shared inclusive
lifecycle/readiness budgets and preserve all diagnostics before any live use.

### Authorized bounded-start integration and one live attempt

The candidate was integrated behind an explicit per-process opt-in,
NATIVE_IPC_GRACE; normal startup and thermal.py do not enable it. Command waiting
uses monotonic time (/proc/uptime on Python 2). Stop/start confirmation shares
the command deadline. The invoking one-shot wrapper reserves 60 seconds for the
attempt and an absolute 120-second deadline for recovery; sensor undo switches
to the reserved recovery deadline. Native readiness additionally requires the
new HAL PID's startup log, all four expected thresholds, and a newer CPU cache.
Seven integration tests bring the passing suite to 81 tests, including the
actual polling supervisor under a virtual monotonic clock, bounded hangs,
ordinary stop behavior, transaction caps and stale-cache rejection.

One explicitly authorized activation ran at NAS-clock 13:35:19, with backups
in `/mnt/HDA_ROOT/.qts-bounded-start-20261020/`. Both starts genuinely received
the conditional grace based on live evidence, not an unconditional larger
timeout:

| Stage | Original queue | Phase evidence | Command returned | New HAL |
| --- | --- | --- | --- | --- |
| Initial start | 14 | queue absent, mode 0, manager wait4 / direct HAL nanosleep at 19.1/19.4/19.8s | 21.104s | 28401 |
| Recovery start | 15 | same qualifying transition and three snapshots | 21.142s | 30314 |

Both confirmed registration and fresh 85/70/60/55 C loaded-threshold logs/cache.
This is live confirmation that allowing the specific native cleanup wait can
complete startup after the former 20s deadline. It strongly corroborates the
statically identified 21-sleep clear_ipc path; no userspace instruction-pointer
trace was collected, so exact branch execution is not directly traced.

The initial sensor transaction then failed its cache check, not startup:
`Monitor cache readings absent`. All preceding native temperature/fan API
checks and comparisons with raw BMC readings passed (individual numeric probe
results were not logged). The original cache verifier requires SYST_1.
Static SE_Get_System_Status at 0x6980f/0x69820 instead reads TEMP_1; the binary
contains CPUT_%d, FANR_%d and TEMP_%d, with no SYST_1 contract found.
This is a verifier defect, but TEMP_1 also did not appear in the captured cache,
so correcting its name alone is not proof that motherboard cache reporting
works. The first ready snapshot contained only FANR_1; FANR_2 appeared later.
Cache population timing and the motherboard-cache write path need investigation.

Automatic rollback completed within 45.29 seconds for the whole transaction.
Model, HAL config, threshold file and /sbin/ipmitool absence exactly match
the original backup hashes/existence. Current model is MAX_TEMP_NUM=1,
MAX_FAN_NUM=0, CPU_TEMP_UNIT=DTS:1; the native shim is absent. Some old FANR/FANS
keys remain in the shared cache after rollback and must NOT be treated as
enabled or fresh fan monitoring. No cache was cleared. Read-only follow-up
confirmed CPU cache updates and a healthy registered PID 30314.

This attempt's token is consumed and no second activation was performed.
The live opt-in code remains installed but is not enabled by normal startup.
No boot overlay was changed, CPU90 remains unapplied, and the thermal failure
marker remains untouched. Next steps are separate: repair/test the sensor cache
contract before another sensor transaction; route the CPU-only thermal reload
through the proven bounded lifecycle before its own authorized acceptance; only
after successful acceptance prepare persistence and explicitly distinguish it
from unperformed reboot/firmware-upgrade tests.


### CPU90 accepted independently; sensor cache repair still incomplete

The subsequent CPU-only activation loaded `90:70:60:55` in a fresh HAL process.
Seven samples over one minute confirmed continuing native CPU-cache refresh.
Only CPU shutdown temperature changed from 85 to 90; other thresholds, counters
and delays remain unchanged. This supersedes the unapplied status above.

The boot overlay now runs the host-gated thermal policy before the independent
reconciler. The prior overlay is preserved as
`qtier-map.before-thermal90-20261020.cpio.gz`; the installed archive SHA256 is
`692c1f5f715c5e76db71123c3354b94978e9b32971147a359225961a595ca85b`.
Its `sensors.pending` marker prevents unvalidated sensor activation at startup.
Cold boot and firmware upgrade have not been tested. Changed native binary
hashes or an incompatible profile fail closed; arbitrary future upgrades are
not guaranteed to accept this policy. Review the status and newly loaded HAL
thresholds after any reboot or update.

For rollback, retain the original archive and CPU-only configuration backup.
Under the same verified boot-device/mount gates, restoring the prior archive
reverts future startup behavior. Reverting the active CPU threshold additionally
requires restoring the saved `hal_util.conf` and a separately bounded native
monitor reload; replacing the archive alone does not change a running HAL.
Do not restore disk mappings or unrelated configuration as part of this rollback.

Sensor verification now uses the native `TEMP_1` contract, alongside `CPUT_1`
and two `FANR` fields, compared with fresh BMC samples. Known residual sensor
fields are removed only while the monitor is confirmed stopped, with an exact
backup; no temperatures or RPM values are synthesized. Readiness polling allows
initial asynchronous population within the existing transaction budget.

The latest completed count diagnostic confirmed two temperatures and one CPU
through `SE_Get_Info`, and two temperatures/two fans through the direct count
interfaces. Independent temperature and fan reads were valid, but the native
motherboard cache remained absent. The attempt rolled back in 75.4 seconds;
the replacement monitor again loaded 90/70/60/55. This is not sensor acceptance.
Native motherboard-cache generation remains under investigation. Runtime library
paths confirmed the original HAL library with no preload override. These results
exclude neither an internal sampling failure nor a process-specific call-path
issue; they do not establish a root cause for the earlier orderly shutdowns.


### Sensor sampling contention repaired and live acceptance passed

A bounded trace caught a real motherboard read rejected by the adapter's
nonblocking KCS lock while another sensor reader held it. Independent probes
and HAL temperature/fan threads share this lock. The adapter now waits up to
0.5 seconds for that process lock before reporting busy. The hardware transaction
still has its original three-second limit and refuses an already-busy KCS state;
there is no controller reset, command expansion, PWM write or fan-mode change.
This fixes an observed sampling failure; it does not attribute earlier NAS
shutdowns to this race.

The subsequent sensor transaction completed in 22.99 seconds. HAL itself created
`TEMP_1=48`, `SYST_1=48`, `FANR_1=2400` and `FANR_2=1900`, matching fresh BMC
readings. CPU threshold remained 90/70/60/55. Follow-up observations showed native
motherboard values advance from 48 to 49 to 51 as BMC temperature changed, with
fan values continuing to vary. A one-minute continuous check passed. An extended
check initially imposed an overly strict requirement that every ten-second
observer sample have a new file timestamp; it stopped at one unchanged timestamp.
The follow-up uses a bounded freshness window and requires repeated timestamp
advancement over the whole observation, rather than assuming observer and native
sampling cycles are synchronized.

The native page contract was checked without bypassing web authentication:
`manaRequest.cgi` imports `SE_Get_System_Status` and emits `sys_tempc` from the
status structure; the QTS store maps this to `sysTempC`. The status function
reads `TEMP_1`, and its runtime result agreed with the cache throughout sampling.
The same function consumes `FANR_%d`; the dashboard builds its fan rows from
native data. A newly authenticated browser rendering was not captured in this
session, so this acceptance covers the underlying interfaces and page contract.

The accepted startup design runs CPU policy independently, then runs the sensor
policy under native-binary, host-profile, healthy-monitor and CPU-temperature
gates. Each sensor transaction has a 60-second work deadline and a 120-second
recovery deadline, with the specific IPC-cleanup grace capped at 25 seconds.
A changed firmware binary fails closed pending review. The accepted archive
removes `sensors.pending`; the previous CPU-only archive remains available to
restore that disabled-sensor startup behavior. Reboot and upgrade survival still
require later operational validation; neither was performed during this repair.


Final acceptance: 19 samples over three minutes passed the freshness and
BMC/native-status comparisons, with 19 distinct cache timestamps and motherboard
values of 51–52 C in that observation window. The original one-minute run and
intermediate observations also recorded 48, 49 and 51 C. Both fan values were
read back through `SE_Get_System_Status` and matched the native cache. The
production sensor entry point returned `state=ok, changed=[]` with the same HAL
PID, confirming a second invocation did not trigger another reload.

The final overlay was installed and verified as SHA256
`512adaa83265aed36fe6821f9a457dabcfa3dfe07310f8d1916dc45cf802d029`.
`qtier-map.before-sensors-20261020.cpio.gz` retains the accepted CPU-only overlay
(SHA256 `692c1f5f715c5e76db71123c3354b94978e9b32971147a359225961a595ca85b`).
The boot partition was unmounted after verification. The running HAL remained
healthy with 90/70/60/55 loaded. All 93 repository tests passed, including
real competing-process KCS locking, timeout handling, rollback ordering, native
cache validation, independent CPU policy, and archive-member preservation.
Private traces, firmware binaries, host profiles and installation scripts with
physical device identifiers are excluded from the public repository.
