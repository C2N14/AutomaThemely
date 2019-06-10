#!/bin/bash

packdir="$(python3 -m pip show automathemely | grep -oP "^Location: \K.*")/automathemely"

if_not_dir_create () {
  if [[ ! -d "$1" ]]; then
  mkdir -p "$1"
  fi
}


local_install=false
## CHECK FOR ROOT PRIVILEGES
if ((${EUID:-0} || "$(id -u)")); then

    if [[ -z "$SUDO_USER" ]]; then
        echo "SUDO_USER variable not found, trying to find user manually..."
        SUDO_USER=$(logname)
        SUDO_UID=$(id -u ${SUDO_USER})

        if [[ -z "$SUDO_USER" ]]; then
            echo "Could not find SUDO_USER, falling back to local only installation..."
            local_install=true
        fi

    fi

else
    echo "Root privileges not detected, falling back to local only installation..."
    local_install=true

fi


## SET RELEVANT VARIABLES
if [[ "$local_install" = true ]]; then
    autostart_path="$HOME/.config/autostart"
    systemd_user_path="$HOME/.config/systemd/user"
    echo "NOTE: AutomaThemely is disabled from autostarting by default on local installation"

else
    autostart_path="/etc/xdg/autostart"
    systemd_user_path="/usr/lib/systemd/user"

fi


## MOVE FILES TO LOCATIONS
# Autostart on user log in
if_not_dir_create "$autostart_path"
cp "$packdir/installation_files/autostart.desktop" "$autostart_path/automathemely.desktop"
sed -i "s|<PACKDIR>|$packdir|g" "$autostart_path/automathemely.desktop"

# Timer & service units
if_not_dir_create "$systemd_user_path"
cp "$packdir/installation_files/sun-times.timer" "$systemd_user_path/automathemely.timer"
cp "$packdir/installation_files/sun-times.service" "$systemd_user_path/automathemely.service"
sed -i "s|<PACKDIR>|$packdir|g" "$systemd_user_path/automathemely.service"


## ENABLE SYSTEMD
if [[ "$local_install" = true ]]; then
    systemctl --user daemon-reload
    systemctl --user enable automathemely.timer
    systemctl --user start automathemely.timer

else
    # Export some vars required to make some systemd user commands work
    export XDG_RUNTIME_DIR="/run/user/${SUDO_UID}"
    export DBUS_SESSION_BUS_ADDRESS="unix:path=${XDG_RUNTIME_DIR}/bus"

    sudo -E -u ${SUDO_USER} systemctl --user --global daemon-reload
    sudo systemctl --global enable automathemely.timer
    sudo -E -u ${SUDO_USER} systemctl --user --global start automathemely.timer

fi


## REMOVE OBSOLETE STUFF
# Crontab removal
# If crontabs are not installed carries on
(crontab -u ${SUDO_USER} -l | awk ' !/sunrise_change_theme/ && !/sunset_change_theme/ && !/update_sunhours_daily/ && !/update_sunhours_reboot/ { print }' | crontab -u ${SUDO_USER} -) || true

