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

gflags.MarkFlagAsRequired('sspath')

def status_files():
  files = os.listdir('.')
  retval = None
  uuid = None
  if 'BEGIN' in files:
    with open('BEGIN') as fh:
      uuid = fh.read()
    retval = 'BEGIN'
  if 'END' in files: retval = 'END'
  if 'HALT' in files: retval = 'HALT'

  if retval: os.remove(retval)
  return retval, uuid

class FssLogger(threading.Thread):
  def __init__(self, sspath, filename):
    self.sspath = sspath
    self.filename = filename
    threading.Thread.__init__(self)

  def run(self):
    ss_log_fh = open(self.filename,'w')
    tcpdump_log = subprocess.Popen(
      ['tcpdump','-i','any','-n','-w',
       self.filename.replace('.ss.log','.server.pcap')])
    ss_log = subprocess.Popen([self.sspath,'-g'], stdout = ss_log_fh)

    while True:
      time.sleep(1)
      status = status_files()
      if not status:
        continue
      status, uuid = status
      if 'END' == status:
        break

    ss_log_fh.flush()
    ss_log.terminate()
    tcpdump_log.terminate()
    logging.info('Done.')
    subprocess.call(['bzip2', self.filename])
    subprocess.call(['bzip2', self.filename.replace('.ss.log','.server.pcap')])
    print 'gzipped log filename:\n%s' % (self.filename + '.bz2')
    print 'pcap file:\n%s' % (self.filename.replace('.ss.log','.pcap') + '.bz2')
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
    if not status: continue
    status, uuid = status
    if 'BEGIN' == status:
      fss = FssLogger(FLAGS.sspath,
                      time.strftime('%Y_%m_%d_%H_%M_%S')
                      + '_%s' % uuid
                      + '.ss.log')
      fss.run()
    if 'HALT' == status:
      break
  logging.debug('Done.')

if __name__=='__main__':
  main(sys.argv)
