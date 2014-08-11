#!/bin/sh
#telnetd -l /bin/bash &

for SCRIPT in /mnt/sd/.wifisd/init.d/*.sh; do
    chmod a+x $SCRIPT
    . $SCRIPT
done
