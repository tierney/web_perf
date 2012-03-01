#!/usr/bin/env python

import logging
import sys
import threading
import xmlrpclib

class Client(object):
  def __init__(self, host, port, command, uuid = None):
    self.host = host
    self.port = port
    self.command = command
    self.uuid = uuid

  def run(self):
    logging.debug('Sending %s to http://%s:%s.' % \
                    (self.command, self.host, self.port))
    proxy = xmlrpclib.ServerProxy('http://%s:%s' % (self.host, self.port),
                                  allow_none = True)
    if 'begin' == self.command:
      proxy.begin(self.uuid)
    if 'end' == self.command:
      proxy.end()
    if 'halt' == self.command:
      proxy.halt()

    return
