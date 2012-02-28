#!/usr/bin/env python
import gflags
import subprocess
import threading
import time

FLAGS = gflags.FLAGS

gflags.DEFINE_string('sspath', None, 'Location of fss ss.', short_name = 's')
gflags.DEFINE_string('filename', time.strftime('%Y_%m_%d_%H_%M_%S'),
                     'ss log file.', short_name = 'f')

gflags.MarkFlagAsRequired('sspath')

class FssLogger(object):
  def __init__(self, sspath, filename):
    self.sspath = sspath
    self.filename = filename

  def run(self):
    ss_log_fh = open(self.filename,'w')
    try:
      ss_log = subprocess.Popen([ss.sspath,'g'], stdout = ss_log_fh)
    except Exception, e:
      print e

def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  fss = FssLogger(FLAGS.sspath, FLAGS.filename)

if __name__=='__main__':
  main(sys.argv)
