#!/bin/sh
chmod a+x /mnt/sd/.wifisd/cgi-bin/refresh_sd
chmod a+x /mnt/sd/.wifisd/cgi-bin/wifi_delete
ln -s /mnt/sd/.wifisd/cgi-bin/refresh_sd /www/cgi-bin/refresh_sd
ln -s /mnt/sd/.wifisd/cgi-bin/wifi_delete /www/cgi-bin/wifi_delete
