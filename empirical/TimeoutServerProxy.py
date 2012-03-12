import httplib
import xmlrpclib

class TimeoutHTTPConnection(httplib.HTTPConnection):
  def __init__(self,host,timeout=10):
    httplib.HTTPConnection.__init__(self, host, timeout=timeout)

class TimeoutTransport(xmlrpclib.Transport):
  def __init__(self, timeout=10, *l, **kw):
    xmlrpclib.Transport.__init__(self,*l,**kw)
    self.timeout=timeout

  def make_connection(self, host):
    conn = TimeoutHTTPConnection(host,self.timeout)
    return conn

class TimeoutServerProxy(xmlrpclib.ServerProxy):
  def __init__(self,uri,timeout=10,*l,**kw):
    kw['transport'] = TimeoutTransport(
       timeout = timeout, use_datetime = kw.get('use_datetime', 0))
    xmlrpclib.ServerProxy.__init__(self,uri,*l,**kw)
