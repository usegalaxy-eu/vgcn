#! /usr/bin/perl

# based on:
# https://aweirdimagination.net/2015/02/28/better-hash-based-colors/

use feature 'say';
use strict;
use open qw(:utf8);
use utf8;
use warnings;

use File::Basename 'basename';
use Digest::SHA 'sha256_hex';
use Getopt::Long;
use bignum;


sub colorize {
    my ($bg, $color, $str) = @_;

    my $color_bg = ($color + 15) % 255;
    my $out = $bg ? "\033[48;5;${color_bg}m" : '';

    return $out . "\033[38;5;${color}m${str}\033[0m";
}


sub usage {
    my ($nr) = shift // 0;

    say "usage: ${\basename $0} [-b|--background] <-|file_path>";
    exit $nr;
}


my $background = 0;
my $help = 0;
GetOptions(
    "background|b" => \$background,
    "help|h" => \$help,
) or usage 1;

usage if $help;

while (<>) {
    chomp;

    my $hash = sha256_hex($_);
    my $num = hex(substr($hash, 0, 2));

    say colorize $background, $num, $_;
}
