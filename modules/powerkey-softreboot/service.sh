#!/system/bin/sh
MODDIR=${0%/*}
CONFIG="$MODDIR/config.conf"
PRESS_COUNT=4
WINDOW_MS=3000

[ -f "$CONFIG" ] && . "$CONFIG"

case "$PRESS_COUNT" in
  ''|*[!0-9]*) PRESS_COUNT=4 ;;
esac
case "$WINDOW_MS" in
  ''|*[!0-9]*) WINDOW_MS=3000 ;;
esac

while [ "$(getprop sys.boot_completed 2>/dev/null)" != "1" ]; do
  sleep 2
done

BIN="$MODDIR/bin/powerkeyd"
[ -x "$BIN" ] || {
  echo "$(date '+%Y-%m-%d %H:%M:%S') ERROR: $BIN missing/not executable" >> "$MODDIR/power-soft-reboot.log"
  exit 1
}

# Native daemon owns an exclusive flock, so repeated KernelSU late-load/service
# invocations cannot create duplicate watchers.
nohup "$BIN" "$PRESS_COUNT" "$WINDOW_MS" >/dev/null 2>&1 &
exit 0
