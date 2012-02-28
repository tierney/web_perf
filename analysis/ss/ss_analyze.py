#!/usr/bin/env python

import cPickle
import math
import time

import numpy as np
import matplotlib
# Calling matplotlib.use() before import pyplot frees us from requiring a
# $DISPLAY environment variable; i.e, makes it easier to script this process.
# TODO(tierney): This image backend should be made more portable.
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

with open('conn_cwnd.pkl', 'r') as fh:
  conn = cPickle.load(fh)

for four_tuple in conn.keys()[:1]:
  print four_tuple

  x = [float(l[0]) for l in conn[four_tuple]]
  for i, entry in enumerate(conn[four_tuple]):
    x[i] += (1.e-9 * int(entry[1]))
  cwnds = [l[2] for l in conn[four_tuple]]
  x = [matplotlib.dates.epoch2num(entry) for entry in x]

  assert(len(x) == len(cwnds))
  print len(x)
  fig = plt.figure(1, figsize=(10,6))
  limit = 16000
  plt.plot_date(x[:limit], cwnds[:limit], tz='EST')
  fig.savefig('plot' + '.png')

  with open('plot.log','w') as fh:
    for i, entry in enumerate(x):
      fh.write('%f %s\n' % (entry, cwnds[i]))
  # keys = {}
  # for e in cwnds:
  #   keys[e] = 1
  # print four_tuple, keys.keys()


