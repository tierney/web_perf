#!/usr/bin/env python

import sys
import logging

import BaseHTTPServer, select, socket, SocketServer, urlparse, urllib2
from BaseHTTPServer import BaseHTTPRequestHandler
import re
import os
import urllib

from proactive_cache import ProactiveCache

RESOURCE_RE = re.compile(r'''(?:href|src)=['"]([^'"]+\.(?:pdf|jpeg|jpg|png|css|js|xml|gif))['"]''')
VERSION = 'Python Proxy/tierney'


def extract_resources(document):
  return set(RESOURCE_RE.findall(document))


class ProxyHandler (BaseHTTPRequestHandler):
  protocol_version = 'HTTP/1.1'
  proactive_cache = ProactiveCache()
  proactive_cache.start()

  def do_GET(self):
    (scm, netloc, path, params, query, fragment) = urlparse.urlparse(
      self.path, 'http')
    if scm != 'http' or fragment or not netloc:
      self.send_error(400, "bad url %s" % self.path)
      return

    url = urlparse.urlunparse((scm, netloc, path, params, query, fragment))
    blob = self.proactive_cache.get(url)
    if not blob:
      self.log_message('MISS on %s.' % urllib.unquote(url)) 
      connection = urllib2.urlopen(url)
      blob = connection.read()
    else:
      self.log_message('HIT on %s.' % urllib.unquote(url))
      
    extracted = extract_resources(blob)
    if extracted:
      for extracted_path in extracted:
        self.proactive_cache.put(netloc, path, extracted_path)
      
#    headers = connection.info()
#    connection.close()
    self.send_response(200)
    self.send_header('Content-Length', len(blob))
    self.end_headers()
    self.wfile.write(blob)

  def _connect_target(self, host):
    i = host.find(':')
    if i!=-1:
      port = int(host[i+1:])
      host = host[:i]
    else:
      port = 80
    (soc_family, _, _, _, address) = socket.getaddrinfo(host, port)[0]
    self.target = socket.socket(soc_family)
    self.target.connect(address)

  def do_CONNECT(self):
    self._connect_target(self.path)
    self.send_response(200)
    self.send_header('Proxy-agent', VERSION)
    self.client_buffer = ''
    self._read_write()
    
  def _read_write(self):
    time_out_max = self.timeout/3
    socs = [self.client, self.target]
    count = 0
    while 1:
      count += 1
      (recv, _, error) = select.select(socs, [], socs, 3)
      if error:
        break
      if recv:
        for in_ in recv:
          data = in_.recv(BUFLEN)
          if in_ is self.client:
            out = self.target
          else:
            out = self.client
          if data:
            out.send(data)
            count = 0
      if count == time_out_max:
        break

  do_HEAD = do_GET
  do_POST = do_GET
  do_PUT = do_GET
  do_DELETE = do_GET

class ThreadingHTTPServer (SocketServer.ThreadingMixIn,
                           BaseHTTPServer.HTTPServer): pass

if __name__ == '__main__':
  from sys import argv
  host = '216.165.108.71'
  port = 34343
  t = ThreadingHTTPServer((host, port), ProxyHandler)
  print "Listening at %s:%d" % (host, port)
  t.serve_forever()
