#!/system/bin/sh
ui_print "- PowerKey SoftReboot: setting file permissions"
set_perm "$MODPATH/service.sh" 0 0 0755
set_perm "$MODPATH/action.sh" 0 0 0755
set_perm "$MODPATH/uninstall.sh" 0 0 0755
set_perm "$MODPATH/bin/powerkeyd" 0 0 0755
