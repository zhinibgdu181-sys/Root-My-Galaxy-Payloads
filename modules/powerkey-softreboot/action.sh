#!/system/bin/sh
MODDIR=${0%/*}
LOG="$MODDIR/power-soft-reboot.log"
echo "$(date '+%Y-%m-%d %H:%M:%S') ACTION_BLOCKED: ksud soft-reboot disabled on SM-S9360 temporary-root safety build" >> "$LOG"
echo "Blocked: ksud soft-reboot is disabled on this safety build because it caused a black-screen userspace failure on SM-S9360 temporary-root."
exit 1
