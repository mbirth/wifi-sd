# https://www.pitt-pladdy.com/blog/_20140202-083815_0000_Transcend_Wi-Fi_SD_Hacks_CF_adaptor_telnet_custom_upload_/

# kill existing ntp daemon
[ -f /var/run/ntpd.pid ] && kill `cat /var/run/ntpd.pid`

# try start a new ntp daemon
if [ -n "$ntpsrv" ]; then
    ntpcommand="busybox-extra ntpd"
    for ntp in $ntpsrv; do
        ntpcommand="$ntpcommand -p $ntp"
    done
    $ntpcommand
else
    busybox-extra ntpd -p pool.ntp.org
fi
