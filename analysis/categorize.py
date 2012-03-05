#!/usr/bin/env python

import os
import shutil

prefix_network = {
  '216.165' : 'beaker',
  '208.54' : 't-mobile',
  '174.252': 'verizon',
  '129.98' : 'yeshiva',
}

for network in prefix_network.values():
  if not os.path.exists(network):
    os.mkdir(network)

for dirpath, dirnames, filenames in os.walk('.'):
  if [fn for fn in filenames if fn.endswith('.png')]:

    if dirpath.startswith('./verizon') or \
          dirpath.startswith('./t-mobile') or \
          dirpath.startswith('./verizon'):
      continue

    # print dirpath, dirnames, filenames
    for filename in filenames:
      # 216.165.108.71_5001_208.54.44.212_20786.png
      ips_ports = filename.replace('.png','')
      try:
        theseus, port5001, netip, netport = ips_ports.split('_')
      except ValueError:
        continue
      slash_16 = '.'.join(netip.split('.')[:2])
      if slash_16 in prefix_network:
        network = prefix_network.get(slash_16)
        print netip, prefix_network.get(slash_16)
        try:
          label = dirpath.replace('./','').replace('/','_')

          shutil.copy2(os.path.join(dirpath, filename),
                       os.path.join(network, label + '.png'))
        except shutil.Error:
          print 'trying to continue'
      else:
        print netip
