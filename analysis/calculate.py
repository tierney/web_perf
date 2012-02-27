#!/usr/bin/env python

import os
import Queue
import subprocess
import threading
import time
import sys

TMOBILE_IP = '192.168.42.196'
# WIRED_IP = '216.165.108.217'
WIRED_IP = '192.168.1.10'
VERIZON_IP = '172.20.10.4'

NUM_THREADS = 6
DATA_DIR = '/home/tierney/data/pcaps_Feb_21_00'
files = os.listdir(DATA_DIR)

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
        cmd = 'tshark -r %s -e %s -T fields -R \"%s\"' % \
            (filepath, self.field, self.tfilter)
        tshark = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        tshark.wait()
        values = [value for value in
                  [line.strip() for line in tshark.stdout.readlines()]
                  if value]
        self.values_queue.put(values)
        self.file_queue.task_done()
    except Queue.Empty:
      return
    except Exception, e:
      pf('\nTrouble with: %s.\n' % filepath)
      pf(e)
      raise



def driver(field, shark_filter, pcap_queue, outfilename):
  values_queue = Queue.Queue()
  for i in range(NUM_THREADS):
    t = TsharkFields(pcap_queue, field, shark_filter, values_queue)
    t.daemon = True
    t.start()

  while not pcap_queue.empty():
    pf('to go:       \r')
    pf('to go: %d\r' % pcap_queue.qsize())
    time.sleep(1)

  with open(outfilename,'w') as fh:
    while not values_queue.empty():
      values = values_queue.get(False)
      for value in values:
        fh.write(value + '\n')
      fh.flush()
      values_queue.task_done()


def queues():
  wired_file_queue = Queue.Queue()
  tmobile_file_queue = Queue.Queue()
  verizon_file_queue = Queue.Queue()
  for filename in files:
    if not filename.endswith('pcap'):
      continue
    if filename.startswith('wired'):
      wired_file_queue.put(os.path.join(DATA_DIR, filename))
    elif filename.startswith('t-mobile'):
      tmobile_file_queue.put(os.path.join(DATA_DIR, filename))
    elif filename.startswith('verizon'):
      verizon_file_queue.put(os.path.join(DATA_DIR, filename))

  return wired_file_queue, tmobile_file_queue, verizon_file_queue

wired_file_queue, tmobile_file_queue, verizon_file_queue = queues()
driver('tcp.analysis.ack_rtt', 'tcp.analysis.ack_rtt and ip.dst == %s' % WIRED_IP,
       wired_file_queue, 'wired.rtt.log')
driver('tcp.analysis.ack_rtt', 'tcp.analysis.ack_rtt and ip.dst == %s' % TMOBILE_IP,
       tmobile_file_queue, 't-mobile.rtt.log')
driver('tcp.analysis.ack_rtt', 'tcp.analysis.ack_rtt and ip.dst == %s' % VERIZON_IP,
       verizon_file_queue, 'verizon.rtt.log')

# wired_file_queue, tmobile_file_queue = queues()
# driver('frame.len', 'tcp and not http and ip.src == %s' % WIRED_IP,
#        wired_file_queue,  'wired.len.outgoing.log')
# driver('frame.len', 'tcp and not http and ip.src == %s' % TMOBILE_IP,
#        tmobile_file_queue,  't-mobile.len.outgoing.log')

# wired_file_queue, tmobile_file_queue = queues()
# driver('frame.len', 'tcp and not http and ip.dst == %s' % WIRED_IP,
#        wired_file_queue,  'wired.len.incoming.log')
# driver('frame.len', 'tcp and not http and ip.dst == %s' % TMOBILE_IP,
#        tmobile_file_queue,  't-mobile.len.incoming.log')
