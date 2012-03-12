#!/usr/bin/env python

# Environment variables set (AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY).

import boto
from boto import ec2
import sys
import time

regions = ec2.regions()

region_indices = [i for i, region in enumerate(regions) if region.name == 'us-west-2']
if len(region_indices) != 1:
  raise Exception('Too many matching regions.')

for region in regions:
  if 'us-' not in region.name:
    continue
  ec2_conn = region.connect()

  ubuntu_server_location = \
      '099720109477/ubuntu/images/ebs/ubuntu-oneiric-11.10-amd64-server-20120222'
  images = ec2_conn.get_all_images(
    filters={'manifest-location': ubuntu_server_location})
  assert len(images) == 1
  image = images[0]

  web = ec2_conn.create_security_group('apache', 'Our Apache Group')
  if not web.authorize('tcp', 80, 80, '0.0.0.0/0'):
    print 'Could not setup web group.'

  ssh = ec2_conn.create_security_group('ssh', 'SSH Access')
  if not ssh.authorize('tcp', 22, 22, cidr_ip='129.98.120.215/32'):
    print 'Could not setup ssh group.'

  reservation = image.run(min_count=1,
                          max_count=1,
                          key_name='id_rsa',
                          security_groups=['ssh', 'apache'],
                          instance_type='t1.micro')

  instance = reservation.instances[0]
  time_waited = 0
  print 'Launching...'
  while 'running' != instance.state:
    sys.stdout.write('Waited %3d seconds...\r' % time_waited)
    sys.stdout.flush()
    time.sleep(1)
    time_waited += 1
    instance.update()
  print

  print 'ssh ubuntu@%s' % (instance.public_dns_name)
  # Hack for stopping automation
  break

  time_left = 15
  while time_left > 0:
    sys.stdout.write('%3d seconds remaining.\r' % time_left)
    sys.stdout.flush()
    time.sleep(1)
    time_left -= 1

  instance.terminate()
  time_waited = 0
  print 'Terminating...'
  while 'terminated' != instance.state:
    sys.stdout.write('Waited %3d seconds...\r' % time_waited)
    sys.stdout.flush()
    time.sleep(1)
    time_waited += 1
    instance.update()
  print

  ec2_conn.delete_security_group('apache')
  ec2_conn.delete_security_group('ssh')

