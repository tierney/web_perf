#!/usr/bin/env python

import gflags
import logging
import os
import shlex
import subprocess
import sys

FLAGS = gflags.FLAGS

gflags.DEFINE_string('bzipped_pcap', None, 'path to bzipped pcap file',
                     short_name = 'p')
gflags.MarkFlagAsRequired('bzipped_pcap')


class ExtractResponses(object):
  def __init__(self, bzipped_pcap_path):
    self.bzipped_pcap_path = bzipped_pcap_path
    self.pcap_path = bzipped_pcap_path.replace('.bz2', '')

  def _bunzip(self):
    subprocess.call(['bunzip2', self.bzipped_pcap_path])

  def _bzip(self):
    subprocess.call(['bzip2', self.pcap_path])

  def extract(self):
    dats_dir = self.bzipped_pcap_path.replace('.bz2', '.dats')
    if not os.path.exists(dats_dir):
      os.mkdir(dats_dir)

    self._bunzip()
    extractor = subprocess.Popen(
      'tshark -r %s -R "tcp.port == 80" -w - | tcptrace -e -n stdin' % \
        (os.path.abspath(self.pcap_path)),
      shell=True,
      cwd=dats_dir)
    extractor.wait()
    self._bzip()

    subprocess.call(shlex.split('tar cjf %s %s' % \
                                  (dats_dir + '.tar.bz2', dats_dir)))
    os.system('rm -rf "%s"' % dats_dir)


def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  er = ExtractResponses(FLAGS.bzipped_pcap)
  er.extract()

if __name__=='__main__':
  main(sys.argv)
