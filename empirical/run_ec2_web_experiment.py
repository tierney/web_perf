#!/usr/bin/env python

# Environment variables set (AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY).

import fcntl
import logging
import socket
import struct
import sys
import threading
import time
import xmlrpclib

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

import boto
from boto import ec2
import gflags
from TimeoutServerProxy import TimeoutServerProxy

FLAGS = gflags.FLAGS
gflags.DEFINE_string('interface', None, 'interface to control experiments',
                     short_name = 'i')
gflags.DEFINE_string('keypair', None, 'keypair to use', short_name = 'k')
gflags.DEFINE_integer('rpcport', 34344, 'RPC port for remote machines to listen on',
                      short_name = 'p')
gflags.MarkFlagAsRequired('interface')
gflags.MarkFlagAsRequired('keypair')

def get_ip_address(ifname):
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  return socket.inet_ntoa(fcntl.ioctl(
    s.fileno(),
    0x8915,  # SIOCGIFADDR
    struct.pack('256s', ifname[:15])
  )[20:24])


class SecurityGroups(object):
  def __init__(self, controller):
    self.controller = controller

  def create(self):
    while True:
      try:
        web = self.controller.connection.create_security_group(
          'apache', 'Our Apache Group')
        web.authorize('tcp', 80, 80, '0.0.0.0/0')

        ssh = self.controller.connection.create_security_group(
          'ssh', 'SSH Access')
        ssh.authorize('tcp', 22, 22, cidr_ip='%s/32' % \
                        (get_ip_address(FLAGS.interface)))

        rpc = self.controller.connection.create_security_group(
          'rpc', 'RPC Access')
        rpc.authorize('tcp', FLAGS.rpcport, FLAGS.rpcport, cidr_ip='%s/32' % \
                        (get_ip_address(FLAGS.interface)))
        break
      except boto.exception.EC2ResponseError:
        logging.warning('Already have security groups.')
        self.delete()
    return ['apache','ssh','rpc']

  def delete(self):
    try:
      self.controller.connection.delete_security_group('apache')
      self.controller.connection.delete_security_group('ssh')
      self.controller.connection.delete_security_group('rpc')
    except boto.exception.EC2ResponseError:
      logging.warning('Problem deleting security groups.')

class Ec2Controller(threading.Thread):
  def __init__(self, region):
    threading.Thread.__init__(self)
    self.region = region
    self.instance = None
    self.connection = None
    self.state = None
    self.stop = threading.Event()

  def run(self):
    self.connection = self.region.connect()

    ubuntu_server_location = \
        '099720109477/ubuntu/images/ebs/ubuntu-oneiric-11.10-amd64-server-20120222'
    images = self.connection.get_all_images(
      filters={'manifest-location': ubuntu_server_location})
    assert len(images) == 1
    image = images[0]

    security_groups = SecurityGroups(self).create()

    user_data = """#!/bin/bash
set -e -x
export DEBIAN_FRONTEND=noninteractive
apt-get install apache2 python-gflags -y
wget -O /tmp/example.tar.gz http://theseus.news.cs.nyu.edu/example.tar.gz
tar xf /tmp/example.tar.gz
mv example/* /var/www/
rmdir example
wget http://theseus.news.cs.nyu.edu/run_ec2_rpc_server.py
chmod +x run_ec2_rpc_server.py
./run_ec2_rpc_server.py -p %d &
""" % (FLAGS.rpcport)

    reservation = image.run(min_count=1,
                            max_count=1,
                            key_name=FLAGS.keypair,
                            user_data = user_data,
                            security_groups=security_groups,
                            instance_type='t1.micro')

    self.instance = reservation.instances[0]
    time_waited = 0
    logging.info('[%s] Launching instance.' % self.region.name)
    while 'running' != self.instance.state:
      time.sleep(1)
      time_waited += 1
      self.instance.update()

    logging.info(' Launched: %s,%s' % (self.region.name, self.instance.public_dns_name))
    self.state = 'running'

    while not self.stop.is_set():
      time.sleep(1)

    self.instance.terminate()
    time_waited = 0
    logging.info('[%s] Terminating instance.' % self.region.name)
    while 'terminated' != self.instance.state:
      time.sleep(1)
      time_waited += 1
      self.instance.update()

    SecurityGroups(self).delete()
    self.state = 'terminated'

  def kill(self):
    self.stop.set()

def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  all_regions = ec2.regions()
  # ['eu-west-1','sa-east-1','us-east-1','ap-northeast-1',
  #  'us-west-1','us-west-2','ap-southeast-1']
  regions = [region for region in all_regions if region.name in
             ['us-east-1']] #, 'us-west-1','us-west-2']]

  logging.info('Working in the following regions: %s.' % \
                 [str(region.name) for region in regions])
  controllers = [Ec2Controller(region) for region in regions]
  for controller in controllers:
    controller.daemon = True

  for controller in controllers:
    controller.start()

  while True:
    ready = 0
    for controller in controllers:
      if controller.state == 'running':
        ready += 1
    if len(controllers) == ready:
      break
    time.sleep(1)

  print 'All running...'
  while True:
    rpc_ready = 0
    for controller in controllers:
      try:
        server = TimeoutServerProxy(
          'http://%s:%d' % (controller.instance.public_dns_name, FLAGS.rpcport),
          timeout = 5)
        if server.ready():
          rpc_ready += 1
      except Exception, e:
        pass
    if len(controllers) == rpc_ready:
      break
    time.sleep(1)

  raw_input('All RPC ready.')

  for controller in controllers:
    controller.kill()

  while True:
    terminated = 0
    for controller in controllers:
      if controller.state == 'terminated':
        terminated += 1
    if len(controllers) == terminated:
      break
    time.sleep(1)

if __name__=='__main__':
  main(sys.argv)