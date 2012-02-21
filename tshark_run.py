#!/usr/bin/env python

# $./adb -s <serialId> shell am start -a android.intent.action.MAIN -n org.openqa.selenium.android.app/.MainActivity
# You can start the application in debug mode, which has more verbose logs by doing:

# $./adb -s <serialId> shell am start -a android.intent.action.MAIN -n org.openqa.selenium.android.app/.MainActivity -e debug true
# Now we need to setup the port forwarding in order to forward traffic from the host machine to the emulator. In a terminal type:

# $./adb -s <serialId> forward tcp:8080 tcp:8080
# This will make the android server available at http://localhost:8080/wd/hub from the host machine. You're now ready to run the tests. Let's take a look at some code.

import gflags
import logging
import os
import re
import signal
import socket
import subprocess
import sys
import time
import threading
from selenium import webdriver

FLAGS = gflags.FLAGS

gflags.DEFINE_boolean('debug', False, 'produces debugging output')
gflags.DEFINE_string('note', '', 'Note for the log.')

logging.basicConfig(stream=sys.stdout, filename='tshark_run.log',
                    level=logging.INFO)
logging.info(FLAGS.note)

_TIMEOUT = 30 # seconds.

_IFACES = { 't-mobile' : 'usb0', # Android Phone
            'verizon' : 'eth1',  # iPhone
            # 'wireless': 'wlan0',
            'wired' : 'eth0'
            }

_BROWSERS = [
  # 'android',
  'chrome',
  'firefox'
  ]

_IFUP_PAUSE = 10
_IFDOWN_PAUSE = 2

class Logger(object):
  def __init__(self, carrier, browser, domain):
    self.carrier = carrier
    self.browser = browser
    self.domain = domain

  def _browser(self, name):
    browser_driver = None
    try:
      if 'chrome' == name:
        browser_driver = webdriver.Chrome()
      elif 'firefox' == name:
        browser_driver = webdriver.Firefox()
      elif 'android' == name:
        # Restart the android selenium app before trying to call into it.
        subprocess.call(
          ['/home/tierney/repos/android/android-sdk-linux/platform-tools/adb',
           '-s','emulator-5554','shell','am','start','-S','-a',
           'android.intent.action.MAIN','-n',
           'org.openqa.selenium.android.app/.MainActivity'])
        time.sleep(2)
        subprocess.call(['/home/tierney/repos/android/android-sdk-linux/platform-tools/adb',
                         '-s','emulator-5554','forward','tcp:8080','tcp:8080'])
        time.sleep(2)
        browser_driver = webdriver.Remote("http://localhost:8080/wd/hub",
                                webdriver.DesiredCapabilities.ANDROID)
    except socket.error, e:
      logging.error("webdriver connection error (%s): %s." % (name, str(e)))
    except Exception, e:
      logging.error("webdriver error (%s): %s." % (name, str(e)))
    return browser_driver

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
    browser = None
    attempts = 0
    while not browser:
      if attempts >= 3:
        logging.error("ERROR with %s, %s, %s." % (self.carrier, self.browser, self.domain))
        return
      attempts += 1
      browser = self._browser(self.browser)

    browser.get('http://' + self.domain) # Executes until "loaded."
    logging.info('Quit browser and all windows.')
    browser.quit()

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


def run_single_experiment(carrier, browser, domain):
  logger = Logger(carrier, browser, domain)
  logger.run()


def run_carrier(domains, carrier, browser_list):
  logging.info('Switching interfaces for %s.' % (carrier))
  prepare_ifaces(carrier)
  for domain in domains:
    logging.info('Domain: %s.' % (domain))
    for browser in browser_list:
      run_single_experiment(carrier, browser, domain)


def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)
  if FLAGS.debug:
    logging.info('non-flag arguments:', argv)

  alexa = AlexaFile('./top-500-US.csv')
  domains = alexa.domains_desc()
  to_fetch = domains
  to_fetch.reverse() # For faster list/stack pop().

  carrier_list = _IFACES.keys()
  while to_fetch:
    domains = [to_fetch.pop() for i in range(10)]

    for carrier in carrier_list:
      run_carrier(domains, carrier, _BROWSERS)

if __name__ == '__main__':
  main(sys.argv)
