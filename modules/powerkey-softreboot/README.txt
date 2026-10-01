Power Key → KernelSU Soft Reboot v1.2 Native

Design
- Native ARM64 daemon; no getevent process.
- Discovers the input event device that advertises KEY_POWER using EVIOCGBIT.
- Blocks in poll() until an input event arrives.
- Watches only KEY_POWER presses.
- Uses flock() so repeated KernelSU late-load/service execution still leaves only one daemon.
- Default: 4 POWER presses within 3000 ms.
- Trigger: ksud soft-reboot.
- No /proc/sysrq-trigger.

Configuration
  PRESS_COUNT=4
  WINDOW_MS=3000

Log
  /data/adb/modules/powerkey_ksu_softreboot/power-soft-reboot.log

Verify one instance
  ps -A | grep powerkeyd

There should be one powerkeyd and zero module-owned getevent processes.
