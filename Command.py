#!/usr/bin/env python
# Example Usage:
#   command = Command("echo 'Process started'; sleep 2; echo 'Process finished'")
#   command.run(timeout=3)
#   command.run(timeout=1)

import logging
import subprocess
import threading

logging.basicConfig(level=logging.INFO)

class Command(object):
  def __init__(self, cmd):
    self.cmd = cmd
    self.process = None

  def run(self, timeout):
    def target():
      logging.info('Thread started')
      self.process = subprocess.Popen(self.cmd, shell=True)
      self.process.communicate()
      logging.info('Thread finished')

    thread = threading.Thread(target=target)
    thread.start()

    thread.join(timeout)
    if thread.is_alive():
      logging.info('Terminating process')
      self.process.terminate()
      thread.join()
    return self.process.returncode
