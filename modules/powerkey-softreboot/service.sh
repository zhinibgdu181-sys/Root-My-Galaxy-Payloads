#!/system/bin/sh
MODDIR=${0%/*}
CONFIG="$MODDIR/config.conf"
LOCK="$MODDIR/powerkeyd.lock"
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
LOG="$MODDIR/power-soft-reboot.log"

[ -x "$BIN" ] || {
  echo "$(date '+%Y-%m-%d %H:%M:%S') ERROR: $BIN missing/not executable" >> "$LOG"
  exit 1
}

# If an instance is already running, keep it only when it is the exact same
# binary. This makes normal repeated late-load invocations no-ops, while an
# in-place module upgrade can replace the old daemon cleanly.
if [ -f "$LOCK" ]; then
  PID="$(cat "$LOCK" 2>/dev/null)"
  case "$PID" in
    ''|*[!0-9]*) PID="" ;;
  esac

  if [ -n "$PID" ] && [ -e "/proc/$PID/exe" ]; then
    OLD_HASH="$(sha256sum "/proc/$PID/exe" 2>/dev/null | awk '{print $1}')"
    NEW_HASH="$(sha256sum "$BIN" 2>/dev/null | awk '{print $1}')"

    if [ -n "$OLD_HASH" ] && [ "$OLD_HASH" = "$NEW_HASH" ]; then
      echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: current powerkeyd already running pid=$PID" >> "$LOG"
      exit 0
    fi

    echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: replacing old powerkeyd pid=$PID" >> "$LOG"
    kill "$PID" 2>/dev/null
    sleep 1
  fi
fi

nohup "$BIN" "$PRESS_COUNT" "$WINDOW_MS" >/dev/null 2>&1 &
exit 0
