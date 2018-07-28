#!/bin/bash

USER_HOME=$(getent passwd $SUDO_USER | cut -d: -f6)
rm -rf "$USER_HOME/.config/AutomaThemely"
rm -rf "/etc/xdg/autostart/automathemely.desktop"

pkill -f "autothscheduler.py"

# Export some vars required to make some systemd user commands work
export XDG_RUNTIME_DIR="/run/user/${SUDO_UID}"
export DBUS_SESSION_BUS_ADDRESS="unix:path=${XDG_RUNTIME_DIR}/bus"

sudo -E -u $SUDO_USER systemctl --user --global stop automathemely.timer
sudo systemctl --user --global disable automathemely.timer
sudo -E -u $SUDO_USER systemctl --user --global daemon-reload