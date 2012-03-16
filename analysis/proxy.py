#!/usr/bin/env python

import BaseHTTPServer, select, socket, SocketServer, urlparse, urllib2
from BaseHTTPServer import BaseHTTPRequestHandler

import re
RESOURCE_RE = re.compile(r'''(?:href|src)=['"]([^'"]+\.(?:pdf|jpeg|jpg|png|css|js|xml|gif))['"]''')

def extract_resources(document):
  return set(RESOURCE_RE.findall(document))

class ProxyHandler (BaseHTTPRequestHandler):
  protocol_version = 'HTTP/1.1'

  def do_GET(self):
    (scm, netloc, path, params, query, fragment) = urlparse.urlparse(
      self.path, 'http')
    if scm != 'http' or fragment or not netloc:
      self.send_error(400, "bad url %s" % self.path)
      return

    url = urlparse.urlunparse((scm, netloc, path, params, query, fragment))
    connection = urllib2.urlopen(url)
    blob = connection.read()

    print extract_resources(blob)
    headers = connection.info()
    connection.close()
    self.send_response(200)
    self.send_header('Content-Length', len(blob))
    self.end_headers()
    self.wfile.write(blob)


  do_HEAD = do_GET
  do_POST = do_GET
  do_PUT = do_GET
  do_DELETE = do_GET

class ThreadingHTTPServer (SocketServer.ThreadingMixIn,
                           BaseHTTPServer.HTTPServer): pass

if __name__ == '__main__':
  from sys import argv
  t = ThreadingHTTPServer(('127.0.0.1', 8080),
                          ProxyHandler)
  t.serve_forever()
