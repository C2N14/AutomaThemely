#!/bin/bash
# Compare last modified date of first arg to current date before executing the second arg, this is needed because to
# make sure it runs every boot AND daily, Persistent=true is needed, but it will try to run several times if several
# days have passed since the last boot.
#
# First tried adding it as a one liner to ExecStart but it failed to run stat, cut and date even with /bin/bash -c
if [ "$(stat -c %y "$(echo ~)$1" | cut -f 1 -d " ")" != "$(date +%F)" ]; then
    eval $2
fi
