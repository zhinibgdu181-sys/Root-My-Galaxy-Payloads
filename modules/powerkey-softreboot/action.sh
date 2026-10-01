#!/system/bin/sh

APK="$(pm path me.weishu.kernelsu 2>/dev/null | sed -n '1s/^package://p')"
APPDIR="${APK%/base.apk}"
KSUD="$APPDIR/lib/arm64/libksud.so"

if [ -z "$APK" ] || [ ! -x "$KSUD" ]; then
  echo "KernelSU Manager libksud.so not found: $KSUD"
  exit 1
fi

echo "Using KernelSU Manager path:"
echo "$KSUD"
echo "Starting manager-equivalent global-mount soft reboot..."

# Mirror KernelSU Manager:
#   libksud.so debug su -g
# then inside that fresh global-mount root shell:
#   libksud.so soft-reboot
printf "'%s' soft-reboot\nexit\n" "$KSUD" | "$KSUD" debug su -g
