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
gflags.DEFINE_multistring('pickles', None, 'pickle files "<data_type>.pkl"',
                          short_name = 'p')
gflags.DEFINE_string('joint', None,
                     'comma-separated list of pickles to plot together',
                     short_name = 'j')
gflags.DEFINE_string('label', None, 'label for directory that will contain graphs',
                     short_name = 'l')

gflags.MarkFlagAsRequired('pickles')
gflags.MarkFlagAsRequired('label')

def four_tuple_to_filename(four_tuple):
  return '_'.join([pair.replace(':','_') for pair in four_tuple])

def average(values):
  if not values: return 0
  return sum(values, 0.0) / len(values)

def plot(data_type, path, four_tuple, conn):
  print data_type,
  # Process data from Pickle.
  x = [float(l[0]) for l in conn[four_tuple]]
  for i, entry in enumerate(conn[four_tuple]):
    x[i] += (1.e-9 * int(entry[1]))
  data = [l[2] for l in conn[four_tuple]]
  x = [matplotlib.dates.epoch2num(entry) for entry in x]
  assert(len(x) == len(data))

  # Plot formatting issues.
  plt.clf()
  fig = plt.figure(1, figsize=(8,6))
  plt.xlabel('Timestamp', fontsize='x-small')
  plt.ylabel(data_type, fontsize='x-small')
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
  print four_tuple

def xy_from_conn(conn, four_tuple):
  x = [float(l[0]) for l in conn[four_tuple]]
  for i, entry in enumerate(conn[four_tuple]):
    x[i] += (1.e-9 * int(entry[1]))
  data = [l[2] for l in conn[four_tuple]]
  x = [matplotlib.dates.epoch2num(entry) for entry in x]
  assert(len(x) == len(data))
  return x,data

def plot_twinx(label, path, four_tuple, conn0, conn1, conn2):
  print label,
  label0, label1, label2 = label.split(',')
  x0, data0 = xy_from_conn(conn0, four_tuple)
  x1, data1 = xy_from_conn(conn1, four_tuple)
  x2, data2 = xy_from_conn(conn2, four_tuple)

  plt.clf()
  fig = plt.figure(figsize=(8,6))
  ax0 = fig.add_subplot(111)
  fontsize = 'x-small'

  lower_limit = 1
  upper_limit = -1

  mdates.DateFormatter('%M:%S')
  line0 = ax0.plot_date(x0[lower_limit:upper_limit], data0[lower_limit:upper_limit],'b.-', label=label0)
  ax1 = ax0.twinx()
  line1 = ax1.plot_date(x1[lower_limit:upper_limit], data1[lower_limit:upper_limit],'r.-', label=label1)
  line1 = ax1.plot_date(x2[lower_limit:upper_limit], data2[lower_limit:upper_limit],'g.-', label=label2)

  lines = line0 + line1
  labels = [l.get_label() for l in lines]
  ax0.legend(lines, labels, loc='upper left')
  ax0.grid()
  ax0.set_xlabel('Timestamp', fontsize=fontsize)
  ax0.set_ylabel(label0, fontsize=fontsize)
  ax1.set_ylabel(label1, fontsize=fontsize)

  for tick in ax0.xaxis.get_major_ticks():
    tick.label1.set_fontsize(fontsize)
  for tick in ax0.yaxis.get_major_ticks():
    tick.label1.set_fontsize(fontsize)
  for tick in ax1.get_yticklabels():
    tick.set_fontsize(fontsize)

  fig.savefig(os.path.join(os.path.join(FLAGS.label, label),
                           four_tuple_to_filename(four_tuple) + '.png'),
              bbox_inches='tight')
  print four_tuple

def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  # os.mkdir(FLAGS.label)
  # for pickle_path in FLAGS.pickles:
  #   logging.info('Processing: %s.' % pickle_path)
  #   path, pickle_name = os.path.split(pickle_path)
  #   data_type = pickle_name.rstrip('.pkl')
  #   os.mkdir(os.path.join(FLAGS.label, data_type))

  #   with open(pickle_path) as fh:
  #     conn = cPickle.load(fh)

  #   for four_tuple in conn.keys():
  #     plot(data_type, path, four_tuple, conn)

  if FLAGS.joint:
    pickle_path0, pickle_path1 = FLAGS.joint.split(',')
    with open(pickle_path0) as fh:
      conn0 = cPickle.load(fh)
    with open(pickle_path1) as fh:
      conn1 = cPickle.load(fh)
    path0, pickle_name0 = os.path.split(pickle_path0)
    path1, pickle_name1 = os.path.split(pickle_path1)
    assert path0 == path1

    label = FLAGS.joint.replace('.pkl','')
    try:
      os.mkdir(os.path.join(FLAGS.label, label))
    except OSError:
      pass

    print conn0.keys()
    print conn1.keys()
    # assert conn0.keys() == conn1.keys()
    for four_tuple in conn0.keys():
      plot_twinx(label, path0, four_tuple, conn0, conn1)

if __name__=='__main__':
  main(sys.argv)
