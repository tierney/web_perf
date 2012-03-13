#!/usr/bin/env python

import re
import shlex
import subprocess

#Current IP Address: 216.165.95.72
RETURNED_IP_INFO = re.compile('Current IP Address: (.*)')

get_external_ip = subprocess.Popen(
  shlex.split('lynx -dump "http://checkip.dyndns.org"'),
  stdout=subprocess.PIPE)
ret = get_external_ip.stdout.read()
m = re.search(RETURNED_IP_INFO, ret)
if m: ip_addr, = m.groups()
print ip_addr

