#!/usr/bin/env python

import gflags
import subprocess
import sys
import time

FLAGS = gflags.FLAGS

gflags.DEFINE_string('iperf', None, 'iperf (reverse NAT-capable) path.',
                     short_name = 'i')

gflags.MarkFlagAsRequired('iperf')


def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  iperf_fh = open('%s_iperf.log' % str(time.time()), 'w')
  while True:
    iperf_rs = subprocess.Popen([FLAGS.iperf,'-s','--reverse','-i','3',
                                 '-t','45'], stdout=iperf_fh, stderr=iperf_fh)
    iperf_rs.wait()

if __name__=='__main__':
  main(sys.argv)

