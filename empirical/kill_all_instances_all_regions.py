#!/usr/bin/env python

import sys
import time
from boto import ec2

REGIONS_LIST = ['eu-west-1','sa-east-1','us-east-1','ap-northeast-1',
                'us-west-1','us-west-2','ap-southeast-1']

def main():
  all_regions = ec2.regions()
  regions = [region for region in all_regions if region.name in REGIONS_LIST]

  for region in regions:
    conn = region.connect()
    instances = conn.get_all_instances()
    print '[%-15s] Reservations: %s' % (region.name, instances)
    for reserv in instances:
      for inst in reserv.instances:
        if inst.state not in [u'shutting-down', u'terminated']:
          print "[%-10s] Terminating instance %s (%s)." % \
              (region.name, inst, inst.state)
          inst.terminate()

if __name__ == "__main__":
  main()
