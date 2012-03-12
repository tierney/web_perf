#!/usr/bin/env python

import shlex
import subprocess
import sys
from uuid import uuid4
import xmlrpclib

from selenium import webdriver
import gflags
FLAGS = gflags.FLAGS

gflags.DEFINE_multistring('ec2_region_hosts', None,
                          'EC2 <region,hosts> to connect to', short_name = 'h')
gflags.DEFINE_integer('rpcport', 34344, 'RPC port to connect to',
                      short_name = 'p')

gflags.MarkFlagAsRequired('ec2_region_hosts')


def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  for region_host in FLAGS.ec2_region_hosts:
    region, host = region_host.split(',')

    # Start server tcpdump
    server = xmlrpclib.ServerProxy('http://%s:%d' % (host, FLAGS.rpcport))
    uuid = str(uuid4())
    pid = server.start(region, uuid)

    # Start our tcpdump
    network = 'wired'
    browser = 'chrome'
    pcap_name = '%s_%s_%s_%s.client.pcap' % (uuid, region, network, browser)
    tcpdump = subprocess.Popen(shlex.split('tcpdump -i eth1 -w %s' % pcap_name))

    # Start browser
    driver = webdriver.Chrome()
    driver.get('http://%s' % host)
    driver.quit()

    # Kill local and remote tcpdumps.
    tcpdump.terminate()
    server.stop(region, uuid, pid)

    subprocess.call(['bzip2', pcap_name])
    copy = subprocess.Popen(shlex.split(
        'scp ubuntu@%s:/%s_%s.server.pcap.bz2 .' % (host, uuid, region)))
    copy.wait()


if __name__=='__main__':
  main(sys.argv)
