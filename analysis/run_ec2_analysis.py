#!/usr/bin/env python

import logging
import subprocess
import sys
import time

import gflags

FLAGS = gflags.FLAGS
gflags.DEFINE_string('filename', None, 'pcap file to open', short_name = 'f')
gflags.MarkFlagAsRequired('filename')

class TsharkAnalysis(object):
  def __init__(self, filename):
    self.filename = filename

  def _frame_time_epoch_conversion(self, frame_time):
    regular_time, sub_second = frame_time.split('.')
    ret = (time.mktime(time.strptime(regular_time, "%b  %d, %Y %H:%M:%S")) +\
             (float(sub_second) * (10 ** -9)))
    return ret

  def analyze(self):
    file_metadata = self.filename.split('.')[0]
    timestamp, uuid, location, operator, browser, port = file_metadata.split('_')

    # Not including DNS time.
    if '80' == port or '34343' == port:
      start_time_cmd = 'tshark -r %s -d tcp.port==%s,http -e frame.time '\
          '-T fields -c 1 http.request' % (self.filename, port)
    if port == '443':
      start_time_cmd = 'tshark -r %s  -e frame.time -T fields -c 1 '\
          '"ssl.app_data"' % self.filename

    finish_time_cmd = 'tshark -r %s -e frame.time -T fields '\
        '-R "tcp.flags.fin == 1 and tcp.seq > 1" -c 1' % self.filename

    start_p = subprocess.Popen(
      start_time_cmd, shell=True, stdout=subprocess.PIPE)
    finish_p = subprocess.Popen(
      finish_time_cmd, shell=True, stdout=subprocess.PIPE)

    start_time = self._frame_time_epoch_conversion(start_p.stdout.read())
    finish_time = self._frame_time_epoch_conversion(finish_p.stdout.read())
    duration = finish_time - start_time
    print '%(timestamp)s,%(location)s,%(operator)s,%(port)s,'\
        '%(browser)s,%(duration)f' % locals()


def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  ta = TsharkAnalysis(FLAGS.filename)
  ta.analyze()

if __name__=='__main__':
  main(sys.argv)
