#!/usr/bin/env python

# Environment variables set (AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY).

import fcntl
import logging
import os
import socket
import struct
import sys
import threading
import time
import xmlrpclib

logging.basicConfig(
  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
  stream=sys.stdout, level=logging.INFO)

import boto
from boto import ec2
import gflags
from TimeoutServerProxy import TimeoutServerProxy

FLAGS = gflags.FLAGS

ALLOWED_CIDR_IPS = ['216.165.0.0/16', '129.98.120.0/24'] + \
    [line.strip() for line in open('cell_phone_prefixes.txt').readlines()]

REGIONS_LIST = [
  'eu-west-1',
  'sa-east-1',
  'us-east-1',
  'ap-northeast-1',
  'us-west-1',
  'us-west-2',
  'ap-southeast-1',
  ]

gflags.DEFINE_integer('num_instances', None, 'number of instances', short_name = 'n')
gflags.DEFINE_multistring('regions', REGIONS_LIST, 'regions to spawn experiment to',
                          short_name = 'r')
gflags.DEFINE_string('keypair', None, 'keypair to use', short_name = 'k')
gflags.DEFINE_integer('rpcport', 34344, 'RPC port for remote machines to listen on',
                      short_name = 'p')
gflags.DEFINE_string('wwwpath', '~/www', 'path to web directory', short_name = 'w')

gflags.MarkFlagAsRequired('num_instances')
gflags.MarkFlagAsRequired('keypair')

def get_ip_address(ifname):
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  return socket.inet_ntoa(fcntl.ioctl(
    s.fileno(),
    0x8915,  # SIOCGIFADDR
    struct.pack('256s', ifname[:15])
  )[20:24])


class SecurityGroups(object):
  protocol_port = {
    'http': 80,
    'ssl' : 443,
    'wacky': 34343,
    'ssh': 22,
    'rpc': 34344,
    }

  def __init__(self, controller):
    self.controller = controller

  def create(self):
    while True:
      try:
        for protocol in self.protocol_port:
          security_group = self.controller.connection.create_security_group(
            protocol, 'Our %s Group' % protocol)
          security_group.authorize('tcp', self.protocol_port.get(protocol),
                                   self.protocol_port.get(protocol),
                                   ALLOWED_CIDR_IPS)

        break
      except boto.exception.EC2ResponseError:
        logging.warning('Already have security groups.')
        self.delete()
    return self.protocol_port.keys()

  def delete(self):
    for protocol in self.protocol_port:
      try:
        self.controller.connection.delete_security_group(protocol)
      except boto.exception.EC2ResponseError:
        logging.warning('Problem deleting security group %s.' % protocol)


