#!/usr/bin/env python

import gflags
import subprocess
import sys
import time
from selenium import webdriver

FLAGS = gflags.FLAGS

# gflags.DEFINE_string()
# gflags.DEFINE_boolean()
# gflags.DEFINE_integer()
gflags.DEFINE_boolean('debug', False, 'produces debugging output')

# gflags.RegisterValidator()

def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    print '%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS)
    sys.exit(1)
  if FLAGS.debug:
    print 'non-flag arguments:', argv

  print 'Starting tcpdump.'
  tcpdump = subprocess.Popen('sudo tcpdump -i eth1 -evvn -w output.pcap', shell=True)
  time.sleep(2)
  print 'Starting firefox.'
  browser = subprocess.Popen('firefox http://cnn.com', shell=True)
  time.sleep(10)
  print 'Killing everything..'
  browser.kill()
  tcpdump.kill()

if __name__ == '__main__':
  main(sys.argv)
