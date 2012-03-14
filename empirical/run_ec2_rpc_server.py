#!/usr/bin/env python

import fcntl
import logging
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
  def start(self, timestamp, uuid, region, carrier, browser, port):
    tcpdump = subprocess.Popen(
      shlex.split('tcpdump -i eth0 -w %s_%s_%s_%s_%s_%s.server.pcap' % \
                    (timestamp, uuid, region, carrier, browser, port)))
    return tcpdump.pid

  def stop(self, timestamp, uuid, region, carrier, browser, port, pid):
    os.kill(pid, signal.SIGKILL)
    subprocess.call(['bzip2', '%s_%s_%s_%s_%s_%s.server.pcap' % \
                       (timestamp, uuid, region, carrier, browser, port)])
    return True

  def ready(self):
    return True


def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  # Create server
  server = SimpleXMLRPCServer((get_ip_address('eth0'), FLAGS.port),
                              requestHandler=RequestHandler,
                              allow_none = True)
  server.register_introspection_functions()

  server.register_instance(Tcpdump())

  # Run the server's main loop
  server.serve_forever()

if __name__=='__main__':
  main(sys.argv)
