#!/usr/bin/env python

import logging
import os
import subprocess
import sys
import threading
import time

logging.basicConfig(stream=sys.stdout)

import gflags

FLAGS = gflags.FLAGS

gflags.DEFINE_string('sspath', None, 'Location of fss ss.', short_name = 's')
gflags.DEFINE_string('filename',
                     time.strftime('%Y_%m_%d_%H_%M_%S') + '.ss.log',
                     'ss log file.', short_name = 'f')

gflags.MarkFlagAsRequired('sspath')

def status_files():
  files = os.listdir('.')
  retval = None
  if 'BEGIN' in files: retval ='BEGIN'
  if 'END' in files: retval = 'END'
  if 'HALT' in files: retval = 'HALT'

  if retval: os.remove(retval)
  return retval

class FssLogger(threading.Thread):
  def __init__(self, sspath, filename):
    self.sspath = sspath
    self.filename = filename
    threading.Thread.__init__(self)

  def run(self):
    ss_log_fh = open(self.filename,'w')
    tcpdump_log = subprocess.Popen(['tcpdump','-i','any','-n','-w',
                                    self.filename.replace('.ss.log','.pcap')])
    ss_log = subprocess.Popen([self.sspath,'-g'], stdout = ss_log_fh)

    while True:
      time.sleep(1)
      status = status_files()
      if not status:
        continue
      if 'END' == status:
        break

    ss_log_fh.flush()
    ss_log.terminate()
    tcpdump_log.terminate()
    logging.info('Done.')
    subprocess.call(['gzip', FLAGS.filename])
    print 'gzipped log filename:\n%s' % (FLAGS.filename + '.gz')
    print 'pcap file:\n%s' % (self.filename.replace('.ss.log','.pcap'))
    ss_log_fh.close()

def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  while True:
    time.sleep(1)
    status = status_files()
    if 'BEGIN' == status:
      fss = FssLogger(FLAGS.sspath, FLAGS.filename)
      fss.run()
    if 'HALT' == status:
      break
  logging.debug('Done.')

if __name__=='__main__':
  main(sys.argv)
