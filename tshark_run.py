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
_IFACES = { 't-mobile' : 'usb0',
            'verizon' : 'usb1' }

_BROWSER = {
  'chrome' : webdriver.Chrome(),
  'firefox' : webdriver.Firefox(),
  'android' : webdriver.Remote("http://localhost:8080/wd/hub",
                               webdriver.DesiredCapabilities.ANDROID)}


class Logger(object):
  def __init__(self, carrier, browser, domain):
    self.carrier = carrier
    self.browser = browser
    self.domain = domain

  def run(self):
    print 'Starting sniffer.'
    pcap = subprocess.Popen(
      ['tcpdump','-i','%s' % _IFACES[self.carrier],'-w',
       '%s_%s_%s_%s.pcap' % (self.carrier, self.browser, self.domain,
                             str(time.time()))])

    print 'Starting browser.'
    browser = _BROWSER[self.browser]
    browser.get('http://' + self.domain) # Executes until "loaded."
    browser.close()

    pcap.terminate()


def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    print '%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS)
    sys.exit(1)
  if FLAGS.debug:
    print 'non-flag arguments:', argv

  l = Logger('t-mobile', 'chrome', 'cnn.com')
  l.run()

if __name__ == '__main__':
  main(sys.argv)
