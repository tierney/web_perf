#!/usr/bin/env python

import logging
import shlex
import subprocess
import sys
import time
import urllib2
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

gflags.DEFINE_multistring('region_hosts', None, '<region>,<hosts> list',
                          short_name = 'r')
gflags.DEFINE_integer('num_site_trials', 1, 'number of trials per site',
                      short_name = 'n')
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
    subprocess.call(shlex.split('ifconfig %s down' % iface_to_down))
    time.sleep(_IFDOWN_PAUSE)

  logging.info('ifup-ing %s.' % interface)
  subprocess.call(
    shlex.split('ifconfig %s up' % interface))
  if 'delay' == carrier:
    subprocess.call(
      shlex.split('tc qdisc add dev %s root netem delay 100ms' % interface))
  elif 'eth0' == carrier:
    subprocess.call(
      shlex.split('tc qdisc del dev %s root netem delay 100ms' % interface))

  time.sleep(_IFUP_PAUSE)


def client_experiment(region, host, carrier, browser, protocol, port,
                      do_traceroute, port80explicit=False, pipelining=0):
  global _CARRIER_IFACES_MAGIC_DICT

  port = str(port)
  interface = _CARRIER_IFACES_MAGIC_DICT.get(carrier)
  timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')

  # Start server tcpdump
  server = xmlrpclib.ServerProxy('http://%s:%d' % (host, FLAGS.rpcport))

  logging.info('Calling .start() at http://%s:%d %s.' % \
                 (host, FLAGS.rpcport, '_'.join([timestamp, region,
                                                 carrier, browser, port])))
  pid = server.start(timestamp, region, carrier, browser, pipelining, port)
  logging.info('Started on server with PID %d.' % pid)

  # Start our tcpdump
  pcap_name = '%s_%s_%s_%s_%s_%s.client.pcap' % \
      (timestamp, region, carrier, browser, pipelining, port)
  tcpdump = subprocess.Popen(
    shlex.split('tcpdump -i %s -w %s' % (interface, pcap_name)),
    stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  # Start browser
  # TODO(tierney): Currently only supports chrome and firefox.
  to_kill = None
  if browser == 'chrome':
    to_kill = 'chromedriver'
  elif browser == 'firefox':
    to_kill = '/usr/lib/firefox-10.0.2/firefox'

  if port == '80' and not port80explicit:
    browser_command = './BrowserRun.py --browser %s --domain %s --pipelining %d' % \
        (browser, protocol + '://' + host, pipelining)
  else:
    browser_command = './BrowserRun.py --browser %s --domain %s --pipelining %d' % \
        (browser, protocol + '://' + host + ':' + str(port), pipelining)

  logging.info('Starting browser %s.' % browser)
  command = Command(browser_command)
  command.run(timeout = FLAGS.timeout, pskill = to_kill)

  # Kill local and remote tcpdumps.
  tcpdump.terminate()
  proxy_ips = server.stop(
    timestamp, region, carrier, browser, pipelining, port, pid, do_traceroute)
  logging.info('Proxies: %s.' % ', '.join(proxy_ips))

  # Traceroute measurement.
  if do_traceroute:
    for proxy_ip in proxy_ips:
      logging.info('Tracerouting %s.' % proxy_ip)
      tr_file = '%s_%s_%s_%s_%s_%s.client.traceroute' % \
          (timestamp, region, carrier, browser, port, proxy_ip)
      with open(tr_file, 'w') as tr_fh:
        subprocess.Popen('traceroute %s' % (proxy_ip),
                         shell=True, stdout=tr_fh).wait()

    logging.info('Tracerouting %s.' % host)
    tr_file = '%s_%s_%s_%s_%s_%s.client.traceroute' % \
        (timestamp, region, carrier, browser, port, host)
    with open(tr_file, 'w') as tr_fh:
      subprocess.Popen('traceroute %s -m 50' % (host),
                       shell=True, stdout=tr_fh).wait()

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
  if not FLAGS.region_hosts:
    ec2_region_hosts = [line.strip() for line in
                        urllib2.urlopen('http://' +
                                        FLAGS.list_host +
                                        FLAGS.list_path).readlines()]
  else:
    ec2_region_hosts = FLAGS.region_hosts

  # Map a browser setting to a host.
  # e.g., ('browser', 'setting0', 'setting1',...) -> host
  browser_setting_host = [
    ('firefox', 0),
    ('firefox', 8),
    ('firefox', 16),
    ('firefox', 32),
    ('chrome', 0),
    ('chrome', 1),
    ]

  ec2_region_browser_host = {}
  ec2_region_hosts_temp = {}
  for ec2_region_host in ec2_region_hosts:
    region, host = ec2_region_host.split(',')
    if region not in ec2_region_hosts_temp:
      ec2_region_hosts_temp[region] = []
    ec2_region_hosts_temp[region].append(host)

  for region in ec2_region_hosts_temp:
    if region not in ec2_region_browser_host:
      ec2_region_browser_host[region] = {}

    for i, host in enumerate(ec2_region_hosts_temp.get(region)):
      ec2_region_browser_host[region][browser_setting_host[i]] = host

  for carrier in _CARRIER_IFACES_MAGIC_DICT:
    prepare_interfaces(carrier)
    for region in ec2_region_browser_host:
      for browser, http_pipelining in ec2_region_browser_host.get(region):
        host = ec2_region_browser_host.get(region).get((browser, http_pipelining))

        for i in range(FLAGS.num_site_trials):
          client_experiment(region, host, carrier, browser, 'http', 80, str(0==i),
                            pipelining = http_pipelining)
        for i in range(FLAGS.num_site_trials):
          client_experiment(region, host, carrier, browser, 'https', 443, False,
                            pipelining = http_pipelining)
        for i in range(FLAGS.num_site_trials):
          client_experiment(region, host, carrier, browser, 'http', 34343, False,
                            pipelining = http_pipelining)

  display.stop()

if __name__=='__main__':
  main(sys.argv)
