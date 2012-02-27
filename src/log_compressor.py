#!/usr/bin/env  python

import os
import subprocess
import time

new_files = False
while True:
  files = os.listdir('.')
  for filename in files:
    if filename.endswith('.ss.log'):
      new_files = True
      print 'Compressing %s.' % filename
      subprocess.call(['gzip',filename])
  if new_files:
    print '.'
    new_files = False
  time.sleep(1)
