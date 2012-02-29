#!/usr/bin/env python

import logging
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

class FssLogger(threading.Thread):
  def __init__(self, sspath, filename):
    self.sspath = sspath
    self.filename = filename
    threading.Thread.__init__(self)

  def run(self):
    ss_log_fh = open(self.filename,'w')
    try:
      tcpdump_log = subprocess.Popen(['tcpdump','-n','-w',
                                      self.filename.replace('.ss.log','.pcap')])
      ss_log = subprocess.Popen([self.sspath,'-g'], stdout = ss_log_fh)
      ss_log.wait()
    except KeyboardInterrupt:
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

  fss = FssLogger(FLAGS.sspath, FLAGS.filename)
  fss.run()

if __name__=='__main__':
  main(sys.argv)
