#!/usr/bin/env python

import logging
import sys
import threading
import xmlrpclib

import gflags

FLAGS = gflags.FLAGS

gflags.DEFINE_string('host', None, 'XMLRPC Server host address',
                     short_name = 'h')
gflags.DEFINE_string('port', None, 'XMLRPC Server port', short_name = 'p')

gflags.DEFINE_string('command', None, 'Command to send (begin, end, halt)',
                     short_name = 'c')

gflags.RegisterValidator(
  'command', lambda x: x in ['begin', 'end', 'halt'],
  'Unknown command name (must be "begin","end", or "halt").')
gflags.MarkFlagAsRequired('host')
gflags.MarkFlagAsRequired('port')

class Client(threading.Thread):
  def __init__(self, host, port, command):
    self.host = host
    self.port = port
    self.command = command
    threading.Thread.__init__(self)

  def run(self):
    proxy = xmlrpclib.ServerProxy('http://%s:%s' % (self.host, self.port))
    if 'begin' == self.command: proxy.begin()
    if 'end' == self.command: proxy.end()
    if 'halt' == self.command: proxy.halt()

def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  c = Client(FLAGS.host, FLAGS.port, FLAGS.command)
  c.start()

if __name__=='__main__':
  main(sys.argv)
