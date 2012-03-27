#!/usr/bin/env python

import re
import logging
import os
import subprocess
import sys
import gflags

FLAGS=gflags.FLAGS

gflags.DEFINE_string('datadir', None, 'data directory', short_name='d')
gflags.MarkFlagAsRequired('datadir')

def listdir_match(directory, pattern):
  matching_files = []
  to_match = re.compile(pattern)
  filenames = os.listdir(directory)
  for filename in filenames:
    if not re.match(to_match, filename):
      continue
    matching_files.append(os.path.join(directory, filename))
  return matching_files

class SocketConvo(object):
  def __init__(self, src_ip, src_port, dst_ip, dst_port):
    self.src_ip = src_ip
    self.src_port = src_port
    self.dst_ip = dst_ip
    self.dst_port = dst_port
  def __repr__(self):
    return 'SocketConvo (%s:%s <-> %s:%s)' % (self.src_ip, self.src_port, self.dst_ip, self.dst_port)

def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  data_dir = os.path.abspath(FLAGS.datadir)
  filenames = listdir_match(data_dir,
                            'tmob(reg|hspa)_(chrome|firefox).*pcap$')
  for filename in filenames[:1]:
    popen_local_ip = subprocess.Popen(
      'tshark -r %(filename)s -e ip.src -T fields -R "tcp.flags.syn == 1 '\
        'and tcp.flags.ack == 0" | sort | uniq' % locals(),
      shell=True, stdout=subprocess.PIPE)
    local_ip = popen_local_ip.stdout.read().strip()
    print '"%s"' % local_ip

    fields = ['ip.src',
              'tcp.srcport',
              'ip.dst',
              'tcp.dstport',
              ]
    joined_fields = ' -e ' + ' -e '.join(fields)

    popen_tcp_convos = subprocess.Popen(
      'tshark -r %(filename)s %(joined_fields)s -T fields -E separator=, '\
        '-R "tcp.flags.syn == 1 and tcp.flags.ack == 0" | sort | uniq' \
        % locals(), shell=True, stdout=subprocess.PIPE)

    for line in popen_tcp_convos.stdout.readlines():
      convo = SocketConvo(*line.strip().split(','))
      print convo
      # Reverse the conversation direction to get the RTT.
      cmd = 'tshark -r %s -e tcp.analysis.ack_rtt -T fields -R "ip.src == %s and '\
          'tcp.srcport == %s and ip.dst == %s and tcp.dstport == %s and tcp.analysis.ack_rtt"' \
          % (filename, convo.dst_ip, convo.dst_port, convo.src_ip, convo.src_port)
      print cmd
      popen_ack_rtts = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
      print popen_ack_rtts.stdout.read()

if __name__=='__main__':
  main(sys.argv)
