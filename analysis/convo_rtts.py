#!/usr/bin/env python

import logging
import sys
import gflags

FLAGS=gflags.FLAGS

gflags.DEFINE_string('datadir', None, 'data directory', short_name='d')
gflags.MarkFlagAsRequired('datadir')

def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  print FLAGS.datadir

if __name__=='__main__':
  main(sys.argv)
