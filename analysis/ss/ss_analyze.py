#!/usr/bin/env python

import cPickle
import logging
import math
import os
import sys
import time

import gflags

import numpy as np
import matplotlib
# Calling matplotlib.use() before import pyplot frees us from requiring a
# $DISPLAY environment variable; i.e, makes it easier to script this process.
# TODO(tierney): This image backend should be made more portable.
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

FLAGS = gflags.FLAGS
gflags.DEFINE_multistring('pickles', None, 'Pickle files "<data_type>.pkl"',
                          short_name = 'p')
gflags.DEFINE_string('label', None, 'Label for directory that will contain graphs.',
                     short_name = 'l')

gflags.MarkFlagAsRequired('pickles')
gflags.MarkFlagAsRequired('label')

def four_tuple_to_filename(four_tuple):
  return '_'.join([pair.replace(':','_') for pair in four_tuple])

def plot(data_type, path, four_tuple, conn):
  print four_tuple

  x = [float(l[0]) for l in conn[four_tuple]]
  for i, entry in enumerate(conn[four_tuple]):
    x[i] += (1.e-9 * int(entry[1]))
  data = [l[2] for l in conn[four_tuple]]

  x = [matplotlib.dates.epoch2num(entry) for entry in x]

  assert(len(x) == len(data))

  print len(x)
  plt.clf()
  fig = plt.figure(1, figsize=(8,6))

  plt.xlabel('Timestamp', fontsize='x-small')
  plt.ylabel(data_type, fontsize='x-small')

  # Plot formatting issues.
  plt.rc("axes", linewidth=2.0)
  fontsize = 'x-small'
  ax = plt.gca()
  for tick in ax.xaxis.get_major_ticks():
    tick.label1.set_fontsize(fontsize)
  for tick in ax.yaxis.get_major_ticks():
    tick.label1.set_fontsize(fontsize)

  lower_limit = 1
  upper_limit = -1

  plt.plot_date(x[lower_limit:upper_limit], data[lower_limit:upper_limit])
  fig.savefig(os.path.join(os.path.join(FLAGS.label, data_type),
                           four_tuple_to_filename(four_tuple) + '.png'),
              bbox_inches='tight')

  def average(values):
    if not values:
      return 0
    return sum(values, 0.0) / len(values)
  print 'avg: %f' % average([float(i) for i in data[lower_limit:upper_limit]])

def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  os.mkdir(FLAGS.label)

  for pickle_path in FLAGS.pickles:
    logging.info('Processing: %s.' % pickle_path)
    path, pickle_name = os.path.split(pickle_path)
    data_type = pickle_name.rstrip('.pkl')
    os.mkdir(os.path.join(FLAGS.label, data_type))

    with open(pickle_path) as fh:
      conn = cPickle.load(fh)

    for four_tuple in conn.keys():
      plot(data_type, path, four_tuple, conn)

if __name__=='__main__':
  main(sys.argv)
