#!/system/bin/sh
KSUD=/data/adb/ksud

if [ ! -x "$KSUD" ]; then
  echo "Canonical KernelSU userspace binary not found: $KSUD"
  exit 1
fi

echo "Triggering KernelSU soft reboot through $KSUD ..."
sync
exec "$KSUD" soft-reboot
