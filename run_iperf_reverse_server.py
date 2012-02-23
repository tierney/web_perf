#!/usr/bin/env python

import subprocess
import time

def main():
  iperf_fh = open('%s_iperf.log' % str(time.time()), 'w')
  while True:
    iperf_rs = subprocess.Popen(['iperf','-s','--reverse','-i','3'],
                                stdout=iperf_fh, stderr=iperf_fh)
    iperf_rs.wait()

main()
    
