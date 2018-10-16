#! /usr/bin/perl

use strict;
use open qw(:utf8);
use utf8;
use warnings;

use POSIX 'strftime';


$|++;

print strftime('%Y-%m-%d %H:%M:%S ', localtime) . $_ while <>;
