#!/bin/bash

USER_HOME="$(getent passwd $SUDO_USER | cut -d: -f6)"
packdir="$(sudo -u ${SUDO_USER} python3 -m pip show automathemely | grep -oP "^Location: \K.*")/automathemely"

if_not_dir_create () {
  if [ ! -d "$1" ]; then
  mkdir -p "$1"
  fi
}

# Autostart HEREDOC
autostart_path="/etc/xdg/autostart/automathemely.desktop"
if_not_dir_create "$(dirname "$autostart_path")"
tee "/etc/xdg/autostart/automathemely.desktop" <<EOF > /dev/null
[Desktop Entry]
Type=Application
Name=AutomaThemely
Comment=Unity & GNOME python application for changing between themes periodically.
Exec=/usr/bin/env python3 ${packdir}/bin/autothscheduler.py
Icon=automathemely
EOF

# Timer & service HEREDOCS
systemd_user_path="/usr/lib/systemd/user"
if_not_dir_create "$systemd_user_path"

tee "$systemd_user_path/automathemely.timer" <<EOF > /dev/null
[Unit]
Description=Update automathemely sun times daily

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF

tee "$systemd_user_path/automathemely.service" <<EOF > /dev/null
[Unit]
Description=Update automathemely sun times daily
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/bin/bash ${packdir}/bin/systemd-trigger.sh "${USER_HOME}/.config/AutomaThemely/sun_times" "/usr/bin/env python3 ${packdir}/autoth_tools/updsuntimes.py"
EOF

# Export some vars required to make some systemd user commands work
export XDG_RUNTIME_DIR="/run/user/${SUDO_UID}"
export DBUS_SESSION_BUS_ADDRESS="unix:path=${XDG_RUNTIME_DIR}/bus"

sudo -E -u $SUDO_USER systemctl --user --global daemon-reload
sudo systemctl --user --global enable automathemely.timer
sudo -E -u $SUDO_USER systemctl --user --global start automathemely.timer

# REMOVE OBSOLETE STUFF
# Crontab removal
# If crontabs are not installed carries on
(crontab -u $SUDO_USER -l | awk ' !/sunrise_change_theme/ && !/sunset_change_theme/ && !/update_sunhours_daily/ && !/update_sunhours_reboot/ { print }' | crontab -u $SUDO_USER -) || true
