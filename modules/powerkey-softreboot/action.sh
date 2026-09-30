#!/system/bin/sh
KSUD=/data/adb/ksud
[ -x "$KSUD" ] || KSUD="$(command -v ksud 2>/dev/null)"
if [ -z "$KSUD" ]; then
    echo "ksud not found"
    exit 1
fi
echo "Triggering KernelSU soft reboot..."
sync
exec "$KSUD" soft-reboot
