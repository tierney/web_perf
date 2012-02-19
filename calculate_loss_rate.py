#!/usr/bin/env python

import os
import Queue
import subprocess
import threading
import time
import sys

# Feb 16
# TMOBILE_IP = '192.168.42.196'
# WIRED_IP = '216.165.108.217'

# Feb 7
VERIZON_IP = '172.20.10.4'
TMOBILE_IP = '192.168.42.196'

NUM_THREADS = 10
DATA_DIR = '/home/tierney/data/pcaps'
files = os.listdir(DATA_DIR)

def pf(msg):
  sys.stdout.write(msg)
  sys.stdout.flush()

class TsharkFields(threading.Thread):
  def __init__(self, pcap_queue, total_filter, subset_filter, values_queue):
    self.pcap_queue = pcap_queue
    self.total_filter = total_filter
    self.subset_filter = subset_filter
    self.values_queue = values_queue
    threading.Thread.__init__(self)

  def run(self):
    try:
      while True:
        filepath = self.pcap_queue.get(False)

        cmd = 'tshark -r %s -R \"%s\"' % (filepath, self.total_filter)
        total = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)

        cmd = 'tshark -r %s -R \"%s\"' % (filepath, self.subset_filter)
        subset = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)

        total_tcp_packets = len(total.stdout.readlines())
        if (0 == total_tcp_packets):
          self.pcap_queue.task_done()
          continue

        rtx_packets = len(subset.stdout.readlines())
        total.wait()
        subset.wait()

        loss_rate = rtx_packets / (1. * total_tcp_packets)

        self.values_queue.put(loss_rate)
        self.pcap_queue.task_done()
    except Queue.Empty:
      return
    except Exception, e:
      pf(str(e))
      raise

def driver(pcap_queue, total_filter, subset_filter, outfilename):
  values_queue = Queue.Queue()
  for i in range(NUM_THREADS):
    t = TsharkFields(pcap_queue, total_filter, subset_filter, values_queue)
    t.daemon = True
    t.start()

  while not pcap_queue.empty():
    pf('%s to go:      \r' % outfilename)
    pf('%s to go: %d\r' % (outfilename, pcap_queue.qsize()))
    time.sleep(1)

  with open(outfilename,'w') as fh:
    while not values_queue.empty():
      value = values_queue.get(False)
      fh.write(str(value) + '\n')
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
# driver(wired_file_queue,
#        'tcp and not http and ip.dst == %s' % WIRED_IP,
#        'not http and tcp.analysis.retransmission and ip.dst == %s' % WIRED_IP,
#        'wired.loss_rate.log')
driver(tmobile_file_queue,
       'tcp and not http and ip.dst == %s' % TMOBILE_IP,
       'not http and tcp.analysis.retransmission and ip.dst == %s' % TMOBILE_IP,
       't-mobile.loss_rate.log')
driver(verizon_file_queue,
       'tcp and not http and ip.dst == %s' % VERIZON_IP,
       'not http and tcp.analysis.retransmission and ip.dst == %s' % VERIZON_IP,
       'verizon.loss_rate.log')
