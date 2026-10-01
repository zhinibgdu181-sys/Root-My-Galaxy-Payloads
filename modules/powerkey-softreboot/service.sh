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

# KernelSU Manager does not use /data/adb/ksud for its soft-reboot UI action.
# It executes the app-bundled libksud.so through a fresh global-mount root shell.
APK="$(pm path me.weishu.kernelsu 2>/dev/null | sed -n '1s/^package://p')"
APPDIR="${APK%/base.apk}"
MANAGER_KSUD="$APPDIR/lib/arm64/libksud.so"

if [ -z "$APK" ] || [ ! -x "$MANAGER_KSUD" ]; then
  echo "$(date '+%Y-%m-%d %H:%M:%S') ERROR: KernelSU Manager libksud.so not found: $MANAGER_KSUD" >> "$LOG"
  exit 1
fi

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

# Repeated KernelSU late-load should be a no-op when the exact same daemon is
# already running. After an in-place module upgrade, stop the stale daemon.
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

echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: launching $BIN press_count=$PRESS_COUNT window_ms=$WINDOW_MS manager_ksud=$MANAGER_KSUD" >> "$LOG"
nohup "$BIN" "$PRESS_COUNT" "$WINDOW_MS" "$MANAGER_KSUD" >/dev/null 2>&1 &
exit 0
