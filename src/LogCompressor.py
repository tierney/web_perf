#!/usr/bin/env python

import logging
import os
import subprocess
import threading
import time

class LogCompressor(threading.Thread):
  def __init__(self, directory):
    self.directory = directory
    threading.Thread.__init__(self)

  def run(self):
    new_files = False
    while True:
      files = os.listdir(self.directory)
      for filename in files:
        if filename.endswith('.ss.log'):
          new_files = True
          to_compress = os.path.join(self.directory, filename)
          logging.info('Compressing %s.' % to_compress)
          subprocess.call(['gzip', to_compress])
      if new_files:
        new_files = False
      time.sleep(1)
