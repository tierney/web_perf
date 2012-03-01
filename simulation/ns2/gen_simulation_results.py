#!/usr/bin/env python

import subprocess

for ot in range(2, 11):
  for tm in range(2, 11):
    print ot, tm
    popen = subprocess.Popen(['./plot_ns2_results.py','--ot',str(ot),
                              '--tm',str(tm)])
    popen.wait()

