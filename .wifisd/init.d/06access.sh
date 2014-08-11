#!/bin/sh
# add custom dhcp code (ntpd & local access)
cat /mnt/sd/.wifisd/access.sh >>/etc/dhcp.script
