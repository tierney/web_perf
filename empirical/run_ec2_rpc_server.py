#!/usr/bin/env python

import fcntl
import logging

logging.basicConfig(
  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
  filename='rpc_server.log', level=logging.INFO)

import os
import shlex
import signal
import socket
import subprocess
import struct
import sys
import time
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler

import gflags
FLAGS = gflags.FLAGS
gflags.DEFINE_string('interface', 'eth0', 'interface to bind', short_name = 'i')
gflags.DEFINE_integer('port', None, 'port number for XMLRPCServer',
                      short_name = 'p')
gflags.MarkFlagAsRequired('port')

def get_ip_address(ifname):
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  return socket.inet_ntoa(fcntl.ioctl(
    s.fileno(),
    0x8915,  # SIOCGIFADDR
    struct.pack('256s', ifname[:15])
  )[20:24])


# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
  rpc_paths = ('/RPC2',)


class Tcpdump:
  def start(self, timestamp, region, carrier, browser, pipelining, port):
    filename = '%s_%s_%s_%s_%s_%s.server.pcap' % \
        (timestamp, region, carrier, browser, pipelining, port)
    logging.info('Starting tcpdump %s.' % filename)
    tcpdump = subprocess.Popen(
      shlex.split('tcpdump -i %s -w %s' % (FLAGS.interface, filename)))
    return tcpdump.pid

  def stop(self, timestamp, region, carrier, browser, pipelining, port, pid,
           do_traceroute):
    logging.info('Killing %d.' % pid)
    os.kill(pid, signal.SIGKILL)

    filename = '%s_%s_%s_%s_%s_%s.server.pcap' % \
        (timestamp, region, carrier, browser, pipelining, port)

    # Figure out the proxy IP addrs.
    logging.info('Finding conversations.')
    tshark = subprocess.Popen(
      'tshark -r %s -n -z conv,tcp | grep "<->"' % filename,
      shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    logging.info('Parsing IP addrs.')
    local_ip = get_ip_address(FLAGS.interface)
    ret = set()
    for line in tshark.stdout.readlines():
      output = line.strip().split()
      ip_a, port_a = output[0].split(':')
      ip_b, port_b = output[2].split(':')

      if ip_a == local_ip and port_a == port:
        ret.add(ip_b)
      if ip_b == local_ip and port_b == port:
        ret.add(ip_a)

    # Perform traceroute to proxy IPs.
    if do_traceroute:
      logging.info('Tracerouting.')
      tr_files = []
      for ip_addr in ret:
        logging.info('Traceroute: %s.' % (ip_addr))
        tr_file = '%s_%s_%s_%s_%s_%s.server.traceroute' % \
            (timestamp, region, carrier, browser, port, ip_addr)
        tr_files.append(tr_file)
        with open(tr_file, 'w') as tr_fh:
          subprocess.Popen('traceroute %s' % (ip_addr),
                           shell=True, stdout=tr_fh).wait()

    logging.info('Zipping pcap.')
    subprocess.call(['bzip2', filename])
    logging.info('Returning list.')
    return list(ret)

  def ready(self):
    return True


def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  # Create server
  server = SimpleXMLRPCServer((get_ip_address(FLAGS.interface), FLAGS.port),
                              requestHandler=RequestHandler,
                              allow_none = True)
  server.register_introspection_functions()

  server.register_instance(Tcpdump())

  # Run the server's main loop
  server.serve_forever()

if __name__=='__main__':
  main(sys.argv)
