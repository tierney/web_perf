#!/usr/bin/env python

import re
import logging
import os
import subprocess
import sys
import time
import threading
import Queue
from numpy import std,var,median,mean
import gflags

MEDIA_TYPE = re.compile('(.*)\/([a-zA-Z\-\+]*);*(.*)')

FLAGS=gflags.FLAGS

gflags.DEFINE_string('datadir', None, 'data directory', short_name='d')
gflags.MarkFlagAsRequired('datadir')

def get_var(input_dict, accessor_string):
  """Gets data from a dictionary using a dotted accessor-string"""
  current_data = input_dict
  for chunk in accessor_string.split('.'):
    current_data = current_data.get(chunk, {})
  return current_data

def listdir_match(directory, pattern):
  matching_files = []
  to_match = re.compile(pattern)
  filenames = os.listdir(directory)
  for filename in filenames:
    if not re.match(to_match, filename):
      continue
    matching_files.append(os.path.join(directory, filename))
  return matching_files


class DataPrinter(object):
  def __init__(self, data, tag):
    self.data = data
    self.tag = tag

  def __repr__(self):
    ret = ''
    for datum in self.data:
      ret += '%s,%s\n' % (str(datum), self.tag)
    return ret


class ConvoStatistics(object):
  # type_label, rtt_measurement, **other data
  def __init__(self, syn_ack_rtt, fin_ack_rtt, application_rtts):
    self.syn_ack_rtt = syn_ack_rtt
    self.fin_ack_rtt = fin_ack_rtt if fin_ack_rtt else None
    self.application_rtts = application_rtts

  def __repr__(self):
    app_rtts = '\n'
    for key in self.application_rtts:
      app_rtts += '    %s: %s\n' % (key, self.application_rtts.get(key))
    return 'ConvoStats:\n syn_ack_rtt: %s\n fin_ack_rtt: %s\n app_rtts: %s' \
        % (self.syn_ack_rtt, self.fin_ack_rtt, app_rtts)


class Tshark(object):
  def __init__(self, filename, fields, constraints):
    self.filename = filename
    self.fields = fields
    self.constraints = constraints

  def cmd(self):
    cmd_fields = ' -e ' + ' -e '.join(self.fields)
    cmd_constraints = ' and '.join(self.constraints)
    cmd = 'tshark -r %s -T fields -E separator=, %s -R "%s"' \
        % (self.filename, cmd_fields, cmd_constraints)
    return cmd

  def lines(self):
    popen_ack_rtts = subprocess.Popen(self.cmd(), shell=True,
                                      stdout=subprocess.PIPE)
    return [line.strip() for line in popen_ack_rtts.stdout.readlines()]


class SocketConvo(object):
  def __init__(self, filename, src_ip, src_port, dst_ip, dst_port):
    self.filename = filename
    self.src_ip = src_ip
    self.src_port = src_port
    self.dst_ip = dst_ip
    self.dst_port = dst_port

  def __repr__(self):
    return 'SocketConvo (%s:%s <-> %s:%s)' \
        % (self.src_ip, self.src_port, self.dst_ip, self.dst_port)

  def _is_fin(self, packet):
    return ['1'] == Tshark(self.filename, ['tcp.flags.fin'],
                           ['frame.number == %s' \
                              % packet['tcp.analysis.acks_frame']]).lines()

  def convo_packets(self):
    fields = ['frame.number',
              'frame.len',
              'ip.src',
              'tcp.srcport',
              'ip.dst',
              'tcp.dstport',
              'tcp.analysis.acks_frame',
              'tcp.flags.syn',
              'tcp.flags.fin',
              'tcp.analysis.ack_rtt',
              'http.content_type',
              ]
    constraints = ['ip.src == %s ' % self.dst_ip,
                   'tcp.srcport == %s' % self.dst_port,
                   'ip.dst == %s' % self.src_ip,
                   'tcp.dstport == %s' % self.src_port,
                   ]
    lines = Tshark(self.filename, fields, constraints).lines()
    convo_packets = [dict(zip(fields, line.strip().split(',')))
                     for line in lines]

    latest_ack_rtt = None
    content_num_packets = 0
    syn_ack_rtt = None
    fin_ack_rtt = None
    application_rtts = {}
    ret_convo_packets = []
    for packet in convo_packets:
      packet['filename'] = self.filename
      ack_rtt = packet['tcp.analysis.ack_rtt']
      if ack_rtt:
        # SYN ACK Measurement.
        if not latest_ack_rtt:
          packet['label'] = 'ACK'
          ret_convo_packets.append(packet)

        latest_ack_packet = packet

      content_num_packets += 1
      content_type = packet['http.content_type']

      if content_type:
        packet['label'] = packet['http.content_type']
        packet['tcp.analysis.ack_rtt'] = latest_ack_packet['tcp.analysis.ack_rtt']
        ret_convo_packets.append(packet)
        content_num_packets = 0

    # FIN ACK Measurement.
    if (self._is_fin(latest_ack_packet) and
        latest_ack_packet['tcp.analysis.ack_rtt'] > 0):

      latest_ack_packet['label'] = 'FIN'
      ret_convo_packets.append(latest_ack_packet)

    # Summary
    return ret_convo_packets

