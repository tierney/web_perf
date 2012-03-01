#!/usr/bin/env python

import cPickle
import gzip
import bz2
import logging
import re
import sys
import gflags

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

FLAGS = gflags.FLAGS

gflags.DEFINE_string('filename', None, 'ss log file.', short_name = 's')
gflags.DEFINE_boolean('gzipped', False, 'ss log is gzipped', short_name = 'z')
gflags.DEFINE_boolean('bzipped', False, 'ss log is bzipped', short_name = 'j')

gflags.MarkFlagAsRequired('filename')

USERS = re.compile('\(\(\"(.*)\",(\d+),(\d+)')

WSCALE = re.compile('wscale:(\d+),(\d+)')
RTO = re.compile('rto:(\d+)')
RTT = re.compile('rtt:([.\d]+)/\d+')
RTTVAR = re.compile('rtt:[.\d]+/(\d+)')
ATO = re.compile('ato:(\d+)')
CWND = re.compile('cwnd:(\d+)')
SSTHRESH = re.compile('ssthresh:(\d+)')
SEND = re.compile('send (\d+[KMG]bps)')
RCV_RTT = re.compile('rcv_rtt:(\d+)')
RCV_SPACE = re.compile('rcv_space:(\d+)')

IP_ADDR_PORT = re.compile('[0-9]+(?:\.[0-9]+){3}:[0-9]+')

def dictify(realtime, tcp_four_tuple, regex, line, data_dict):
  m = re.search(regex, line)
  if m:
    data = m.groups()[0]
    if tcp_four_tuple not in data_dict:
      data_dict[tcp_four_tuple] = []
    ts_type, sec, nsec = realtime.split('\t')
    data_dict[tcp_four_tuple].append((sec, nsec, data))

class Organizer(object):
  def __init__(self):
    pass

def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  if FLAGS.gzipped:
    open_func = gzip.open
  elif FLAGS.bzipped:
    open_func = bz2.BZ2File
  else:
    open_func = open

  fh = open_func(FLAGS.filename)

  ss_log = [line.strip() for line in fh.readlines()]
  ss_log.reverse()
  fh.close()

  conn_cwnd = dict()
  conn_rto = dict()
  conn_rtt = dict()
  conn_rttvar = dict()

  monotonic = None
  realtime = None
  tcp_4tuple = None
  while ss_log:
    line = ss_log.pop()

    if 'TIMESTAMP' in line:
      try:
        monotonic = ss_log.pop()
        realtime = ss_log.pop()
      except IndexError, e:
        logging.error(str(e))
        break

    ip_addrs = re.findall(IP_ADDR_PORT, line)
    if ip_addrs:
      try:
        src_ip_port, dest_ip_port = ip_addrs
      except ValueError, e:
        logging.error("%s: %s." % (str(e), ip_addrs))
        break

      tcp_4tuple = (src_ip_port, dest_ip_port)
      continue

    if not realtime or not monotonic or not tcp_4tuple:
      continue

    dictify(realtime, tcp_4tuple, CWND, line, conn_cwnd)
    dictify(realtime, tcp_4tuple, RTO, line, conn_rto)
    dictify(realtime, tcp_4tuple, RTT, line, conn_rtt)
    dictify(realtime, tcp_4tuple, RTTVAR, line, conn_rttvar)

  logging.info("Writing pickles.")

  with open('cwnd.pkl', 'w') as fh:
    cPickle.dump(conn_cwnd, fh)
  with open('rto.pkl', 'w') as fh:
    cPickle.dump(conn_rto, fh)
  with open('rtt.pkl', 'w') as fh:
    cPickle.dump(conn_rtt, fh)
  with open('rttvar.pkl', 'w') as fh:
    cPickle.dump(conn_rttvar, fh)

if __name__=='__main__':
  main(sys.argv)
