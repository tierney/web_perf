#!/usr/bin/env python

import cPickle

with open('conn_cwnd.pkl', 'r') as fh:
  conn = cPickle.load(fh)

for four_tuple in conn.keys():
  cwnds = [l[2] for l in conn[four_tuple]]

  keys = {}
  for e in cwnds:
    keys[e] = 1
  print four_tuple, keys.keys()