class Ec2Controller(threading.Thread):
  def __init__(self, region, num_instances):
    threading.Thread.__init__(self)
    self.region = region
    self.num_instances = num_instances
    self.instances = None
    self.connection = None
    self.state = None
    self.stop = threading.Event()
    self.public_dns_names_path = \
        os.path.expanduser(os.path.join(FLAGS.wwwpath, 'public_dns_names.txt'))

  def run(self):
    self.connection = self.region.connect()

    ubuntu_server_location = \
        '099720109477/ubuntu/images/ebs/ubuntu-oneiric-11.10-amd64-server-20120222'
    images = self.connection.get_all_images(
      filters={'manifest-location': ubuntu_server_location})
    assert len(images) == 1
    image = images[0]

    logging.info('[%s] Creating Security groups...' % self.region.name)
    security_groups = SecurityGroups(self).create()
    logging.info('[%s] Security groups created: %s.' % \
                   (self.region.name, ', '.join(security_groups)))

    user_data = """#!/bin/bash
set -e -x
export DEBIAN_FRONTEND=noninteractive
apt-get install apache2 python-gflags traceroute tshark -y
a2dissite default

wget http://theseus.news.cs.nyu.edu/generate_apache_site.py
chmod +x ./generate_apache_site.py
wget -O /tmp/example.tar.gz http://theseus.news.cs.nyu.edu/example.tar.gz
tar xf /tmp/example.tar.gz

./generate_apache_site.py -f /var/www/80 -p 80
mv 80 /etc/apache2/sites-available/80
mkdir /var/www/80
cp -r example/* /var/www/80
a2ensite 80

./generate_apache_site.py -f /var/www/34343 -p 34343
mv 34343 /etc/apache2/sites-available/34343
mkdir /var/www/34343
cp -r example/* /var/www/34343
a2ensite 34343
echo "Listen 34343" >> /etc/apache2/ports.conf

wget http://theseus.news.cs.nyu.edu/mod_ssl.so
cp mod_ssl.so /usr/lib/apache2/modules
a2enmod ssl
mkdir -p /etc/apache2/ssl
wget -O /etc/apache2/ssl/selfsigned.crt http://theseus.news.cs.nyu.edu/selfsigned.crt
wget http://theseus.news.cs.nyu.edu/spdy
mv spdy /etc/apache2/sites-available/spdy
mkdir /var/www/spdy
cp -r example/* /var/www/spdy
a2ensite spdy

service apache2 restart
wget http://theseus.news.cs.nyu.edu/libmod_spdy.so
cp libmod_spdy.so /usr/lib/apache2/modules/mod_spdy.so
echo "LoadModule spdy_module /usr/lib/apache2/modules/mod_spdy.so" | tee /etc/apache2/mods-available/spdy.load
echo "SpdyEnabled on" | tee /etc/apache2/mods-available/spdy.conf
a2enmod spdy

service apache2 restart
rm -rf example

wget http://theseus.news.cs.nyu.edu/run_ec2_rpc_server.py
chmod +x run_ec2_rpc_server.py
./run_ec2_rpc_server.py -p %d &
""" % (FLAGS.rpcport)

    # TODO(tierney): Let's have multiple instances on the reservation: one for
    # each browser to test.
    reservation = image.run(min_count=self.num_instances,
                            max_count=self.num_instances,
                            key_name=FLAGS.keypair,
                            user_data = user_data,
                            security_groups=security_groups,
                            instance_type='t1.micro')

    self.instances = reservation.instances
    time_waited = 0
    logging.info('[%s] Launching %d instances.' % (self.region.name, len(self.instances)))
    while True:
      num_running = 0
      for instance in self.instances:
        if 'running' == instance.state:
          num_running += 1
      if len(self.instances) == num_running:
        break

      time_waited += 1
      try:
        for instance in self.instances:
          instance.update()
      except boto.exception.EC2ResponseError:
        pass
      time.sleep(1)

    for instance in self.instances:
      logging.info(' Launched: %s,%s' % (self.region.name,
                                         instance.public_dns_name))
      with open(self.public_dns_names_path, 'a') as fh:
        fh.write('%s,%s\n' % (self.region.name, instance.public_dns_name))
        fh.flush()

    self.state = 'running'

    while not self.stop.is_set():
      time.sleep(1)

    for instance in self.instances:
      name = instance.id
      dns_name = instance.public_dns_name
      instance.terminate()
      time_waited = 0
      logging.info('[%s] Terminating instance %s %s.' % \
                     (self.region.name, name, dns_name))

    while True:
      num_terminated = 0
      for instance in self.instances:
        if 'terminated' == instance.state:
          num_terminated += 1
      if len(self.instances) == num_terminated:
        break

      for instance in self.instances:
        instance.update()

      time.sleep(1)
      time_waited += 1

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
  regions = [region for region in all_regions if region.name in FLAGS.regions]

  logging.info('Working in the following regions: %s.' % \
                 [str(region.name) for region in regions])

  # Clear old public_dns_names file.
  public_dns_path = \
      os.path.expanduser(os.path.join(FLAGS.wwwpath, 'public_dns_names.txt'))
  with open(public_dns_path, 'w') as fh: pass

  # Fire up controllers and the EC2 instances..
  controllers = [Ec2Controller(region, FLAGS.num_instances) for region in regions]
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

  print 'Launched. Initializing setup...'

  # Check for when RPC is ready.
  while True:
    rpc_ready = 0
    waiting_on = []
    num_instances = 0
    for controller in controllers:
      for instance in controller.instances:
        num_instances += 1
        try:
          server = TimeoutServerProxy(
            'http://%s:%d' % (instance.public_dns_name, FLAGS.rpcport),
            timeout = 5)
          if server.ready():
            rpc_ready += 1
        except Exception, e:
          waiting_on.append(instance.public_dns_name)

    sys.stdout.write('Waiting on:    instances\r')
    sys.stdout.write('Waiting on: %2d instances\r' % (len(waiting_on)))
    sys.stdout.flush()
    if num_instances == rpc_ready:
      break
    time.sleep(2)

  sys.stdout.write('Waiting on: (None).          \n')
  sys.stdout.flush()

  # We'll wait for the proper exit command.
  while True:
    command = raw_input('Ready. (Type quit to terminate.)\n')
    if command == 'quit':
      break

  # Clean up everything.
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

  os.remove(public_dns_path)

if __name__=='__main__':
  main(sys.argv)
