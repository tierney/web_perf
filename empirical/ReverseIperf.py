#!/usr/bin/env python

import logging
import shlex
import subprocess
import sys
from uuid import uuid4

import gflags
from RpcClient import Client

FLAGS = gflags.FLAGS
gflags.DEFINE_string('host', None, 'host to connect to', short_name = 'h')
gflags.DEFINE_string('port', None, 'port to connect to', short_name = 'p')
gflags.DEFINE_string('iperf', None, 'iperf location', short_name = 'i')
gflags.DEFINE_string('iperfopts', '', 'iperf options', short_name = 'o')

gflags.MarkFlagAsRequired('host')
gflags.MarkFlagAsRequired('port')
gflags.MarkFlagAsRequired('iperf')

def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  uuid = str(uuid4())

  Client(FLAGS.host, FLAGS.port, 'begin', uuid).run()

  tcpdump_cmd = 'tcpdump -n -i any -w %s.client.pcap' % uuid
  tcpdump_args = shlex.split(tcpdump_cmd)
  tcpdump_popen = subprocess.Popen(tcpdump_args)

  # iperf_cmd = "%s --reverse -c %h -w 1M" % (FLAGS.iperf, FLAGS.host)
  # iperf_args = shlex.split(iperf_cmd)
  iperf_popen = subprocess.Popen([FLAGS.iperf, '--reverse', '-c', FLAGS.host])
  iperf_popen.wait()

  tcpdump_popen.terminate()

  Client(FLAGS.host, FLAGS.port, 'end').run()

if __name__=='__main__':
  main(sys.argv)
