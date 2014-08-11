# https://www.pitt-pladdy.com/blog/_20140202-083815_0000_Transcend_Wi-Fi_SD_Hacks_CF_adaptor_telnet_custom_upload_/

# kill existing telnet & ftp daemons
killaccessdaemons() {
    if [ -f /var/run/telnetd.pid ]; then
        kill `cat /var/run/telnetd.pid`
        rm /var/run/telnetd.pid
    fi
    if [ -f /var/run/ftpd.pid ]; then
        kill `cat /var/run/ftpd.pid`
        rm /var/run/ftpd.pid
    fi
}

# start telnet & ftp daemons
startaccessdaemons() {
    if [ ! -f /var/run/telnetd.pid ] || [ ! -d /proc/`cat /var/run/telnetd.pid` ]; then
        telnetd -F -l /bin/bash &
        echo $! >/var/run/telnetd.pid
    fi
    if [ ! -f /var/run/ftpd.pid ] || [ ! -d /proc/`cat /var/run/ftpd.pid` ]; then
        # add -w to allow write access
        tcpsvd -vE 0.0.0.0 21 ftpd /mnt/sd/ &
        echo $! >/var/run/ftpd.pid
    fi
}

# kill the autoupload process
killautoupload() {
    if [ -f /var/run/autoupload.pid ]; then
        kill `cat /var/run/autoupload.pid`
        rm /var/run/autoupload.pid
    fi
}

# start autoupload
startautoupload() {
    if [ ! -f /var/run/autoupload.pid ] || [ ! -d /proc/`cat /var/run/autoupload.pid` ]; then
        autoupload.pl
        echo $! >/var/run/autoupload.pid
    fi
}


# collect info about our surroundings
apssid=`busybox-extra head -n 1 /tmp/iwconfig_maln0.txt | busybox-extra sed 's/^.*ESSID:"\([^"]\+\)".*$/\1/'`
ping -c 1 $router >/dev/null 2>&1
routerMAC=`busybox-extra arp -n $router | busybox-extra awk '{print $4}'`

# check the situation and act accordingly
case "$1" in
    deconfig)
        killaccessdaemons
    ;;
    bound)
        echo "$apssid:$router:$routerMAC" >>/tmp/netid.log
        case "$apssid:$router:$routerMAC" in
            'SSID:11.22.33.44:ab:cd:ef:12:34:56'|'SECOND_SSID:11.22.33.44:fe:dc:ba:98:76:54')
                # trusted network - run open access (telnetd / ftpd)
                killautoupload
                startaccessdaemons
            ;;
            *)
                # unknown - start auto-uploader TODO
                killaccessdaemons
                #startautoupload
            ;;
        esac
    ;;
    renew)
        # do nothing - no change
    ;;
esac
