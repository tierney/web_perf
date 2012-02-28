#!/usr/bin/env python

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

logging.basicConfig(
  stream=sys.stdout, level=logging.DEBUG, filename='run_experiment.log',
  format='%(asctime)-15s %(name)-5s %(levelname)-8s %(message)s')

import gflags
from Command import Command
from LogCompressor import LogCompressor
from selenium import webdriver

_IFUP_PAUSE = 10
_IFDOWN_PAUSE = 2

FLAGS = gflags.FLAGS

gflags.DEFINE_boolean('debug', False, 'produces debugging output',
                      short_name = 'g')
gflags.DEFINE_string('note', '', 'Note for the log.')
gflags.DEFINE_string('alexa', './top-500-US.csv', 'Alexa CSV file to seed.',
                     short_name = 'a')
gflags.DEFINE_integer('timeout', 300, 'Timeout in seconds.', lower_bound=0,
                      short_name = 't')
gflags.DEFINE_string('sspath', None,
                     'Filepath of special ss', short_name = 's')
gflags.DEFINE_string('logdir',
                     time.strftime('%Y_%m_%d_%H_%M_%S',
                                   time.gmtime(time.time())),
                     'Name of logfile directory.', short_name = 'l')
gflags.DEFINE_multistring('browsers', None, 'Browsers to use.', short_name = 'b')
gflags.DEFINE_multistring('carrierifaces', None,
                          '"<carrier>,<iface>" string pair.',
                          short_name = 'c')

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

    logging.info('Starting sniffers.')
    if FLAGS.sspath:
      ss_log_name = '%s_%s_%s_%s.ss.log' % \
                     (self.carrier, self.browser, self.domain, str(time.time()))
      ss_log_path = os.path.join(FLAGS.logdir, ss_log_name)
      ss_fh = open(ss_log_path + '.tmp', 'w')
      ss_log = subprocess.Popen([FLAGS.sspath,'-g'], stdout = ss_fh)

    pcap_name = '%s_%s_%s_%s.pcap' % (self.carrier, self.browser, self.domain,
                                      str(time.time()))
    pcap_path = os.path.join(FLAGS.logdir, pcap_name)
    pcap = subprocess.Popen(
      ['tcpdump','-i','%s' % self.interface,'-w', pcap_path])
    logging.info(str(['tcpdump','-i','%s' % self.interface,'-w', pcap_path]))
    time.sleep(2)

    logging.info('Starting browser.')

    # TODO(tierney): Hacks to fix how we deal with non-terminating connections.
    to_kill = None
    if self.browser == 'chrome':
      to_kill = 'chromedriver'
    elif self.browser == 'firefox':
      to_kill = '/usr/lib/firefox-10.0.2/firefox'

    command = Command('./BrowserRun.py --browser %s --domain %s' % \
                        (self.browser, self.domain))
    command.run(timeout = FLAGS.timeout, pskill = to_kill)

    pcap.terminate()
    if FLAGS.sspath:
      ss_fh.flush()
      ss_log.terminate()
      ss_fh.flush()
      ss_fh.close()
      os.rename(ss_log_path + '.tmp', ss_log_path)
    return


class AlexaFile(object):
  def __init__(self, filepath):
    self.filepath = filepath

  def domains_desc(self):
    with open(self.filepath) as fh:
      lines = fh.readlines()
    domains = [rank_domain.strip().split(',')[1] for rank_domain in lines]
    return domains


def prepare_ifaces(carriers, carrier, interface):
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


def run_single_experiment(carrier, interface, browser, domain):
  logger = Logger(carrier, interface, browser, domain)
  logger.run()
  del(logger)

def run_carrier(domains, carriers, carrier, interface, browser_list):
  logging.info('Switching interfaces for %s.' % (carrier))
  prepare_ifaces(carriers, carrier, interface)

  # Do iface throughput check.
  timestamp = str(time.time())
  pcap_name = '%s_%s_%s_%s.pcap' % (carrier, 'NA', 'NA', timestamp)
  pcap_path = os.path.join(FLAGS.logdir, pcap_name)
  pcap = subprocess.Popen(['tcpdump', '-i', '%s' % interface, '-w', pcap_path])

  time.sleep(2)
  iperf_name = '%s_%s.iperf.log' % (timestamp, carrier)
  iperf_path = os.path.join(FLAGS.logdir, iperf_name)
  iperf_fh = open(iperf_path, 'w')
  iperf = subprocess.Popen(['iperf', '-c', 'theseus.news.cs.nyu.edu',
                            '--reverse'], stdout=iperf_fh, stderr=iperf_fh)
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
      logging.info('Running experiment for %s %s %s %s.' % \
                     (carrier, interface, browser, domain))
      run_single_experiment(carrier, interface, browser, domain)


def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  if FLAGS.note:
    logging.info(FLAGS.note)
  if FLAGS.debug:
    logging.info('non-flag arguments:', argv)

  alexa = AlexaFile(FLAGS.alexa)
  domains = alexa.domains_desc()
  to_fetch = domains
  to_fetch.reverse() # For faster list/stack pop().

  # Create log directory.
  try:
    os.mkdir(FLAGS.logdir)
  except OSError:
    logging.error('Problem with logdir name.')
    return

  log_compressor = LogCompressor(FLAGS.logdir)
  log_compressor.daemon = True
  log_compressor.start()

  carriers = []
  ifaces = []
  for carrieriface in FLAGS.carrierifaces:
    carrier, interface = carrieriface.split(',')
    carriers.append(carrier)
    ifaces.append(interface)

  while to_fetch:
    domains = [to_fetch.pop() for i in range(10)]

    for carrierinterface in FLAGS.carrierifaces:
      carrier, interface = carrierinterface.split(',')
      run_carrier(domains, carriers, carrier, interface, FLAGS.browsers)

if __name__ == '__main__':
  main(sys.argv)
