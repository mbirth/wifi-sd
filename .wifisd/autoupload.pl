#!/usr/bin/perl
# Custom Upload script for a Transcend Wi-Fi SD Card
# Copyright (C) Glen Pitt-Pladdy 2014
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
#
# See: https://www.pitt-pladdy.com/blog/_20140202-083815_0000_Transcend_Wi-Fi_SD_Hacks_CF_adaptor_telnet_custom_upload_/
#

use strict;
use warnings;

# delay between itterations
my $LOOPDELAY = 5;

# path to mirror
my $PATH = '/mnt/sd/DCIM';
my $PATHLENGTH = length $PATH;
my $FINDCMD = "find $PATH -type f";

# curl command and URL to send to
my $CURL = 'curl --user-agent \'WiFISD Uploader\' --cacert /mnt/sd/.wifisd/ca/SomeRootCert.pem --user user:pass';
my $URL = 'https://upload.somedomain.com/tscardupload/';



# keep track of files already sent
my %DONEFILES;

# find files available to upload
sub findfiles {
	my ( $files ) = @_;
	open my $find, '-|', $FINDCMD or die "FATAL - can't run find: $!\n";
	while ( defined ( my $line = <$find> ) ) {
		chomp $line;
		substr ( $line, 0, $PATHLENGTH, '' );
		$line =~ s/^\/+//;
		push @$files, $line;
	}
	close $find;
}

# verify file is uploaded
sub checkfile {
	my ( $file ) = @_;
	my $fileesc = $file;
	$fileesc =~ s/\\/\\\\/g;
	$fileesc =~ s/`/\\`/g;
	$fileesc =~ s/\$/\\\$/g;
	$fileesc =~ s/"/\\"/g;
	my $fullpath = "$PATH/$file";
	open my $curl, '-|', "$CURL --silent --form time=".(stat $fullpath)[9]." --form size=".(-s $fullpath)." --form verifypath=\"$fileesc\" $URL"
		or return 0;
	my $result = <$curl>;
	if ( ! defined($result) ) { return 0; }
	chomp $result;
	close $curl;
	if ( $result eq 'OK' ) {
		return 1;
	}
	return 0;
}

# upload a file
sub upload {
	my ( $file ) = @_;
	my $fullpath = "$PATH/$file";
	my $fullpathesc = $fullpath;
	$fullpathesc =~ s/\\/\\\\/g;
	$fullpathesc =~ s/`/\\`/g;
	$fullpathesc =~ s/\$/\\\$/g;
	$fullpathesc =~ s/"/\\"/g;
	my $fileesc = $file;
	$fileesc =~ s/\\/\\\\/g;
	$fileesc =~ s/`/\\`/g;
	$fileesc =~ s/\$/\\\$/g;
	$fileesc =~ s/"/\\"/g;
	my $start = time();
	system ( "$CURL --form time=".(stat $fullpath)[9]." --form size=".(-s $fullpath)." --form filepath=\"$fileesc\" --form uploadfile=\"\@$fullpathesc;type=application/octet-stream\" $URL" );
	my $elapsed = time() - $start;
	if ( $elapsed == 0 ) { return; }
	my $rate = (-s $fullpath) / $elapsed;
	print "$rate B/s\n";
}


# signal handler - exit cleanly
my $run = 1;
sub exitclean {
	warn "got signal - exiting\n";
	$run = 0;
}

# signal handler - doesn't seem to work TODO
$SIG{'TERM'} = 'exitclean';
$SIG{'QUIT'} = 'exitclean';
$SIG{'INT'} = 'exitclean';
$SIG{'HUP'} = 'exitclean';

# wait for crypto lib available
while ( ! -f '/mnt/mtd/libcrypto.so.0.9.8.bz2' ) { sleep 1; }

# do initial scan of all files
my @files;
system ( 'sh /usr/bin/refresh_sd' );
findfiles ( \@files );
foreach my $file (@files) {
	if ( checkfile ( $file ) ) {
		$DONEFILES{$file} = 1;
	}
}

# loop checking files
while ( $run ) {
	# get file list
	undef @files;
	system ( 'sh /usr/bin/refresh_sd' );
	findfiles ( \@files );
	foreach my $file (@files) {
		if ( $DONEFILES{$file} ) { next; }
		upload ( $file );
		if ( checkfile ( $file ) ) {
			$DONEFILES{$file} = 1;
		}
	}
	# clean removed files
	foreach my $file (keys %DONEFILES) {
		if ( ! -f "$PATH/$file" ) {
			delete $DONEFILES{$file};
		}
	}
	# delay before next try
	sleep $LOOPDELAY;
}




