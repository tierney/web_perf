#!/usr/bin/env python

import os
import subprocess
from NatHttpConversations import ConvoParser, average

uuid_files = {}
for filename in os.listdir('.'):
  uuid = filename.split('_')[0]
  if uuid not in uuid_files:
    uuid_files[uuid] = {}

  if 'client' in filename:
    uuid_files[uuid]['client'] = filename
  elif 'server' in filename:
    uuid_files[uuid]['server'] = filename
  else:
    print 'PROBLEM: %s' % (filename)

for uuid in uuid_files:
  client_fn = uuid_files.get(uuid).get('client')
  server_fn = uuid_files.get(uuid).get('server')

  cp = ConvoParser(client_fn, server_fn)
  client_convos_file_time, client_convos_rtt = cp.client_convos()
  server_convos_file_time, server_convos_rtt = cp.server_convos()

  print uuid
  for convo in client_convos_file_time:
    print '  %s:%s -> (%s:%s)' % (convo[0], convo[1], convo[2], convo[3])
    client_rtts = [float(val) for val in client_convos_rtt.get(convo)]
    if client_rtts:
      print '  client rtt min/avg/max = %.3f/%.3f/%.3f ms' % (1000 * min(client_rtts), 1000 * average(client_rtts), 1000 * max(client_rtts))
    print
