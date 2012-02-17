#!/usr/bin/env python

import os
import Queue
import subprocess
import threading
import sys

def pf(msg):
  sys.stdout.write(msg)
  sys.stdout.flush()

class TsharkFields(threading.Thread):
  def __init__(self, file_queue, field, tfilter, values_queue):
    self.file_queue = file_queue
    self.field = field
    self.tfilter = tfilter
    self.values_queue = values_queue
    threading.Thread.__init__(self)

  def run(self):
    try:
      while True:
        filepath = self.file_queue.get(False)
        pf('-')
        cmd = 'tshark -r %s -e %s -T fields -R \"%s\"' % \
            (filepath, self.field, self.tfilter)
        tshark = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                  stderr = subprocess.PIPE)
        pf('.')
        tshark.wait()
        values = [value for value in
                  [line.strip() for line in tshark.stdout.readlines()]
                  if value]
        self.values_queue.put(values)
        self.file_queue.task_done()
    except Queue.Empty:
      return


mylist = []
TMOBILE_IP = '192.168.42.196'
WIRED_IP = '216.165.108.217'

DATA_DIR = '/home/tierney/data/pcaps_Feb_16'
files = os.listdir(DATA_DIR)

wired_file_queue = Queue.Queue()
wired_values_queue = Queue.Queue()
tmobile_file_queue = Queue.Queue()
tmobile_values_queue = Queue.Queue()
for filename in files:
  if not filename.endswith('pcap'):
    continue
  if filename.startswith('wired'):
    wired_file_queue.put(os.path.join(DATA_DIR, filename))
  elif filename.startswith('t-mobile'):
    tmobile_file_queue.put(os.path.join(DATA_DIR, filename))

num_worker_threads = 6
for i in range(num_worker_threads):
  t = TsharkFields(wired_file_queue, 'tcp.analysis.ack_rtt',
                   'tcp.analysis.ack_rtt and ip.dst == %s' % WIRED_IP,
                   wired_values_queue)
  t.daemon = True
  t.start()

for i in range(num_worker_threads):
  t = TsharkFields(tmobile_file_queue, 'tcp.analysis.ack_rtt',
                   'tcp.analysis.ack_rtt and ip.dst == %s' % TMOBILE_IP,
                   tmobile_values_queue)
  t.daemon = True
  t.start()

tmobile_file_queue.join()
wired_file_queue.join()

with open('wired_rtt.log','w') as fh:
  while not wired_values_queue.empty():
    values = wired_values_queue.get()
    for value in values:
      pf(value + ' (w)\n')
      fh.write(value + '\n')
    fh.flush()
    wired_values_queue.task_done()

with open('tmobile_rtt.log','w') as fh:
  while not tmobile_values_queue.empty():
    values = tmobile_values_queue.get()
    for value in values:
      pf(value + ' (t)\n')
      fh.write(value + '\n')
    fh.flush()
    tmobile_values_queue.task_done()
