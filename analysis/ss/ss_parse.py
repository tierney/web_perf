#!/usr/bin/env python

import cPickle
import logging
import re
import sys
import gflags

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

FLAGS = gflags.FLAGS

gflags.DEFINE_string('filename', None, 'ss log file.', short_name = 's')
gflags.DEFINE_string('picklename', 'conn_cwnd.pkl', 'Output pickle filename.',
                     short_name = 'p')

gflags.MarkFlagAsRequired('filename')

USERS = re.compile('\(\(\"(.*)\",(\d+),(\d+)')

WSCALE = re.compile('wscale:(\d+),(\d+)')
RTO = re.compile('rto:(\d+)')
RTT = re.compile('rtt:([.\d]+)/(\d+)')
ATO = re.compile('ato:(\d+)')
CWND = re.compile('cwnd:(\d+)')
SSTHRESH = re.compile('ssthresh:(\d+)')
SEND = re.compile('send (\d+)([KMG]bps)')
RCV_RTT = re.compile('rcv_rtt:(\d+)')
RCV_SPACE = re.compile('rcv_space:(\d+)')

def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  with open(FLAGS.filename) as fh:
    ss_log = [line.strip() for line in fh.readlines()]
    ss_log.reverse()

  conn_cwnd = dict()

  while ss_log:
    line = ss_log.pop()

    if 'TIMESTAMP' in line:
      try:
        monotonic = ss_log.pop()
        realtime = ss_log.pop()
      except IndexError:
        break
      # print "New entry: %s . %s" % (monotonic, realtime)

    ip_addrs = re.findall('[0-9]+(?:\.[0-9]+){3}:[0-9]+', line)
    if ip_addrs:
      src_ip_port, dest_ip_port = ip_addrs
      tcp_4tuple = (src_ip_port, dest_ip_port)
      continue

    m = re.search(CWND, line)
    if m:
      cwnd = m.groups()[0]
      if tcp_4tuple not in conn_cwnd:
        conn_cwnd[tcp_4tuple] = []
      try:
        ts_type, sec, nsec = realtime.split('\t')
      except ValueError, e:
        logging.error('%s: %s.' % (str(e), realtime))
        sys.exit(1)
      conn_cwnd[tcp_4tuple].append((sec, nsec, cwnd))

  logging.info("Writing pickle.")

  with open(FLAGS.picklename, 'w') as fh:
    cPickle.dump(conn_cwnd, fh)

if __name__=='__main__':
  main(sys.argv)


