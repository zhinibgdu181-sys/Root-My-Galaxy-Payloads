#!/system/bin/sh
KSUD=/data/adb/ksud
[ -x "$KSUD" ] || KSUD=/data/local/tmp/ksud-s25u-kdp
if [ ! -x "$KSUD" ]; then
  echo "ksud not found"
  exit 1
fi
echo "Triggering KernelSU soft reboot..."
sync
exec "$KSUD" soft-reboot
