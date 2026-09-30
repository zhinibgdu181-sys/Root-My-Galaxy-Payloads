#!/system/bin/sh
MODDIR=${0%/*}
LOGFILE="$MODDIR/power-soft-reboot.log"
CONFIG="$MODDIR/config.conf"

PRESS_COUNT=4
WINDOW_SEC=3
[ -f "$CONFIG" ] && . "$CONFIG"

log_msg() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> "$LOGFILE"
}

find_ksud() {
    if [ -x /data/adb/ksud ]; then
        echo /data/adb/ksud
        return 0
    fi
    if command -v ksud >/dev/null 2>&1; then
        command -v ksud
        return 0
    fi
    return 1
}

find_getevent() {
    for p in /system/bin/getevent /vendor/bin/getevent /odm/bin/getevent; do
        if [ -x "$p" ]; then
            echo "$p"
            return 0
        fi
    done
    return 1
}

find_power_device() {
    ge="$1"
    for dev in /dev/input/event*; do
        [ -e "$dev" ] || continue
        caps="$("$ge" -lp "$dev" 2>/dev/null)"
        echo "$caps" | grep -q "KEY_POWER" || continue
        echo "$dev"
        return 0
    done
    return 1
}

while [ "$(getprop sys.boot_completed 2>/dev/null)" != "1" ]; do
    sleep 2
done

KSUD="$(find_ksud)"
if [ -z "$KSUD" ]; then
    log_msg "ERROR: ksud not found"
    exit 1
fi

if ! "$KSUD" --help 2>&1 | grep -q "soft-reboot"; then
    log_msg "ERROR: this ksud does not expose soft-reboot"
    exit 1
fi

GETEVENT="$(find_getevent)"
if [ -z "$GETEVENT" ]; then
    log_msg "ERROR: getevent not found"
    exit 1
fi

POWER_DEV=""
attempt=0
while [ -z "$POWER_DEV" ] && [ "$attempt" -lt 12 ]; do
    POWER_DEV="$(find_power_device "$GETEVENT")"
    [ -n "$POWER_DEV" ] && break
    attempt=$((attempt + 1))
    sleep 5
done

if [ -z "$POWER_DEV" ]; then
    log_msg "ERROR: KEY_POWER input device not found"
    exit 1
fi

log_msg "START: power_dev=$POWER_DEV press_count=$PRESS_COUNT window_sec=$WINDOW_SEC ksud=$KSUD"

"$GETEVENT" -lt "$POWER_DEV" 2>/dev/null | while IFS= read -r line; do
    case "$line" in
        *EV_KEY*KEY_POWER*DOWN*)
            now="$(date +%s)"
            if [ -z "$first_press" ] || [ $((now - first_press)) -gt "$WINDOW_SEC" ]; then
                first_press="$now"
                count=1
            else
                count=$((count + 1))
            fi
            log_msg "POWER_DOWN count=$count first=$first_press now=$now"
            if [ "$count" -ge "$PRESS_COUNT" ] && [ $((now - first_press)) -le "$WINDOW_SEC" ]; then
                log_msg "TRIGGER: ksud soft-reboot"
                count=0
                first_press=""
                sync
                "$KSUD" soft-reboot >> "$LOGFILE" 2>&1
                rc=$?
                log_msg "RETURN: rc=$rc"
                sleep 5
            fi
            ;;
    esac
done

log_msg "WARN: getevent exited; watcher stopped"