class StatRunner(threading.Thread):
  def __init__(self, in_queue, out_queue):
    threading.Thread.__init__(self)
    self.in_queue = in_queue
    self.out_queue = out_queue
    self.daemon = True
    self.done = False

  def run(self):
    while True:
      try:
        filename = self.in_queue.get(False)
        logging.info('Dequeued %s.' % filename)
      except Queue.Empty:
        self.done = True
        return

      syn_ack_rtts = []
      fin_ack_rtts = []
      application_rtts = {}

      local_ip = list(set(sorted(Tshark(filename, ['ip.src'],
                                        ['tcp.flags.syn == 1',
                                         'tcp.flags.ack == 0']).lines())))

      fields = ['ip.src', 'tcp.srcport', 'ip.dst', 'tcp.dstport',]
      constraints = ['tcp.flags.syn == 1', 'tcp.flags.ack == 0',]

      tcp_convos = list(set(sorted(
            Tshark(filename, fields, constraints).lines())))

      convo_packets = []
      for line in tcp_convos:
        convo = SocketConvo(filename, *line.strip().split(','))
        convo_packets.append(convo.convo_packets())

      logging.info('Finished %s.' % filename)

      self.out_queue.put(convo_packets)
      self.in_queue.task_done()

class OutQueueWriter(threading.Thread):
  def __init__(self, filename, out_queue):
    threading.Thread.__init__(self)
    self.out_queue = out_queue
    self.filename = filename
    self.daemon = True
    self._fh = None

  def _write_data(self, filename, content_type, rtts):
    ret = ''
    for length, rtt in rtts:
      ret += '%(filename)s,%(content_type)s,%(length)s,%(rtt)s\n' % locals()
    self._fh.write(ret)
    self._fh.flush()

  def run(self):
    fields_to_print=['label',
                     'tcp.analysis.ack_rtt',
                     'frame.len',
                     'ip.src',
                     'tcp.srcport',
                     'tcp.dstport',
                     ]

    derived_fields = ['filename', 'hspa', 'cached', 'domain', 'media_type',
                      'media_subtype', 'media_subtype_parameter']

    with open(os.path.expanduser(self.filename), 'w') as self._fh:
      self._fh.write(','.join(derived_fields + fields_to_print) + '\n')
      self._fh.flush()
      while True:
        out_data = self.out_queue.get()
        for convo in out_data:
          for packet in convo:
            media_type, media_subtype, media_subtype_parameter = ('', '', '')

            filename = os.path.basename(packet['filename'])
            sfilename = filename.split('_')

            hspa = 'TRUE' if 'tmobhspa' == sfilename[0] else 'FALSE'
            cached = 'TRUE' if 'firefox' == sfilename[1] else 'FALSE'
            domain = sfilename[2]

            m = re.search(MEDIA_TYPE, packet['label'])
            if m:
              media_type, media_subtype, media_subtype_parameter = m.groups()

            self._fh.write(
              ','.join([filename,hspa,cached,domain,media_type,
                        media_subtype, media_subtype_parameter]) + ',' + \
                ','.join([packet[field] for field in fields_to_print]) + '\n')
        self._fh.flush()


def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  data_dir = os.path.abspath(FLAGS.datadir)
  filenames = listdir_match(data_dir, 'tmob(reg|hspa)_(chrome|firefox).*pcap$')

  NUM_THREADS=5
  in_queue = Queue.Queue()
  out_queue = Queue.Queue()
  for filename in filenames[:10]:
    in_queue.put(filename)

  out_writer = OutQueueWriter('~/data.log', out_queue)
  out_writer.start()

  threads = [StatRunner(in_queue, out_queue) for i in range(NUM_THREADS)]
  start = [t.start() for t in threads]
  while True:
    qsize = in_queue.qsize()
    if qsize == 0:
      break
    sys.stdout.write('%3d tasks remaining.\r' % (qsize))
    sys.stdout.flush()
    time.sleep(1)
  print

  while True:
    completed = [t.done for t in threads]
    if False not in completed:
      break
    sys.stdout.write('Waiting on %-3d tasks.\r' % completed.count(False))
    sys.stdout.flush()
    time.sleep(1)

  # TODO(tierney): Find a better way to wait for outwriter to finish.
  print '\nDone.'
  time.sleep(3)

if __name__=='__main__':
  main(sys.argv)
