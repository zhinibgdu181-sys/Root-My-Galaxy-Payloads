Power Key → KernelSU Manager Soft Reboot v1.6

Why this version exists
KernelSU Manager's soft-reboot UI does NOT simply run:
/data/adb/ksud soft-reboot

The Manager source calls:
execKsud("soft-reboot", newShell=true, globalMnt=true)

That means:
1. use the Manager-bundled libksud.so
2. create a fresh KernelSU root shell
3. switch that shell to the global mount namespace
4. run the same Manager-bundled libksud.so soft-reboot inside it

v1.6 mirrors that sequence.

Watcher
- Native ARM64
- monitors every KEY_POWER input node
- blocking poll() while idle
- flock() single-instance
- 120 ms duplicate suppression for mirrored Samsung input events
- trigger: 4 POWER presses within 3000 ms

Manager package expected
me.weishu.kernelsu

Log
/data/adb/modules/powerkey_ksu_softreboot/power-soft-reboot.log

Expected trigger log
TRIGGER: manager-equivalent soft reboot via .../lib/arm64/libksud.so debug su -g
