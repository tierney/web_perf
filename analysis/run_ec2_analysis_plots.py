#!/usr/bin/env python

import logging
import sys

import gflags
import numpy as np
import matplotlib
# Calling matplotlib.use() before import pyplot frees us from requiring a
# $DISPLAY environment variable; i.e, makes it easier to script this process.
# TODO(tierney): This image backend should be made more portable.
# matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

matplotlib.rcParams['legend.fontsize'] = 'x-small'
matplotlib.rcParams['legend.fancybox'] = True
matplotlib.rcParams['ytick.labelsize'] = 'x-small'

FLAGS = gflags.FLAGS
gflags.DEFINE_string('filename', None, 'file to open', short_name = 'f')
gflags.MarkFlagAsRequired('filename')

def average(data):
  if not data:
    return 0
  return (sum(data) / (1. * len(data)))

def plot_data(operator_to_plot, data_lines):
  duration_dict = {}
  for data_line in data_lines:
    timestamp, ec2_region, operator, port, browser, duration = data_line.split(',')
    if operator != operator_to_plot:
      continue
    if 'firefox' == browser:
      continue

    # Format key for dictionary.
    key = (ec2_region, operator)
    if key not in duration_dict:
      duration_dict[key] = {}
    if port not in duration_dict[key]:
      duration_dict[key][port] = []
    duration_dict[key][port].append((browser, float(duration)))

  # Global max_val.
  max_val = 0
  for key in duration_dict:
    port_durations = duration_dict.get(key)
    for port in port_durations:
      max_val = max([max_val] + [bd[1] for bd in port_durations.get(port)])

  num_rows = len(duration_dict)
  plot_num = 0
  sorted_duration_dict = sorted(duration_dict)

  fig = plt.figure(1, figsize=(4.25, 10))
  fig.subplots_adjust(hspace=0.3)

  plt.suptitle(operator_to_plot)
  for row_num, key in enumerate(sorted_duration_dict):
    print key
    # Locally-calculated max-val.
    max_val = 0
    port_durations = duration_dict.get(key)

    for port in port_durations:
      max_val = max([max_val] + [bd[1] for bd in port_durations.get(port)])

    for port in duration_dict.get(key):
      # print key, port,
      bds = duration_dict.get(key).get(port)
      # print bds,

      data = [bd[1] for bd in bds]
      if '443' == port:
        data = [bd[1] for bd in bds if 'chrome' == bd[0]]
      # print data

      if '80' == port:
        ax = plt.subplot(num_rows,1, row_num)
        plt.xlabel(' '.join(key), fontsize='x-small')
        ax.xaxis.set_ticks([])
        plt.ylim(0,max_val)
        plt.ylabel('Seconds', fontsize='x-small')
        plt.plot(data, 'bo-', label = 'P.80')

      if '34343' == port:
        plt.subplot(num_rows,1, row_num)
        plt.xlabel(' '.join(key))
        plt.ylim(0,max_val)
        print port, data[0], data
        plt.bar(2.1, data[0], color='r', alpha=0.7, label = 'P.34343')

      if '443' == port:
        plt.subplot(num_rows,1, row_num)
        plt.xlabel(' '.join(key))
        plt.ylim(0,max_val)
        plt.bar(4.1, average(data), color='g', alpha=0.7, label = 'SPDY')

    leg = plt.legend(loc='lower left', fancybox=True)
    leg.get_frame().set_alpha(0.2)

  plt.savefig(operator_to_plot + '.png', bbox_inches='tight')
  plt.clf()

def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  with open('duration.log') as fh:
    data_lines = [line.strip() for line in fh.readlines()]

  plot_data('verizon', data_lines)
  plot_data('tmobile', data_lines)


if __name__=='__main__':
  main(sys.argv)
