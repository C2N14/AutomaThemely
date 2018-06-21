#!/bin/bash

python3 - <<END
from crontab import CronTab
import os

crontabs = ['sunrise_change_theme', 'sunset_change_theme', 'update_sunhours_daily', 'update_sunhours_reboot']
cron = CronTab(user=os.environ['SUDO_USER'])
for tab in crontabs:
    cron.remove_all(comment=tab)

cron.write()

END

USER_HOME=$(getent passwd $SUDO_USER | cut -d: -f6)
rm -rf "$USER_HOME/.config/AutomaThemely"

