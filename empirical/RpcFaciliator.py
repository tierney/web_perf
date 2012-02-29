#!/usr/bin/env python

import sys

from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
  rpc_paths = ('/RPC2',)

# Create server
server = SimpleXMLRPCServer(("thesues.news.cs.nyu.edu", 34343),
                            requestHandler=RequestHandler)
server.register_introspection_functions()

class FileSignalWriter:
  def begin(self):
    with open('BEGIN','w') as fh: pass

  def end(self):
    with open('END','w') as fh: pass

  def halt(self):
    with open('HALT','w') as fh: pass
    sys.exit(0)

server.register_instance(FileSignalWriter())

# Run the server's main loop
server.serve_forever()
