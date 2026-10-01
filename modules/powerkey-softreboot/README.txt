Power Key → KernelSU Soft Reboot v1.5

Compatibility fix
- Uses only /data/adb/ksud for soft reboot.
- Never invokes /data/local/tmp/ksud-s25u-kdp.
- The staging ksud used by Root-My-Galaxy late-load can differ from the installed canonical KernelSU userspace binary.

Watcher
- Native ARM64 daemon.
- Monitors all input nodes that advertise KEY_POWER.
- poll() blocks while idle.
- flock() keeps a single daemon across repeated late-load/service runs.
- 120 ms duplicate suppression for mirrored Samsung input events.
- Trigger: 4 POWER presses within 3000 ms.

Log
/data/adb/modules/powerkey_ksu_softreboot/power-soft-reboot.log
