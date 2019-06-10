#!/bin/bash

pkill -f "autothscheduler.py"


local_install=false
## CHECK FOR ROOT PRIVILEGES
if ((${EUID:-0} || "$(id -u)")); then

    if [[ -z "$SUDO_USER" ]]; then
        echo "SUDO_USER variable not found, trying to find user manually..."
        SUDO_USER=$(logname)
        SUDO_UID=$(id -u ${SUDO_USER})

        if [[ -z "$SUDO_USER" ]]; then
            echo "Could not find SUDO_USER, trying to remove local installation..."
            local_install=true
        fi

    fi

else
    echo "Root privileges not detected, trying to remove local installation..."
    local_install=true

fi


if [[ "$local_install" = true ]]; then
    systemctl --user stop automathemely.timer
    systemctl --user disable automathemely.timer
    systemctl --user daemon-reload

else
    # Export some vars required to make some systemd user commands work
    export XDG_RUNTIME_DIR="/run/user/${SUDO_UID}"
    export DBUS_SESSION_BUS_ADDRESS="unix:path=${XDG_RUNTIME_DIR}/bus"

    sudo -E -u ${SUDO_USER} systemctl --user --global stop automathemely.timer
    sudo systemctl --global disable automathemely.timer
    sudo -E -u ${SUDO_USER} systemctl --user --global daemon-reload

fi
