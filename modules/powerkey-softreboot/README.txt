Power Key → KernelSU Soft Reboot v1.1 Low Power

Default trigger:
  Press POWER 4 times within 3 seconds.

Low-power behavior:
  - Scans /dev/input/event* after boot.
  - Finds the event node advertising KEY_POWER.
  - Listens ONLY to that event node.
  - Touchscreen/fingerprint/volume events do not enter the watcher.
  - Does not use /proc/sysrq-trigger.

Reboot action:
  /data/adb/ksud soft-reboot

Manual test:
  Use the module Action button in KernelSU Manager.

Configuration:
  Edit config.conf:
    PRESS_COUNT=4
    WINDOW_SEC=3
  Then reboot once.

Log:
  /data/adb/modules/powerkey_ksu_softreboot/power-soft-reboot.log
