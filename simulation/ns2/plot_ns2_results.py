#!/usr/bin/env python

import logging
import os
import subprocess
import sys

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
gflags.DEFINE_string('ot', None, 'operator to tower queue')
gflags.DEFINE_string('tm', None, 'tower to mobile queue')
gflags.DEFINE_string('plotname', 'plot.png',
                     'Name of output plot, including file extension.')
gflags.MarkFlagAsRequired('ot')
gflags.MarkFlagAsRequired('tm')

def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  if os.path.exists('result0'):
    os.remove('result0')
  popen = subprocess.Popen(['ns','ns-bufferbloat.tcl',
                            '-ot',FLAGS.ot,
                            '-tm',FLAGS.tm,
                            ])
  popen.wait()
  with open('result0') as fh:
    data = [line.strip() for line in fh.readlines()]

  timestamps = []
  cwins = []
  rtts = []
  for line in data:
    ts, cwin, ack, rtt = line.split()
    timestamps.append(ts)
    cwins.append(cwin)
    rtts.append(rtt)

  plt.clf()
  fig = plt.figure(figsize=(8,6))
  ax0 = fig.add_subplot(111)
  fontsize = 'x-small'

  line0 = ax0.plot(timestamps, cwins,'b.-', label='cwin')
  ax1 = ax0.twinx()
  line1 = ax1.plot(timestamps, rtts,'r.-', label='rtt')

  lines = line0 + line1
  labels = [l.get_label() for l in lines]
  ax0.legend(lines, labels, loc='upper left')
  ax0.grid()
  ax0.set_title('%s %s' % (FLAGS.ot, FLAGS.tm))
  ax0.set_xlim(0,45)
  ax0.set_ylim(0,400)
  ax0.set_xlabel('Timestamp', fontsize=fontsize)
  ax0.set_ylabel('cwin', fontsize=fontsize)
  ax1.set_ylabel('rtt', fontsize=fontsize)

  for tick in ax0.xaxis.get_major_ticks():
    tick.label1.set_fontsize(fontsize)
  for tick in ax0.yaxis.get_major_ticks():
    tick.label1.set_fontsize(fontsize)
  for tick in ax1.get_yticklabels():
    tick.set_fontsize(fontsize)

  fig.savefig(FLAGS.plotname, bbox_inches='tight')

if __name__=='__main__':
  main(sys.argv)
