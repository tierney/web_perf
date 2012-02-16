#!/usr/bin/env python

import gflags
import os
import re
import signal
import subprocess
import sys
import time
import threading
from selenium import webdriver

FLAGS = gflags.FLAGS

gflags.DEFINE_boolean('debug', False, 'produces debugging output')

_TIMEOUT = 30 # seconds.
# _IFACES = { 't-mobile' : 'usb0', # Android
#             'verizon' : 'eth1',  # iPhone
#             'wired' : 'eth0'
#             }
_IFACES = { 'wifi' : 'wlan0', # Android
            }

_IFUP_PAUSE = 10
_IFDOWN_PAUSE = 2

class Logger(object):
  def __init__(self, carrier, browser, domain):
    self.carrier = carrier
    self.browser = browser
    self.domain = domain

  def _browser(self, name):
    if 'chrome' == name:
      return webdriver.Chrome()
    elif 'firefox' == name:
      return webdriver.Firefox()
    elif 'android' == name:
      return webdriver.Remote("http://localhost:8080/wd/hub",
                              webdriver.DesiredCapabilities.ANDROID)

  def kill_tcp_processes(self):
    ss = subprocess.Popen('ss -iepm', shell=True, stdout=subprocess.PIPE)
    lines = [line.strip() for line in ss.stdout.readlines()]
    for line in lines:
      m = re.search('users:(\(.*\))', line)
      if m:
        pid = int(m.groups()[0].split(',')[1])
        os.kill(pid, signal.SIGKILL)

  def run(self):
    print 'Kill old sessions.'
    self.kill_top_processes()

    print 'Starting sniffer.'
    ss_log = subprocess.Popen(
      '/home/tierney/repos/fss/src/ss -g > %s_%s_%s_%s.pcap' % \
        (self.carrier, self.browser, self.domain, str(time.time())), shell=True)

    pcap = subprocess.Popen(
      ['tcpdump','-i','%s' % _IFACES[self.carrier],'-w',
       '%s_%s_%s_%s.pcap' % (self.carrier, self.browser, self.domain,
                             str(time.time()))])
    time.sleep(2)

    print 'Starting browser.'
    browser = self._browser(self.browser)
    browser.get('http://' + self.domain) # Executes until "loaded."
    print 'Closing page.'
    browser.close()

    print 'Letting residual packets arrive and ending sniff session.'
    time.sleep(3)

    pcap.terminate()
    ss_log.terminate()


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


def run_carrier(carrier, browser_list):
  print 'Switching interfaces for t-mobile.'
  prepare_ifaces(carrier)
  for domain in domains:
    for browser in browser_list:
      Logger(carrier, browser, domain).run()


def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    print '%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS)
    sys.exit(1)
  if FLAGS.debug:
    print 'non-flag arguments:', argv

  alexa = AlexaFile('./top-1m.csv')
  domains = alexa.domains_desc()
  to_fetch = domains[:3]

  browser_list = ['android', 'chrome', 'firefox']
  carrier_list = _IFACES.keys()
  while to_fetch:
    domains = [to_fetch.pop(0) for i in range(10)]

    for carrier in carrier_list:
      run_carrier(carrier, browser_list)

if __name__ == '__main__':
  main(sys.argv)
