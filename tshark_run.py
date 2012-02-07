#!/usr/bin/env python

import gflags
import subprocess
import sys
import time
import threading
from selenium import webdriver

FLAGS = gflags.FLAGS

# gflags.DEFINE_string()
# gflags.DEFINE_boolean()
# gflags.DEFINE_integer()
gflags.DEFINE_boolean('debug', False, 'produces debugging output')

# gflags.RegisterValidator()

_TIMEOUT = 30 # seconds.
_IFACES = { 't-mobile' : 'usb0', # Android
            'verizon' : 'eth1'   # iPhone
            }


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

  def run(self):
    print 'Starting sniffer.'
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


class AlexaFile(object):
  def __init__(self, filepath):
    self.filepath = filepath

  def domains_desc(self):
    with open(self.filepath) as fh:
      lines = fh.readlines()
    domains = [rank_domain.strip().split(',')[1] for rank_domain in lines]
    return domains


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
  to_fetch = domains[:500]

  while to_fetch:
    domains = [to_fetch.pop(0) for i in range(10)]

    # t-mobile Measurement.
    print 'Switching interfaces for t-mobile.'
    subprocess.Popen('ifconfig eth1 down', shell=True).wait()
    time.sleep(1)
    subprocess.Popen('ifconfig usb0 up', shell=True).wait()
    time.sleep(6)
    for domain in domains:
      Logger('t-mobile', 'android', domain).run()
      Logger('t-mobile', 'chrome', domain).run()
      Logger('t-mobile', 'firefox', domain).run()

    # verizon Measurement.
    print 'Switching interfaces for verizon.'
    subprocess.Popen('ifconfig usb0 down', shell=True).wait()
    time.sleep(1)
    subprocess.Popen('ifconfig eth1 up', shell=True).wait()
    time.sleep(6)
    for domain in domains:
      Logger('verizon', 'android', domain).run()
      Logger('verizon', 'chrome', domain).run()
      Logger('verizon', 'firefox', domain).run()

if __name__ == '__main__':
  main(sys.argv)
