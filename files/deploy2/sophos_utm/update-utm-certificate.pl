#!/usr/bin/perl

# MIT License
# Copyright (c) 2016 Moritz Bunkus m.bunkus@linet-services.de
# https://github.com/mbunkus/utm-update-certificate

use warnings;
use strict;

use Astaro::ConfdPlRPC;
use Data::Dumper;
use IO::File;
use POSIX qw(strftime);

$ENV{LC_ALL} = 'C';
$ENV{LANG}   = 'C';

$Data::Dumper::Sortkeys = 1;
$Data::Dumper::Indent   = 2;

my (%changes, %files_by_object);

sub read_file {
  my ($file_name) = @_;

  my $file = IO::File->new($file_name, "r") || die "Could not read ${file_name}.\n";

  local $/;
  my $content = <$file>;
  $file->close;

  return $content;
}

sub update_field {
  my ($obj, $data_key, $new_value) = @_;

  return if (ref($obj->{data}->{$data_key}) eq 'ARRAY') && join("\n", @{ $obj->{data}->{$data_key} }) eq join("\n", @{ $new_value });
  return if !ref($obj->{data}->{$data_key})             && $obj->{data}->{$data_key}                  eq $new_value;

  $obj->{data}->{$data_key} = $new_value;

  $changes{$obj} ||= { object => $obj, fields => [] };
  push @{ $changes{$obj}->{fields} }, $data_key;
}

sub update_certificate {
  my ($sys, $ref, $cert_file_name, $key_file_name) = @_;

  my $obj            = $sys->get_object($ref)                 || die "Unknown object $ref\n";
  my $meta_obj       = $sys->get_object($obj->{data}->{meta}) || die "Meta object not found for $ref\n";

  my $cert_info      = `openssl x509 -in ${cert_file_name} -noout -text`;
  my ($not_before)   = $cert_info =~ m{not *before *: *([^\n]+)}i;
  my ($not_after)    = $cert_info =~ m{not *after *: *([^\n]+)}i;
  my ($issuer)       = $cert_info =~ m{issuer: *([^\n]+)}i;
  my ($subject)      = $cert_info =~ m{subject: *([^\n]+)}i;
  my ($serial)       = $cert_info =~ m{serial *number *: *\d+ *\(0x([0-9a-f]+)}i;
  ($serial)          = $cert_info =~ m{serial *number *: *\n *([0-9a-f:]+)}i if !defined $serial;
  my ($pub_key_algo) = $cert_info =~ m{public *key *algorithm *: *([^\n]+)}i;
  my ($sub_alt_name) = $cert_info =~ m{X509v3 *Subject *Alternative *Name *: *\n *([^\n]+)}i;
  my @sub_alt_names  = $sub_alt_name  ? split(m{, *}, $sub_alt_name) : ();
  my $vpn_id         = @sub_alt_names ? $sub_alt_names[0]            : $subject;
  my $vpn_id_type    = @sub_alt_names ? 'fqdn'                       : 'der_asn1_dn';

  my $issuer_hash    = `openssl x509 -issuer_hash  -in ${cert_file_name} -noout`;
  my $subject_hash   = `openssl x509 -subject_hash -in ${cert_file_name} -noout`;
  my $fingerprint    = `openssl x509 -fingerprint  -in ${cert_file_name} -noout`;

  $issuer            =~ s{/}{, }g;
  $subject           =~ s{/}{, }g;
  $issuer_hash       =~ s{\n}{};
  $subject_hash      =~ s{\n}{};
  $fingerprint       =~ s{.*=|\n}{}g;
  $serial            =~ s{:}{}g;

  $serial            = "0${serial}" if length($serial) % 2;
  $serial            = uc $serial;

  update_field($obj,      'certificate',          read_file($cert_file_name));
  update_field($obj,      'key',                  read_file($key_file_name)) if $key_file_name;

  update_field($meta_obj, 'enddate',              $not_after);
  update_field($meta_obj, 'fingerprint',          $fingerprint);
  update_field($meta_obj, 'issuer',               $issuer);
  update_field($meta_obj, 'issuer_hash',          $issuer_hash);
  update_field($meta_obj, 'name',                 $subject);
  update_field($meta_obj, 'public_key_algorithm', $pub_key_algo);
  update_field($meta_obj, 'serial',               $serial);
  update_field($meta_obj, 'startdate',            $not_before);
  update_field($meta_obj, 'subject',              $subject);
  update_field($meta_obj, 'subject_alt_names',    \@sub_alt_names);
  update_field($meta_obj, 'subject_hash',         $subject_hash);
  update_field($meta_obj, 'vpn_id',               $vpn_id);
  update_field($meta_obj, 'vpn_id_type',          $vpn_id_type);

  $files_by_object{$obj} = [ $cert_file_name ];
  push @{ $files_by_object{$obj} }, $key_file_name if $key_file_name;
}

sub main {
  my ($ref, $cert_file_name, $key_file_name, $intermediate_ref, $intermediate_file_name) = @ARGV;

  if (   !$ref
      || !$cert_file_name
      || !$key_file_name
      || ($ref !~ m{^REF_})
      || (   $intermediate_ref
          && (   ($intermediate_ref !~ m{^REF_})
              || !$intermediate_file_name))) {
    die "usage: $0 ref cert-file-name key-file-name [intermediate-ref intermediate-file-name]\n";
  }

  my $sys = Astaro::ConfdPlRPC->new || die "Login failed.\n";
  $sys->lock                        || die "Locking failed.\n";

  update_certificate($sys, $ref,              $cert_file_name, $key_file_name);
  update_certificate($sys, $intermediate_ref, $intermediate_file_name) if $intermediate_ref;

  my $now = strftime('auto-updated on %Y-%m-%d %H:%M:%S', localtime());

  foreach my $current_obj (map { $_->{object} } values %changes) {
    update_field($current_obj, 'comment', $now);
    die Dumper($sys->err_list) unless $sys->set_object($current_obj);
  }

  $sys->commit if %changes;
  # $sys->rollback;
  $sys->disconnect;

  if (%changes) {
    print "UPDATE: certficates have been updated: " . join(' ', sort { lc $a cmp lc $b } map { @{ $files_by_object{$_} // [] } } keys %changes) . "\n";
  } else {
    print "OK: certificates are already up to date.\n";
  }
}

main();
