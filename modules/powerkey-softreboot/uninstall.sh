#!/system/bin/sh
MODDIR=${0%/*}
LOCK="$MODDIR/powerkeyd.lock"

if [ -f "$LOCK" ]; then
  PID="$(cat "$LOCK" 2>/dev/null)"
  case "$PID" in
    ''|*[!0-9]*) ;;
    *)
      if [ -r "/proc/$PID/cmdline" ]; then
        CMD="$(tr '\0' ' ' < "/proc/$PID/cmdline" 2>/dev/null)"
        case "$CMD" in
          *powerkeyd*) kill "$PID" 2>/dev/null ;;
        esac
      fi
      ;;
  esac
fi

rm -f "$LOCK" "$MODDIR/power-soft-reboot.log"
exit 0
