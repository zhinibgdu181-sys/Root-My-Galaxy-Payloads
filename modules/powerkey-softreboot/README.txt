Power Key → KernelSU Soft Reboot v1.3 Native

Changes from v1.2
- Monitors every /dev/input/event* device that advertises KEY_POWER.
- Uses one native process and one poll() call; no getevent subprocesses.
- 120 ms duplicate guard prevents mirrored input nodes from counting one physical press twice.
- flock() keeps the module single-instance across repeated KernelSU late-load/service runs.
- Logs every selected input device and the ksud path used for soft reboot.

Default trigger
  Press POWER 4 times within 3000 ms.

Configuration
  PRESS_COUNT=4
  WINDOW_MS=3000

Log
  /data/adb/modules/powerkey_ksu_softreboot/power-soft-reboot.log

Manual verification
  ps -A | grep powerkeyd
  cat /data/adb/modules/powerkey_ksu_softreboot/power-soft-reboot.log

Expected idle state
- one powerkeyd process
- no getevent process created by this module
