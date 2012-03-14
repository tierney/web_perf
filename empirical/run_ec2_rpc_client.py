#!/usr/bin/env python

import logging
import shlex
import subprocess
import sys
import time
import urllib2
from uuid import uuid4
import xmlrpclib

import gflags
from selenium import webdriver
from pyvirtualdisplay import Display
from Command import Command

_IFUP_PAUSE = 10
_IFDOWN_PAUSE = 2

FLAGS = gflags.FLAGS

gflags.DEFINE_string('list_host', 'theseus.news.cs.nyu.edu', 'http host with list')
gflags.DEFINE_string('list_path', '/public_dns_names.txt', 'http path to list')

gflags.DEFINE_integer('rpcport', 34344, 'RPC port to connect to',
                      short_name = 'p')
gflags.DEFINE_multistring('browsers', None, 'Browsers to use.',
                          short_name = 'b')
gflags.DEFINE_multistring('carrierifaces', None,
                          '"<carrier>,<iface>" string pair.',
                          short_name = 'c')
gflags.DEFINE_integer('timeout', 60, 'Timeout in seconds.', lower_bound=0,
                      short_name = 't')

gflags.MarkFlagAsRequired('browsers')
gflags.MarkFlagAsRequired('carrierifaces')

def prepare_interfaces(carrier):
  global _CARRIER_IFACES_MAGIC_DICT

  carriers = _CARRIER_IFACES_MAGIC_DICT.keys()
  interface = _CARRIER_IFACES_MAGIC_DICT.get(carrier)
  for carr in carriers:
    if carr == carrier:
      continue

    iface_to_down = _CARRIER_IFACES_MAGIC_DICT.get(carr)
    logging.info('ifdown-ing %s.' % iface_to_down)
    subprocess.Popen('ifconfig %s down' % iface_to_down, shell=True).wait()
    time.sleep(_IFDOWN_PAUSE)

  logging.info('ifup-ing %s.' % interface)
  subprocess.Popen('ifconfig %s up' % interface, shell=True).wait()
  time.sleep(_IFUP_PAUSE)


def client_experiment(region_host, carrier, browser):
  global _CARRIER_IFACES_MAGIC_DICT

  region, host = region_host.split(',')
  interface = _CARRIER_IFACES_MAGIC_DICT.get(carrier)
  timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')

  # Start server tcpdump
  server = xmlrpclib.ServerProxy('http://%s:%d' % (host, FLAGS.rpcport))

  uuid = str(uuid4())
  pid = server.start(timestamp, uuid, region, carrier, browser)

  # Start our tcpdump
  pcap_name = '%s_%s_%s_%s_%s.client.pcap' % \
      (timestamp, uuid, region, carrier, browser)
  tcpdump = subprocess.Popen(
    shlex.split('tcpdump -i %s -w %s' % (interface, pcap_name)))

  # Start browser
  # TODO(tierney): Currently only supports chrome and firefox.
  to_kill = None
  if browser == 'chrome': to_kill = 'chromedriver'
  elif browser == 'firefox': to_kill = '/usr/lib/firefox-10.0.2/firefox'
  command = Command(
    './BrowserRun.py --browser %s --domain %s' % (browser, host))
  command.run(timeout = FLAGS.timeout, pskill = to_kill)

  # Kill local and remote tcpdumps.
  tcpdump.terminate()
  server.stop(timestamp, uuid, region, carrier, browser, pid)

  # Zip up local tcpdump.
  subprocess.call(['bzip2', pcap_name])


def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  # Prepare interface data.
  global _CARRIER_IFACES_MAGIC_DICT
  _CARRIER_IFACES_MAGIC_DICT = {}
  for carrieriface in FLAGS.carrierifaces:
    carrier, interface = carrieriface.split(',')
    _CARRIER_IFACES_MAGIC_DICT[carrier] = interface

  # Starting fake display in which to launch browsers.
  display = Display(visible=0, size=(800, 600))
  display.start()

  # Get the regions,public_dns_names
  ec2_region_hosts = [line.strip() for line in
                      urllib2.urlopen('http://' +
                                      FLAGS.list_host +
                                      FLAGS.list_path).readlines()]

  for carrier in _CARRIER_IFACES_MAGIC_DICT:
    prepare_interfaces(carrier)

    for region_host in ec2_region_hosts:

      for i, browser in enumerate(FLAGS.browsers):
        client_experiment(region_host, carrier, browser)

      for i, browser in enumerate(FLAGS.browsers):
        client_experiment(region_host, carrier, browser)

        # if len(FLAGS.browsers) == i + 1:
        #   continue
        # WAIT = 120
        # print 'Waiting %d seconds...' % WAIT
        # time.sleep(WAIT)

  display.stop()

if __name__=='__main__':
  main(sys.argv)
