#!/system/bin/sh
MODDIR=${0%/*}
CONFIG="$MODDIR/config.conf"
LOCK="$MODDIR/powerkeyd.lock"
PRESS_COUNT=4
WINDOW_MS=3000
TRIGGER_DELAY_MS=1000
BUILD_ID="v1.7.1-release-delay"

[ -f "$CONFIG" ] && . "$CONFIG"

case "$PRESS_COUNT" in
  ''|*[!0-9]*) PRESS_COUNT=4 ;;
esac
case "$WINDOW_MS" in
  ''|*[!0-9]*) WINDOW_MS=3000 ;;
esac
case "$TRIGGER_DELAY_MS" in
  ''|*[!0-9]*) TRIGGER_DELAY_MS=1000 ;;
esac

while [ "$(getprop sys.boot_completed 2>/dev/null)" != "1" ]; do
  sleep 2
done

BIN="$MODDIR/bin/powerkeyd"
LOG="$MODDIR/power-soft-reboot.log"


if [ ! -f "$BIN" ]; then
  echo "$(date '+%Y-%m-%d %H:%M:%S') ERROR: powerkeyd file missing: $BIN" >> "$LOG"
  exit 1
fi

# Some module installers do not preserve the executable bit of nested files.
# Repair it every time service.sh is invoked.
chmod 0755 "$BIN" 2>/dev/null

if [ ! -x "$BIN" ]; then
  echo "$(date '+%Y-%m-%d %H:%M:%S') ERROR: powerkeyd exists but chmod 0755 failed: $BIN" >> "$LOG"
  ls -lZ "$BIN" >> "$LOG" 2>&1
  exit 1
fi

# Keep a running daemon only when its argv contains the exact current build ID.
# This avoids stale v1.6/v1.7 processes surviving an in-place module upgrade.
if [ -f "$LOCK" ]; then
  PID="$(cat "$LOCK" 2>/dev/null)"
  case "$PID" in
    ''|*[!0-9]*) PID="" ;;
  esac

  if [ -n "$PID" ] && [ -e "/proc/$PID/cmdline" ]; then
    CMDLINE="$(tr '\000' ' ' < "/proc/$PID/cmdline" 2>/dev/null)"
    case "$CMDLINE" in
      *"$BUILD_ID"*)
        echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: current powerkeyd already running pid=$PID build_id=$BUILD_ID" >> "$LOG"
        exit 0
        ;;
      *)
        echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: replacing stale powerkeyd pid=$PID old_cmdline=$CMDLINE" >> "$LOG"
        kill "$PID" 2>/dev/null
        sleep 1
        ;;
    esac
  fi
fi

rm -f "$LOCK"
echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: launching $BIN press_count=$PRESS_COUNT window_ms=$WINDOW_MS trigger_delay_ms=$TRIGGER_DELAY_MS build_id=$BUILD_ID" >> "$LOG"
nohup "$BIN" "$PRESS_COUNT" "$WINDOW_MS" "$TRIGGER_DELAY_MS" "$BUILD_ID" >/dev/null 2>&1 &
exit 0
