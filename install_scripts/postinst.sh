#!/bin/bash

packdir=$(pip3 show automathemely | grep -oP "^Location: \K.*")
sudo chmod a+x "$packdir/automathemely/bin/cron-trigger"
sudo chmod a+x "$packdir/automathemely/bin/run.py"
sudo chmod a+x "$packdir/automathemely/autoth_tools/updsunhours.py"
