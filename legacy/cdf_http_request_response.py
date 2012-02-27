#!/usr/bin/env python

import gflags
import subprocess
import sys
import time
import datetime

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import scikits
import scikits.statsmodels as sm
from scikits.statsmodels import tools

filename = 'verizon_chrome_163.com_1328592928.52.pcap'

def _frame_time_epoch_conversion(frame_time):
  regular_time, sub_second = frame_time.split('.')
  return (time.mktime(time.strptime(regular_time, "%b  %d, %Y %H:%M:%S")) +\
            (float(sub_second) * (10 ** -9)))

fig = plt.figure()
plt.title('%s GET Request (blue) and Response (green) CDF.' % filename)
plt.xlabel('Time (seconds).')
plt.ylabel('Fraction of total GET Requests issued or Responses logged.')

# Requests.

cmd = 'tshark -r %s -e frame.time -T fields -R "http.request"' % \
    (filename)
popen = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE)
lines = [line.strip() for line in popen.stdout.readlines()]
epochs = [_frame_time_epoch_conversion(timestamp)
          for timestamp in lines]
ecdf = tools.tools.ECDF(epochs)
try:
  x = np.linspace(min(epochs), max(epochs))
except ValueError:
  print 'No data for: %s.' % filename

y = ecdf(x)
plt.step(x,y)

# Responses.

cmd = 'tshark -r %s -e frame.time -T fields -R "http.response"' % \
    (filename)
popen = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE)
lines = [line.strip() for line in popen.stdout.readlines()]
epochs = [_frame_time_epoch_conversion(timestamp)
          for timestamp in lines]
ecdf = tools.tools.ECDF(epochs)
try:
  x = np.linspace(min(epochs), max(epochs))
except ValueError:
  print 'No data for: %s.' % filename

y = ecdf(x)
plt.step(x,y)

plt.show()

# fig = plt.figure()
# ax = fig.add_subplot(111)
# ax.plot(x_epoch, y_size, 'o-')
# plt.show()
