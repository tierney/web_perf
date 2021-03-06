#!/usr/bin/env python

import Queue
import logging
import os
import sys
import threading
import time
import urllib2

logging.basicConfig(
  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
  filename='proactive_cache.log', level=logging.INFO)

class Fetcher(threading.Thread):
  def __init__(self, proactive_cache):
    threading.Thread.__init__(self)
    self.daemon = True
    self.proactive_cache = proactive_cache

  def run(self):
    while True:
      url = self.proactive_cache.queue.get(block=True)
      connection = urllib2.urlopen(url)
      blob = connection.read()
      logging.info('Prefetched %s.' % url)
      self.proactive_cache.cache[url] = blob


class ProactiveCache(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    self.cache = dict()
    self.queue = Queue.Queue()
    self.fetcher = Fetcher(self)
    self.daemon = True
    
  def put(self, netloc, father_path, path):
    if path.startswith('//'):
      url = 'http:' + path
    elif path.startswith('http://'):
      url = path
    else:
      to_fetch = os.path.abspath(os.path.join(father_path, path))
      url = netloc + to_fetch
    logging.info('Putting %s.' % url)
    self.queue.put(url)
  
  def get(self, url):
    # return None
    logging.info('GETTING %s.' % (url))
    getted = self.cache.get(url)
    if getted:
      logging.info('Successful prefetch and hit %s.' % url)
    return getted
  
  def run(self):
    self.fetcher.start()
    while True:
      time.sleep(1)