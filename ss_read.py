#!/usr/bin/env python

#timer:(keepalive,26sec,0) users:(("chrome",13263,92)) uid:1000 ino:872263 sk:ffff8802092d3cc0
# 	 mem:(r0,w0,f4096,t0) sack cubic wscale:2,7 rto:752 rtt:188/141 ato:40 cwnd:3 ssthresh:3 send 160.9Kbps rcv_rtt:792 rcv_space:591434

import subprocess
import re

USERS = re.compile('\(\(\"(.*)\",(\d+),(\d+)')

WSCALE = re.compile('wscale:(\d+),(\d+)')
RTO = re.compile('rto:(\d+)')
RTT = re.compile('rtt:([.\d]+)/(\d+)')
ATO = re.compile('ato:(\d+)')
CWND = re.compile('cwnd:(\d+)')
SSTHRESH = re.compile('ssthresh:(\d+)')
SEND = re.compile('send (\d+)([KMG]bps)')
RCV_RTT = re.compile('rcv_rtt:(\d+)')
RCV_SPACE = re.compile('rcv_space:(\d+)')

while True:
  popen = subprocess.Popen(['ss', '-ipem'], stdout=subprocess.PIPE)
  for line in [line.strip() for line in popen.stdout.readlines()]:
    # print line

    m = re.search(USERS, line)
    if m: print 'USERS: ', m.groups()

    # m = re.search(RTT, line)
    # if m: print 'RTT: ', m.groups()

    m = re.search(CWND, line)
    if m: print 'CWND: ', m.groups()
  print
