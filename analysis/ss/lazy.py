#!/usr/bin/env python

import os
import shlex
import subprocess

_LOG_PATH = '/scratch/data/FssLogs'
for filename in os.listdir(_LOG_PATH):
  if not filename.endswith('ss.log.gz'):
    continue

  print filename
  parse = subprocess.Popen(shlex.split('./ss_parse.py -s /scratch/data/FssLogs/%s -z' % filename))
  parse.wait()
  plot = subprocess.Popen(shlex.split('./ss_analyze.py -p cwnd.pkl -p rtt.pkl -j cwnd.pkl,rto.pkl,rtt.pkl -l %s' % filename.replace('.ss.log.gz','')))
  plot.wait()
