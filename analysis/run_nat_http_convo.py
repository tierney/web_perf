#!/usr/bin/env python

import os
import subprocess
from NatHttpConversations import ConvoParser, average, \
    intersect, ordered_intersect

tsuuid_files = {}
for filename in os.listdir('.'):
  if not filename.endswith('.pcap'):
    continue

  tsuuid = filename.split('.')[0]
  if tsuuid not in tsuuid_files:
    tsuuid_files[tsuuid] = {}

  if 'client' in filename:
    tsuuid_files[tsuuid]['client'] = filename
  elif 'server' in filename:
    tsuuid_files[tsuuid]['server'] = filename
  else:
    print 'PROBLEM: %s' % (filename)

for tsuuid in sorted(tsuuid_files.keys()):
  client_fn = tsuuid_files.get(tsuuid).get('client')
  server_fn = tsuuid_files.get(tsuuid).get('server')

  cp = ConvoParser(client_fn, server_fn)
  client_convos_file_time, client_convos_rtt = cp.client_convos()
  server_convos_file_time, server_convos_rtt = cp.server_convos()

  print '=' * 80
  print tsuuid
  print
  for convo in client_convos_file_time:
    print '  %s:%s -> (%s:%s)' % (convo[0], convo[1], convo[2], convo[3])
    client_rtts = [float(val) for val in client_convos_rtt.get(convo)]
    if client_rtts:
      print '  client rtt min/avg/max = %.3f/%.3f/%.3f ms' % \
          (1000 * min(client_rtts), 1000 * average(client_rtts),
           1000 * max(client_rtts))
    print

  print '  ' + '-' * 78
  print
  for convo in client_convos_file_time:
    convo_dict = {k:v for k,v in client_convos_file_time.get(convo)}
    convo_keys = [key for key, value in client_convos_file_time.get(convo)]
    for possible_match in server_convos_file_time:
      possible_match_keys = [key for key, value in
                             server_convos_file_time.get(possible_match)]
      intersection = ordered_intersect(convo_keys, possible_match_keys)
      if len(intersection) == 0: continue

      # Found a match!
      print '  %s:%s -> %s:%s -> %s:%s' % \
          (convo[0], convo[1], possible_match[0], possible_match[1],
           possible_match[2], possible_match[3])
      match_dict = {k:v for k,v in server_convos_file_time.get(possible_match)}
      client_rtts = [float(val) for val in client_convos_rtt.get(convo)]
      print '  client rtt min/avg/max = %.3f/%.3f/%.3f ms' % \
          (1000 * min(client_rtts), 1000 * average(client_rtts),
           1000 * max(client_rtts))
      server_rtts = [float(val) for val in server_convos_rtt.get(possible_match)]
      print '  server rtt min/avg/max = %.3f/%.3f/%.3f ms' % \
          (1000 * min(server_rtts), 1000 * average(server_rtts),
           1000 * max(server_rtts))

      for match in intersection:
        print '    %-30s %.6f %.6f' % \
            (match, convo_dict.get(match), match_dict.get(match))
      print
