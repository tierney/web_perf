#!/usr/bin/env python

import gflags
import math
import os
import subprocess
import sys
import time
import datetime
import logging

import numpy as np
import matplotlib
# Calling matplotlib.use() before import pyplot frees us from requiring a
# $DISPLAY environment variable; i.e, makes it easier to script this process.
# TODO(tierney): This image backend should be made more portable.
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import scikits
import scikits.statsmodels as sm
from scikits.statsmodels import distributions

FLAGS = gflags.FLAGS

gflags.DEFINE_multistring('filename', '', 'Name of data file (flag can be repeated).',
                          short_name = 'f')
gflags.DEFINE_string('plot_name','plot', 'Name of output plot (*excluding* suffix).',
                     short_name = 'p')
gflags.DEFINE_string('title', '', 'Title for plot.',
                     short_name = 't')
gflags.DEFINE_string('xlabel', '', 'X-axis label for plot.',
                     short_name = 'x')
gflags.DEFINE_string('xmax', '', 'X-axis maximum value.')
gflags.DEFINE_string('ylabel', '', 'Y-axis label for plot.',
                     short_name = 'y')
gflags.DEFINE_boolean('xlog', False, 'Set xscale to log.',
                      short_name = 'l')


logging.basicConfig()


class CDFPlotter(object):
  def __init__(self, filepaths):
    self.filepaths = filepaths

  def _get_stripped_file_lines(self):
    ret = []
    for filepath in self.filepaths:
      try:
        with open(filepath) as fh:
          ret.append([line.strip() for line in fh.readlines()])
      except IOError, e:
        logging.error('File does not exist: %s.' % e)
        raise
    return ret

  def run(self):
    dataset = [[float(entry) for entry in data]
               for data in self._get_stripped_file_lines()]
    if not data:
      return None

    # Plot aesthetics.
    fig = plt.figure(1)
    plt.title('%s' % FLAGS.title)
    xlabel = FLAGS.xlabel
    if FLAGS.xlog:
      xlabel = 'log( ' + xlabel + ' )'
    plt.xlabel(xlabel)
    plt.ylabel(FLAGS.ylabel)

    data_plts = []
    for i, data in enumerate(dataset):
      ecdf = distributions.ECDF(data)
      if FLAGS.xmax:
        x = np.linspace(0, float(FLAGS.xmax), num=len(data))
      else:
        x = np.linspace(min(data), max(data), num=len(data))
      y = ecdf(x)
      plt.step(x, y, '.-', label=self.filepaths[i])

    xmin, xmax, ymin, ymax = plt.axis()
    plt.axis((xmin, xmax, 0, 1))
    plt.legend(loc='lower right')
    if FLAGS.xlog:
      plt.xscale('log')
    fig.savefig(FLAGS.plot_name + '.png')


def main(argv):
  try:
    argv = FLAGS(argv) # Parse flags.
  except gflags.FlagsError, e:
    print '%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS)
    sys.exit(1)

  cdfplotter = CDFPlotter(FLAGS.filename)
  cdfplotter.run()

if __name__ == '__main__':
  main(sys.argv)
