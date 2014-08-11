#!/bin/sh

# copy files from specific sd card directory /WIFISD/ 
# to servers root directory
cp -Rf /mnt/sd/.wifisd/chdk/* /www/

# make scipts executable
chmod a+x /www/cgi-bin/*

# add links to /www/frame1.html (insert before </tbody></table>)
# Schema: <tr><td width="100%"><a href="/..." target="f3">&#8226; Title</a></td></tr>
busybox-extra sed -i.orig1 -e 's/<\/tbody>/<tr><td width="100%"><a href="\/chdk.html" target="f3">\&#8226; CHDK<\/a><\/td><\/tr>\n<\/tbody>/' /www/frame1.html
busybox-extra sed -i.orig2 -e 's/<\/tbody>/<tr><td width="100%"><a href="\/webdev.html" target="f3">\&#8226; WebDev<\/a><\/td><\/tr>\n<\/tbody>/' /www/frame1.html
