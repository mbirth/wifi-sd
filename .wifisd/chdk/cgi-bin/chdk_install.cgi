#!/usr/bin/perl
# license: GPL V2
# (c)2014 rudi, forum.chdk-treff.de
use URI::Escape;

my $unzip = "/usr/bin/unzip";
my $srcfolder = "/tmp/";
my $mainhtml = "/chdk.html";
my $form;
my $qsChdkZip;              #querystring filename
my $qsChdkZipSize;          #querystring filesize
my $qsChdkFileCount = 0;    #querystring file count
my $qsTime = 0;             #time for set server time
my $chdkZip;                #full path filename
my $chdkFileCount = 0;      #checkZipContent file count
my $chdkUPsize = 0;         #unpacked size of chdk files
my $fullChdk = 0;           #zip type
my $updTime = 0;            #time need update
my $langDE = ($ENV{'HTTP_ACCEPT_LANGUAGE'} =~ /^de/)?1:0;   #user language german from HTTP_ACCEPT_LANGUAGE
my $htmlTitle = (!$langDE)?"install CHDK":"CHDK einrichten";
my $htmlCheckErr;

sub isSvrTime {
  my (undef, $min, $hour, $day, $mon, $year) = localtime();
  $year = $year+1900;
  $mon = $mon+1;
  $mon = ($mon > 9)?$mon:"0".$mon;
  $day = ($day > 9)?$day:"0".$day;
  $hour = ($hour > 9)?$hour:"0".$hour;
  $min = ($min > 9)?$min:"0".$min;
  my $svrTime = "$year$mon$day$hour$min";
  $updTime = ($qsTime > $svrTime)?1:0;
}

sub setSvrTime {
  if ($updTime) { `date -s $qsTime`; }
}

