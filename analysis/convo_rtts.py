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
  def __init__(self, syn_ack_rtt, fin_ack_rtt, application_rtts):
    self.syn_ack_rtt = float(syn_ack_rtt)
    self.fin_ack_rtt = float(fin_ack_rtt) if fin_ack_rtt else None
    self.application_rtts = application_rtts

  def __repr__(self):
    app_rtts = '\n'
    for key in self.application_rtts:
      app_rtts += '    %s: %s\n' % (key, self.application_rtts.get(key))
    return 'ConvoStatistics:\n  syn_ack_rtt: %f\n  fin_ack_rtt: %f\n  app_rtts: %s' \
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
    popen_ack_rtts = subprocess.Popen(self.cmd(), shell=True, stdout=subprocess.PIPE)
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

  def rtt_stats(self):
    fields = ['frame.number',
              'frame.len',
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
    convo_packets = [dict(zip(fields, line.strip().split(','))) for line in lines]

    latest_ack_rtt = None
    content_num_packets = 0
    syn_ack_rtt = 0
    fin_ack_rtt = None
    application_rtts = {}

    for packet in convo_packets:
      ack_rtt = packet['tcp.analysis.ack_rtt']
      if ack_rtt:
        # SYN ACK Measurement.
        if not latest_ack_rtt:
          syn_ack_rtt = ack_rtt

        latest_ack_rtt = ack_rtt
        latest_ack_frame = (packet['frame.number'],
                            packet['tcp.analysis.acks_frame'],
                            latest_ack_rtt)

      content_num_packets += 1
      content_type = packet['http.content_type']
      if content_type:
        if content_type not in application_rtts:
          application_rtts[content_type] = []
        application_rtts[content_type].append(
          (int(packet['frame.len']), float(latest_ack_rtt)))
        content_num_packets = 0

    # FIN ACK Measurement.
    if (['1'] == Tshark(self.filename, ['tcp.flags.fin'],
                        ['frame.number == %s' % latest_ack_frame[1]]).lines()
        and
        latest_ack_rtt > 0):
      fin_ack_rtt = latest_ack_rtt

    # Summary
    cs = ConvoStatistics(syn_ack_rtt, fin_ack_rtt, application_rtts)
    return cs

class StatRunner(threading.Thread):
  def __init__(self, queue):
    threading.Thread.__init__(self)
    self.queue = queue
    self.daemon = True
    self.done = False

  def run(self):
    while True:
      try:
        filename = self.queue.get()
      except Queue.Empty:
        self.done = True
        break

      syn_ack_rtts = []
      fin_ack_rtts = []
      application_rtts = {}

      local_ip = list(set(sorted(Tshark(filename, ['ip.src'],
                                        ['tcp.flags.syn == 1',
                                         'tcp.flags.ack == 0']).lines())))

      fields = ['ip.src', 'tcp.srcport', 'ip.dst', 'tcp.dstport',]
      constraints = ['tcp.flags.syn == 1', 'tcp.flags.ack == 0',]

      tcp_convos = list(set(sorted(Tshark(filename, fields, constraints).lines())))
      rtt_stats = []
      for line in tcp_convos:
        convo = SocketConvo(filename, *line.strip().split(','))
        rtt_stats.append(convo.rtt_stats())

      syn_ack_rtts = [rtt_stat.syn_ack_rtt for rtt_stat in rtt_stats
                      if rtt_stat.syn_ack_rtt]
      fin_ack_rtts = [rtt_stat.fin_ack_rtt for rtt_stat in rtt_stats
                      if rtt_stat.fin_ack_rtt]
      for rtt_stat in rtt_stats:
        for app in rtt_stat.application_rtts:
          if app not in application_rtts:
            application_rtts[app] = []
          application_rtts[app] += rtt_stat.application_rtts.get(app)

      # print DataPrinter(syn_ack_rtts, 'SYN')
      # print DataPrinter(fin_ack_rtts, 'FIN')
      # for app in application_rtts:
      #   print DataPrinter([str(duration) for (length, duration) in
      #                      application_rtts.get(app)], app)

      self.queue.task_done()

      # for app in application_rtts:
      #   print ','.join([app] + [str(duration) for (length, duration) in
      #                           application_rtts.get(app)])
        # print app, DataPrinter([duration for (length, duration) in
        #                          application_rtts.get(app)])

        # if app != 'image/jpeg':
        #   continue

        # # DataPrinter(application_rtts.get(app))
        # for (length, duration) in application_rtts.get(app):
        #   print '%d,%f' % (length, duration)
        # print



def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  data_dir = os.path.abspath(FLAGS.datadir)
  filenames = listdir_match(data_dir, 'tmob(reg|hspa)_(chrome|firefox).*pcap$')

  NUM_THREADS=5
  queue = Queue.Queue()
  for filename in filenames[:5]:
    queue.put(filename)

  threads = [StatRunner(queue) for i in range(NUM_THREADS)]
  start = [t.start() for t in threads]
  while True:
    qsize = queue.qsize()
    if qsize == 0:
      break
    sys.stdout.write('%3d tasks remaining.\r' % (qsize))
    sys.stdout.flush()
    time.sleep(1)

  while True:
    completed = [t.done for t in threads]
    if False not in completed:
      break
    sys.stdout.write('waiting....\r')
    sys.stdout.flush()
    time.sleep(1)

if __name__=='__main__':
  main(sys.argv)
