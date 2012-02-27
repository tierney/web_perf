#!/usr/bin/env python

import gflags
import httplib
import logging
import os
import re
import signal
import socket
import subprocess
import sys
import time
import threading
from Command import Command
from selenium import webdriver

_IFUP_PAUSE = 10
_IFDOWN_PAUSE = 2

_BROWSERS_MAGIC_LIST = ['android', 'chrome', 'firefox']
_CARRIER_IFACES_MAGIC_DICT = { 't-mobile' : 'usb0', # Android Phone
                               'verizon' : 'eth1',  # iPhone
                               'wireless': 'wlan0',
                               'wired' : 'eth0'
                               }

FLAGS = gflags.FLAGS

gflags.DEFINE_boolean('debug', False, 'produces debugging output',
                      short_name = 'g')
gflags.DEFINE_string('note', '', 'Note for the log.')
gflags.DEFINE_string('alexa', 'top-500-US.csv', 'Alexa CSV file to seed.',
                     short_name = 'a')
gflags.DEFINE_integer('timeout', 300, 'Timeout in seconds.', lower_bound=0,
                      short_name = 't')
gflags.DEFINE_string('debuglog', 'experiment.log',
                     'Filename for experiment log.', short_name = 'd')
gflags.DEFINE_string('logdir', None, 'Name of logfile directory.',
                     short_name = 'l')
gflags.DEFINE_multistring('browsers', None, 'Browsers to use.', short_name = 'b')
gflags.DEFINE_multistring('carrierifaces', None,
                          '"<carrier>,<iface>" string pair.',
                          short_name = 'c')

# TODO(tierney): These validators should be made more flexible, if not removed.

def validate_browsers(browsers):
  for browser in browers:
    if browser not in _BROWSERS_MAGIC_LIST:
      return False
  return True

def validate_carrierifaces(carrierifaces):
  for carrieriface in carrierifaces:
    try:
      carrier, iface = carrierifaces.split(',')
    except ValueError:
      return False

    if carrier not in _CARRIER_IFACES_MAGIC_DICT:
      return False

    expected_iface = _CARRIER_IFACES_MAGIC_DICT.get(carrier)
    if iface is not expected_iface:
      return False

gflags.RegisterValidator('browsers', validate_browsers,
                         message = 'Unknown browser.', flag_values=FLAGS)
gflags.RegisterValidator('carrierifaces', validate_carrierifaces,
                         message = 'Unknown "<carrier>,<iface>" pair',
                         flag_values=FLAGS)


class Logger(object):
  def __init__(self, carrier, interface, browser, domain):
    self.carrier = carrier
    self.interface = interface
    self.browser = browser
    self.domain = domain


  def kill_tcp_processes(self):
    ss = subprocess.Popen('ss -iepm', shell=True, stdout=subprocess.PIPE)
    lines = [line.strip() for line in ss.stdout.readlines()
             if 'emulator-arm' not in line and 'adb' not in line]
    for line in lines:
      m = re.search('users:(\(.*\))', line)
      if m:
        logging.info('To kill: %s.' % line)
        pid = int(m.groups()[0].split(',')[1])
        try:
          os.kill(pid, signal.SIGKILL)
        except OSError:
          logging.error('pid already killed: %s' % line)


  def run(self):
    logging.info('Kill old sessions.')
    self.kill_tcp_processes()

    logging.info('Starting sniffer.')
    ss_log_name = '%s_%s_%s_%s.ss.log' % \
                   (self.carrier, self.browser, self.domain, str(time.time()))
    ss_fh = open(ss_log_name + '.tmp', 'w')
    ss_log = subprocess.Popen(['/home/tierney/repos/fss/src/ss','-g'],
                              stdout = ss_fh)

    pcap = subprocess.Popen(
      ['tcpdump','-i','%s' % _IFACES[self.carrier],'-w',
       '%s_%s_%s_%s.pcap' % (self.carrier, self.browser, self.domain,
                             str(time.time()))])
    time.sleep(2)

    logging.info('Starting browser.')

    # TODO(tierney): Hacks to fix how we deal with non-terminating connections.
    to_kill = None
    if self.browser == 'chrome':
      to_kill = 'chromedriver'
    elif self.browser == 'firefox':
      to_kill = 'firefox'

    command = Command('./BrowserRun.py --browser %s --domain %s' % \
                        (self.browser, self.domain))
    command.run(timeout = FLAGS.timeout, pskill = to_kill)

    pcap.terminate()
    ss_fh.flush()
    ss_log.terminate()
    ss_fh.flush()
    ss_fh.close()
    os.rename(ss_log_name + '.tmp', ss_log_name)
    return


class AlexaFile(object):
  def __init__(self, filepath):
    self.filepath = filepath

  def domains_desc(self):
    with open(self.filepath) as fh:
      lines = fh.readlines()
    domains = [rank_domain.strip().split(',')[1] for rank_domain in lines]
    return domains


def prepare_ifaces(carrier):
  for carr in _IFACES.keys():
    if carr == carrier:
      continue
    subprocess.Popen('ifconfig %s down' % _IFACES[carr], shell=True).wait()
    time.sleep(_IFDOWN_PAUSE)

  subprocess.Popen('ifconfig %s up' % _IFACES[carrier], shell=True).wait()
  time.sleep(_IFUP_PAUSE)


def run_single_experiment(carrier, interface, browser, domain):
  logger = Logger(carrier, interface, browser, domain)
  logger.run()
  del(logger)

def run_carrier(domains, carrier, interface, browser_list):
  logging.info('Switching interfaces for %s.' % (carrier))
  prepare_ifaces(carrier)

  # Do iface throughput check.
  timestamp = str(time.time())
  pcap = subprocess.Popen(
    ['tcpdump','-i','%s' % interface,'-w',
     '%s_%s_%s_%s.pcap' % (carrier, 'NA', 'NA', timestamp)])

  time.sleep(2)
  iperf_fh = open('%s_%s.iperf.log' % (timestamp, carrier), 'w')
  iperf = subprocess.Popen(['iperf', '-c', 'theseus.news.cs.nyu.edu',
                            '--reverse'],
                           stdout=iperf_fh, stderr=iperf_fh)
  time.sleep(50)
  # iperf.wait()
  iperf.terminate()
  iperf_fh.flush()
  iperf_fh.close()
  pcap.terminate()

  # Run through the domains.
  for domain in domains:
    logging.info('Domain: %s.' % (domain))
    for browser in browser_list:
      run_single_experiment(carrier, interface, browser, domain)


def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  logging.basicConfig(stream=sys.stdout, filename=FLAGS.debuglog,
                      level=logging.INFO)

  if FLAGS.note:
    logging.info(FLAGS.note)
  if FLAGS.debug:
    logging.info('non-flag arguments:', argv)

  alexa = AlexaFile('./top-500-US.csv')
  domains = alexa.domains_desc()
  to_fetch = domains
  to_fetch.reverse() # For faster list/stack pop().

  while to_fetch:
    domains = [to_fetch.pop() for i in range(10)]

    for carrierinterface in FLAGS.carrierifaces:
      carrier, interface = carrierifaces.split(',')
      run_carrier(domains, carrier, interface, FLAGS.browsers)

if __name__ == '__main__':
  main(sys.argv)
