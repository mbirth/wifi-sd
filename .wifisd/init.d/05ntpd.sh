#!/bin/sh
# add custom dhcp code (ntpd & local access)
cat /mnt/sd/.wifisd/ntpd.sh >>/etc/dhcp.script
