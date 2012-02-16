#!/usr/bin/env python

import gflags
import os
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

FLAGS = gflags.FLAGS

gflags.DEFINE_string('filename', '', 'Name of data file.',
                     short_name = 'f')
gflags.DEFINE_boolean('duration', False, 'Duration of dump.',
                      short_name = 'd')
gflags.DEFINE_boolean('ack_rtt', False, 'ACK RTT graph.',
                      short_name = 'a')
gflags.DEFINE_boolean('get_spawn', False, 'GET Request time CDF.',
                      short_name = 'g')

gflags.RegisterValidator('filename', lambda value: value is not '',
                         message = 'Filename required.', flag_values = FLAGS)

class Analyze(object):
  def __init__(self, filename):
    self.filename = filename
    self._parse_filename()


  def _frame_time_epoch_conversion(self, frame_time):
    regular_time, sub_second = frame_time.split('.')
    return (time.mktime(time.strptime(regular_time, "%b  %d, %Y %H:%M:%S")) +\
        (float(sub_second) * (10 ** -9)))

  def _parse_filename(self):
    self.carrier, self.browser, self.site, self.epoch_time =\
        os.path.split(self.filename)[1][:-5].split('_')

  def duration(self):
    first_dns_req = subprocess.Popen("tshark -r %s -e frame.time -T fields dns" % self.filename,
                                     shell = True, stdout = subprocess.PIPE)
    dns_lines = [line.strip() for line in first_dns_req.stdout.readlines()]
    start = self._frame_time_epoch_conversion(dns_lines[0])

    tcp_packets = subprocess.Popen("tshark -r %s -e frame.time -T fields tcp" % self.filename,
                                   shell = True, stdout = subprocess.PIPE)
    tcp_lines = [line.strip() for line in tcp_packets.stdout.readlines()]
    finish = self._frame_time_epoch_conversion(tcp_lines[-1])
    print finish - start

  def get_request_response_time_cdf(self):
    # Base plot.
    fig = plt.figure()
    plt.title('%s %s %s GET Req. (blue) and Resp. (green) CDF' % \
                (self.carrier.capitalize(), self.browser.capitalize(), self.site))
    plt.xlabel('Time (seconds).')
    plt.ylabel('Fraction of total GET Reqs. or Resps. logged.')

    # Requests
    cmd = 'tshark -r %s -e frame.time -T fields -R "http.request"' % \
        (FLAGS.filename)
    popen = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE)
    lines = [line.strip() for line in popen.stdout.readlines()]
    epochs = [self._frame_time_epoch_conversion(timestamp)
              for timestamp in lines]
    ecdf = tools.tools.ECDF(epochs)

    try:
      x = np.linspace(min(epochs), max(epochs))
    except ValueError:
      print 'No request data for: %s.' % FLAGS.filename
      return
    y = ecdf(x)
    plt.step(x,y)

    # Responses
    cmd = 'tshark -r %s -e frame.time -T fields -R "http.response"' % \
        (FLAGS.filename)
    popen = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE)
    lines = [line.strip() for line in popen.stdout.readlines()]
    epochs = [self._frame_time_epoch_conversion(timestamp)
              for timestamp in lines]
    ecdf = tools.tools.ECDF(epochs)
    try:
      x = np.linspace(min(epochs), max(epochs))
    except ValueError:
      print 'No response data for: %s.' % FLAGS.filename
      return

    y = ecdf(x)
    plt.step(x,y)
    fig.savefig('get_request_response_cdf_%s.png' % FLAGS.filename)

  def ack_time(self):
    cmd = "tshark -r verizon_chrome_hulu.com_1328618574.58.pcap -e frame.time "\
        "-e tcp.analysis.ack_rtt -T fields tcp.analysis.ack_rtt"
    popen = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE)
    lines = [line.strip() for line in popen.stdout.readlines()]

    x_epoch = list()
    y_size = list()
    for line in lines:
      dt = self._frame_time_epoch_conversion(line[:31])
      ack_rtt = line[32:]

      print dt, ack_rtt

      x_epoch.append(dt)
      y_size.append(ack_rtt)

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(x_epoch, y_size, 'o-')
    plt.show()

  def run(self):
    # popen = subprocess.Popen("tshark -r %s -e frame.time -T fields" %
    #                          self.filename, shell = True,
    #                          stdout = subprocess.PIPE)
    popen = subprocess.Popen(
      "tshark -r verizon_firefox_xunlei.com_1328610414.9.pcap " \
        "-e frame.time -e http.content_length -T fields http.content_length",
      shell = True, stdout = subprocess.PIPE)

    lines = [line.strip() for line in popen.stdout.readlines()]

    x_epoch = []
    y_size = []
    prev_dt = None
    for line in lines:
      dt = self._frame_time_epoch_conversion(line[:31])
      print dt, line[32:]

      x_epoch += [dt]
      y_size += [int(line[32:])]

      # if not prev_dt:
      #   prev_dt = dt
      #   continue
      # print 'Diff: %.9f' % (dt - prev_dt)
      # prev_dt = dt

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(x_epoch, y_size, 'o-')
    plt.show()

def main(argv):
  try:
    argv = FLAGS(argv) # Parse flags.
  except gflags.FlagsError, e:
    print '%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS)
    sys.exit(1)

  a = Analyze(FLAGS.filename)
  if FLAGS.duration:
    a.duration()
    sys.exit(0)

  if FLAGS.ack_rtt:
    a.ack_time()
    sys.exit(0)

  if FLAGS.get_spawn:
    a.get_request_response_time_cdf()
    sys.exit(0)

  a.run()

if __name__ == '__main__':
  main(sys.argv)
