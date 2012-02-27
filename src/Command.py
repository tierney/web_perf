#!/usr/bin/env python
# Example Usage:
#   command = Command("echo 'Process started'; sleep 2; echo 'Process finished'")
#   command.run(timeout=3)
#   command.run(timeout=1)

import logging
import os
import shlex
import signal
import subprocess
import threading

logging.basicConfig(level=logging.INFO)

class Command(object):
  def __init__(self, cmd):
    self.cmd = cmd
    self.process = None

  def run(self, timeout, pskill=None):
    def target():
      logging.info('Thread started')
      self.process = subprocess.Popen(shlex.split(self.cmd))
      self.process.communicate()
      logging.info('Thread finished')

    thread = threading.Thread(target=target)
    thread.start()

    thread.join(timeout)
    if thread.is_alive():
      logging.info('Terminating process')
      self.process.terminate()
      thread.join()
    if pskill:
      to_kill = subprocess.Popen('ps axo pid,cmd | grep %s' % pskill,
                                 shell=True, stdout=subprocess.PIPE)
      lines = [line.strip() for line in to_kill.stdout.readlines()]
      for line in lines:
        try:
          pid, cmd = line.split()
          os.kill(pid, signal.SIGKILL)
        except OSError:
          logging.error('pid already killed: (%s, %s).' % (line, cmd))
        except ValueError, e:
          logging.error('%s: %s.' % (str(e), line))

    return self.process.returncode
