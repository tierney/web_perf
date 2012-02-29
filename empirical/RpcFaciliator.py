#!/usr/bin/env python

import sys
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler

import gflags

FLAGS = gflags.FLAGS

gflags.DEFINE_string('host', None, 'host address for XMLRPCServer',
                     short_name = 'h')
gflags.DEFINE_integer('port', None, 'port number for XMLRPCServer',
                      short_name = 'p')
gflags.MarkFlagAsRequired('host')
gflags.MarkFlagAsRequired('port')

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
  rpc_paths = ('/RPC2',)

class FileSignalWriter:
  def begin(self, uuid):
    with open('BEGIN','w') as fh:
      fh.write(uuid)
    return True

  def end(self):
    with open('END','w') as fh: pass
    return True

  def halt(self):
    with open('HALT','w') as fh: pass
    sys.exit(0)

def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  # Create server
  server = SimpleXMLRPCServer((FLAGS.host, FLAGS.port),
                              requestHandler=RequestHandler,
                              allow_none = True)
  server.register_introspection_functions()

  server.register_instance(FileSignalWriter())

  # Run the server's main loop
  server.serve_forever()

if __name__=='__main__':
  main(sys.argv)
