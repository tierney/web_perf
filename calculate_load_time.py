#!/usr/bin/env python

import os
import Queue
import subprocess
import threading
import time
import sys

NUM_THREADS = 10
DATA_DIR = '/home/tierney/data/pcaps_Feb_20'
files = os.listdir(DATA_DIR)

_TSHARK_BIN = '/home/tierney/repos/wireshark/tshark'

def pf(msg):
  sys.stdout.write(msg)
  sys.stdout.flush()

class TsharkFields(threading.Thread):
  def __init__(self, pcap_queue, values_queue):
    self.pcap_queue = pcap_queue
    self.values_queue = values_queue
    threading.Thread.__init__(self)

  def _frame_time_epoch_conversion(self, frame_time):
    regular_time, sub_second = frame_time.split('.')
    ret = (time.mktime(time.strptime(regular_time, "%b  %d, %Y %H:%M:%S")) +\
             (float(sub_second) * (10 ** -9)))
    return ret

  def run(self):
    try:
      while True:
        filepath = self.pcap_queue.get(False)

        cmd = _TSHARK_BIN + ' -r %s -e frame.time -T fields dns' % filepath
        dns_reqs = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        dns_lines = [line.strip() for line in dns_reqs.stdout.readlines()]
        # No DNS request...
        if not dns_lines:
          pf('No DNS request for %s.\n' % filepath)
          self.pcap_queue.task_done()
          continue

        start = self._frame_time_epoch_conversion(dns_lines[0])

        cmd = _TSHARK_BIN + ' -r %s -e frame.time -T fields tcp' % filepath
        tcp_packets = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE)
        tcp_lines = [line.strip() for line in tcp_packets.stdout.readlines()]

        # No TCP responses to the DNS requests.
        if not tcp_lines:
          pf('No TCP response for %s.\n' % filepath)
          self.pcap_queue.task_done()
          continue

        finish = self._frame_time_epoch_conversion(tcp_lines[-1])

        # Only log values where we have a reasonable measure of the page having
        # loaded (no TCP packets before the DNS request should count).
        if finish > start:
          self.values_queue.put(finish - start)
        self.pcap_queue.task_done()
    except Queue.Empty:
      return
    except Exception, e:
      pf(filepath + '\n')
      pf(str(e))
      raise

def driver(pcap_queue, outfilename):
  values_queue = Queue.Queue()
  for i in range(NUM_THREADS):
    t = TsharkFields(pcap_queue, values_queue)
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
driver(wired_file_queue, 'wired.load_time.log')
driver(tmobile_file_queue, 't-mobile.load_time.log')
# driver(verizon_file_queue, 'verizon.loss_rate.log')
