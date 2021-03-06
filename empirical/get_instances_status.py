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
    for reserv in instances:
      for inst in reserv.instances:
        if inst.state == u'terminated':
          continue
        print "[%-15s] %s is %s" % (region.name, inst.id, inst.state)


if __name__ == "__main__":
  main()