sub checkZipContent {
  my $fn;
  my $us = 0;
  my @res = `unzip -l $chdkZip`;
  my $res = 0;
  my $fDiskboot = 0;
  my $dModules = 0;
  foreach $line (@res) {
    if ($line =~ /(\d+)  \d\d-\d\d-\d\d \d\d:\d\d   ([\w+\/]*[\w\-]+\.\w\w\w)/) {
      $fn = $2;
      $us +=$1;
      if ($fn =~ /^CHDK\//) {
        #dir exist
        if ($fn =~ /^CHDK\/MODULES\//) { $dModules += 1; } else { $fullChdk = 1; }
      } else {
        #not chdk dir => root dir
        if ($fn =~ /\//) { $res = 0; last; } # '/' in line
        if ($fn =~ /^DISKBOOT.BIN$/) { $fDiskboot += 1; }
      }
      $res += 1;
    }
  }
  if ($res == 0 || $fDiskboot != 1 || $dModules == 0) { return 1; }
  $chdkFileCount = $res;
  $chdkUPsize = $us;
  return 0;
}

sub deleteFile {
  my $err = system("rm $chdkZip");
  if ($err == 0) {
    my @text = ("uploaded file deleted", "hochgeladene Datei gelöscht");
    print "<li>$text[$langDE]</li>\n";
  } else {
    my @text = ("Can't delete uploaded file!", "Hochgeledene Datei konnte nicht gelöscht werden!");
    print "<li>$text[$langDE]</li>\n";
  }
  return ($err)?1:0;
}

sub refreshSD {
  my $duration = shift @_;
  my @text = (
    ["synchronize files, need approximate %d seconds time ...", "synchronisiere Dateien, dauert etwa %d Sekunden ..."],
    ["... completed", "... abgeschlossen"],
    ["synchronize failed!", "Synchronisation fehlgeschlagen!"]
  );
  if ($duration > 1) { printf "<li>$text[0][$langDE]</li>\n", $duration+1; } #add time for sync
  my $err = system("sync") ||
    system("sleep $duration") ||
    system("sync") ||
    system("mount -o remount /mnt/sd");
  if ($duration > 1) { print "<li>$text[1][$langDE]</li>\n"; }
  if ($err) { print "<li class=\"error\" style=\"margin: 0px;\">$text[2][$langDE]</li>\n"; }
  return ($err)?1:0;
}

sub checkChdkZip {
  if ($abort != 0) {
    $htmlCheckErr = (!$langDE)?"Installation canceled!":"Einrichtung abgebrochen!";
    return 1;
  }
  if (length($chdkZip) == 0) {
    $htmlCheckErr = (!$langDE)?"Missing file name!":"Dateiname fehlt!";
    return 1;
  }
  if ($chdkZip !~ /.zip$/) {
    $htmlCheckErr = (!$langDE)?"ZIP file required!":"ZIP-Datei erwartet!";
    return 1;
  }
  if (checkZipContent != 0) {
    $htmlCheckErr = (!$langDE)?"CHDK ZIP file required!":"CHDK-ZIP-Datei erwartet!";
    return 1;
  }
  return 0;
}

sub processInstall {
  my @text = (
    ["Extract and copy CHDK files, please wait ...", "CHDK-Dateien werden entpackt und kopiert, bitte warten ..."],
    ["... completed", "... abgeschlossen"],
    ["Error on copy files!<br>Check filesystem with fsck/chkdsk and try installation again.", "Fehler beim Kopieren!<br>Überprüfe das Dateisystem mit fsck/chkdsk und führe die Einrichtung erneut aus."],
    ["Copied %d from %d files", "%d von %d Dateien kopiert"],
    ["Press Button 'OK' and restart the camera!", "Drücke die 'OK'-Schaltfläche und starte die Kamera neu!"]
  );
  $| = 1; #flush for print
  print "<li>$text[0][$langDE]</li>\n";
  my $err = refreshSD(1);
  if (!$err) {
    my @res = `unzip -o $chdkZip -d /mnt/sd/`;
    my $res = 0;
    foreach $line (@res) {
      if ($line =~ /inflating:/) { $res += 1; }
    }
    if ($qsChdkFileCount == $res) {
      print "<li>$text[1][$langDE]</li>\n";
    } else {
      print "<li class=\"error\" style=\"margin: 0px;\">$text[2][$langDE]</li>\n";
    }
    printf "<li>$text[3][$langDE]</li>\n", $res, $qsChdkFileCount;
    #wait duration for sync
    #highest value from data volume, ref=250'000 byte/sec
    my $wd = $chdkUPsize/250000;
    #or file count, ref=25 files/sec
    if ($res/25 > $wd) { $wd = $res/25; }
    $err = refreshSD(int($wd)+1); #round up
  }
  deleteFile;
  if (!$err) { print "<li>$text[4][$langDE]</li>\n"; }
  return ($err)?1:0;
}

sub qsSplit {
  my @nameValuePairs = split (/&/, $queryString);
  foreach $nameValue (@nameValuePairs) {
    my ($name, $value) = split (/=/, $nameValue);
    $value =~ tr/+/ /;
    $value =~ s/%([\dA-Fa-f][\dA-Fa-f])/ pack ("C",hex ($1))/eg;
    $form{$name} = $value;
  }
}

sub writeChdkFileinfo {
  my @text = (
    ["Update", "Aktualisierung"],
    ["Complete", "Komplett"],
    ["CHDK (absent value)", "CHDK (Angabe fehlt)"],
    ["Uploaded file", "hochgeladene Datei"],
    ["Name", "Name"],
    ["Size", "Größe"],
    ["File content", "Inhalt der Datei"],
    ["Package", "Paket"],
    ["Files", "Dateien"],
    ["Informations from filename", "Informationen aus dem Dateinamen"],
    ["Type", "Typ"],
    ["Camera", "Kamera"],
    ["Version", "Version"],
    ["Revision", "Revision"]
  );
  my $package = ($fullChdk == 0)?$text[0][$langDE]:$text[1][$langDE];
  my $typ = (!$langDE)?"unknown":"unbekannt";
  my $cam = $typ;
  my $ver = $typ;
  my $rev = $typ;
  my $err = 1;
  if ($qsChdkZip =~ /^(CHDK\-DE|CHDK_DE|CHDK)?[-_]?([a-z]+\d+[a-z]*_?\w*\-\d\d\d[a-z])\-(\d+\.\d+\.\d+)\-[-_A-Za-z]*(\d+).*\.zip/) {
    if ($1) { $typ = $1 }
    if ($2) { $cam = $2 }
    if ($3) { $ver = $3 }
    if ($4) { $rev = $4 }
    if (!$1 && $2 && $3 && $4) { $typ = $text[2][$langDE] }
    $err = 0;
  }
  print "<div class=\"hint\">\n";
  if($qsChdkZipSize > 0) {
    print "<table class=\"fileinfo\">\n";
    print "<caption>$text[3][$langDE]</caption>\n";
    print "<tr><th scope=\"row\">$text[4][$langDE]:</th><td>$qsChdkZip</td></tr>\n";
    print "<tr><th scope=\"row\">$text[5][$langDE]:</th><td>$qsChdkZipSize Byte</td></tr>\n";
    print "</table>\n";
  }
  print "<table class=\"fileinfo\">\n";
  print "<caption>$text[6][$langDE]</caption>\n";
  print "<tr><th scope=\"row\">$text[7][$langDE]:</th><td>$package</td></tr>\n";
  print "<tr><th scope=\"row\">$text[8][$langDE]:</th><td>$chdkFileCount</td></tr>\n";
  print "<tr><th scope=\"row\">$text[5][$langDE]:</th><td>$chdkUPsize Byte</td></tr>\n";
  print "</table>\n";
  print "<table class=\"fileinfo\">\n";
  print "<caption>$text[9][$langDE]</caption>\n";
  print "<tr><th scope=\"row\">$text[10][$langDE]:</th><td>$typ</td></tr>\n";
  print "<tr><th scope=\"row\">$text[11][$langDE]:</th><td>$cam</td></tr>\n";
  print "<tr><th scope=\"row\">$text[12][$langDE]:</th><td>$ver</td></tr>\n";
  print "<tr><th scope=\"row\">$text[13][$langDE]:</th><td>$rev</td></tr>\n";
  print "</table>\n";
  print "</div>\n";
  return $err;
}

#POST required
if($ENV{'REQUEST_METHOD'} eq "POST") {
  read(STDIN, $queryString, $ENV{'CONTENT_LENGTH'});
  qsSplit;
}
if (length($form{fn}) > 0) {
  $qsChdkZip = $form{fn};
  $chdkZip = $srcfolder.$qsChdkZip;
}
if (length($form{fc}) > 0) { $qsChdkFileCount = $form{fc}; }
if (length($form{fs}) > 0) { $qsChdkZipSize = $form{fs}; }
if (length($form{time}) > 0) { $qsTime = $form{time}; }
if (length($form{utime}) > 0) { $updTime = $form{utime}; }
if (length($form{abort}) > 0) { $abort = $form{abort}; }

if (checkChdkZip == 0) {
   $htmlTitle = ($qsChdkFileCount == $chdkFileCount)?"$htmlTitle : 2":"$htmlTitle : 1";
}
# HTML HEADER BEGIN
print "Content-type: text/html\n\n";
print "<!DOCTYPE html>\n";
print "<html>\n";
print "<head>\n";
print "<title>$htmlTitle</title>\n";
print "<style type=\"text/css\">\n";
print "body {\n";
print "  font-family: Arial, sans-serif;\n";
print "  background-color: #004488;\n";
print "  min-width: 600px;\n";
print "  margin: 5px 0px;\n";
print "  padding: 5px;\n";
print "}\n";
print "h1 {\n";
print "  color: #ffffff;\n";
print "  font-size: 20px;\n";
print "  margin: 0px 40px;\n";
print "}\n";
print "form {\n";
print "  margin: 10px;\n";
print "}\n";
print "a {\n";
print "  color: #ffffff;\n";
print "  font-size: 11px;\n";
print "  text-decoration: none;\n";
print "}\n";
print "a:hover {\n";
print "  text-decoration: underline;\n";
print "}\n";
print "table {\n";
print "  width: 100%;\n";
print "  border: 1px dotted;\n";
print "  margin: 0px 0px 10px;\n";
print "}\n";
print "table caption{\n";
print "  background-color: #eeeeee;\n";
print "  padding: 2px 10px;\n";
print "  text-align: left;\n";
print "  text-transform: uppercase;\n";
print "}\n";
print "table th {\n";
print "  width: 100px;\n";
print "  text-align: right;\n";
print "}\n";
print ".article {\n";
print "  background-color: #ffffff;\n";
print "  margin: 10px;\n";
print "  padding: 10px;\n";
print "  padding-top: 4px;\n";
print "  font-size: 14px;\n";
print "}\n";
print ".article hr{\n";
print "  color: #000000;\n";
print "  background-color: #000000;\n";
print "  height: 1px;\n";
print "  border: 0px;\n";
print "}\n";
print ".article fieldset{\n";
print "  border: 1px solid;\n";
print "}\n";
print ".article legend{\n";
print "  font-weight: 400;\n";
print "  text-transform: uppercase;\n";
print "}\n";
print ".dir{\n";
print "  font-family: monospace;\n";
print "}\n";
print ".hint{\n";
print "  margin: 0px 14px;\n";
print "  font-size: 12px;\n";
print "}\n";
print ".footer {\n";
print "  color: #ffffff;\n";
print "  font-size: 11px;\n";
print "  margin: 3px 40px;\n";
print "  float: left;\n";
print "}\n";
print ".version {\n";
print "  color: #ffffff;\n";
print "  font-size: 11px;\n";
print "  margin: 3px 40px;\n";
print "  float: right;\n";
print "}\n";
print ".fileinput {\n";
print "  font-size: 14px;\n";
print "  width: 370px;\n";
print "  height: 26px;\n";
print "  background-color: #ffffff;\n";
print "  border: 1px dotted #004488;\n";
print "}\n";
print ".submit {\n";
print "  margin-left: 20px;\n";
print "  font-size: 14px;\n";
print "  width: 120px;\n";
print "  height: 26px;\n";
print "  background-color: #ffffff;\n";
print "  border: 1px solid #004488;\n";
print "}\n";
print ".error {\n";
print "  color: #ff0000;\n";
print "  font-weight: bold;\n";
print "  margin: 0px 20px;\n";
print "}\n";
print "</style>\n";
print "</head>\n";
print "<body>\n";
print "  <h1>$htmlTitle</h1>\n";
print "  <div class=\"article\">\n";
print "    <section>\n";
print "      <fieldset>\n";
#HTML HEADER END

if (checkChdkZip == 0) {
  if ($qsChdkFileCount == $chdkFileCount) {
    #step 2: install
    my @text = (
      ["Step 2 - Copy files", "Schritt 2 - CHDK-Dateien kopieren"],
      ["Current server time", "Aktuelle Serverzeit"],
      ["Unsafe filename!", "Unsicherer Dateiname!"],
      ["Step 2 completed", "Schritt 2 abgeschlossen"],
      ["Error on step 2", "Fehler im Schritt 2"]
    );
    print "<legend>$text[0][$langDE]</legend>\n";
    my $pi = writeChdkFileinfo;
    print "<hr>\n";
    print "<ul>\n";
    if ($updTime == 1) {
      my $lt = localtime;
      print "<li>$text[1][$langDE]: $lt</li>\n";
    }
    if ($pi) { print "<li class=\"error\" style=\"margin: 0px;\">$text[2][$langDE]</li>\n"; }
    $pi = processInstall;
    print "</ul>\n";
    print "<hr>\n";
    print "<form action=$mainhtml>\n";
    print "<span>$text[3+$pi][$langDE]</span>\n";
    print "<input type=submit value=\"OK\" class=\"submit\">\n";
    print "</form>\n";
  } else {
    #step 1: check
    my @text = (
      ["Step 1 completed", "Schritt 1 abgeschlossen"],
      ["Unsafe filename!", "Unsicherer Dateiname!"],
      ["Step 2 - Copy files", "Schritt 2 - CHDK-Dateien kopieren"],
      ["Cancel", "Abbrechen"],
      ["Next", "Weiter"]
    );
    $| = 1; #flush for print
    isSvrTime;
    print "<legend>$text[0][$langDE]</legend>";
    my $fi = writeChdkFileinfo;
    print "<hr>\n";
    print "<form name=\"_f\" action=\"/cgi-bin/chdk_install.cgi\" method=\"post\">\n";
    print "<input type=\"hidden\" name=\"fn\" value=\"$qsChdkZip\">\n";
    print "<input type=\"hidden\" name=\"fc\" value=\"$chdkFileCount\">\n";
    print "<input type=\"hidden\" name=\"utime\" value=\"$updTime\">\n";
    print "<input type=\"hidden\" name=\"abort\" value=\"0\">\n";
    if ($fi) { print "<div class=\"error\">$text[1][$langDE]</div>" }
    print "<span>$text[2][$langDE]</span>\n";
    print "<input type=\"button\" value=\"$text[3][$langDE]\" class=\"submit\" onclick=\"document.forms._f.abort.value = '1'; document.forms._f.submit()\">\n";
    print "<input type=\"submit\" value=\"$text[4][$langDE]\" class=\"submit\">\n";
    print "</form>\n";
  }
} else {
  my @text = (
    ["Error", "Fehler"],
    ["", ""]
  );
  #check error
  print "<legend>$text[0][$langDE]</legend>\n";
  print "<p  class=\"error\">$htmlCheckErr</p>\n";
  print "<ul>\n";
  deleteFile;
  print "</ul>\n";
  print "<hr>\n";
  print "<form action=$mainhtml>\n";
  print "<span>$text[1][$langDE]</span>\n";
  print "<input type=\"submit\" value=\"OK\" class=\"submit\">\n";
  print "</form>\n";
}
# HTML FOOTER BEGIN
print "      </fieldset>\n";
print "    </section>\n";
print "  </div>\n";
print "  <div class=\"footer\">(C)2014 rudi, <a target=\"_blank\" href=\"http://forum.chdk-treff.de/viewtopic.php?t=3287\">forum.chdk-treff.de</a></div>\n";
print "  <div class=\"version\">chdk_install.cgi: v1.6</div>\n";
print "</body>\n";
print "</html>\n";
# HTML FOOTER END

#! push to end of script
# webserver output fails with set date on execute cgi
# at first time after boot
setSvrTime;
