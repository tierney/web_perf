#!/usr/bin/env python

import shlex
import subprocess
import sys
import urllib2

import gflags
FLAGS = gflags.FLAGS

gflags.DEFINE_string('list_host', 'theseus.news.cs.nyu.edu', 'http host with list')
gflags.DEFINE_string('list_path', '/public_dns_names.txt', 'http path to list')

def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  ec2_region_hosts = [line.strip() for line in
                      urllib2.urlopen('http://' +
                                      FLAGS.list_host +
                                      FLAGS.list_path).readlines()]

  for region_host in ec2_region_hosts:
    region, host = region_host.split(',')

    subprocess.call(shlex.split(
        'scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no ' \
          'ubuntu@%s:/*.server.pcap.bz2 .' % (host)))

    subprocess.call(shlex.split(
        'scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no ' \
          'ubuntu@%s:/*.server.traceroute .' % (host)))

    subprocess.call(shlex.split(
        'ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no ' \
          'ubuntu@%s sudo rm -f /*.server.pcap.bz2 /*.server.traceroute' \
          % (host)))


if __name__=='__main__':
  main(sys.argv)
