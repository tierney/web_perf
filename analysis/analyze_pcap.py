#!/usr/bin/env python

from BaseHTTPServer import BaseHTTPRequestHandler
from cStringIO import StringIO
import BaseHTTPServer
import email.parser
import glob
import gzip
import os
import re
import tarfile
import zlib


DATA = '/home/power/w/mobile-browsing/2012_03_02_05_28_53'
BASE = 'wired_firefox'
TEST = 't-mobile_firefox'

top500 = [
'1and1.com',
'aa.com',
'abc.go.com',
'about.com',
'adultfriendfinder.com',
'alibaba.com',
'amazon.com',
'aol.com',
'apple.com',
'ask.com',
'att.net',
'autotrader.com',
'babycenter.com',
'bankofamerica.com',
'bankrate.com',
'basecamphq.com',
'bhphotovideo.com',
'biblegateway.com',
'bing.com',
'bizrate.com',
'blogger.com',
'blogspot.com',
'businessweek.com',
'buy.com',
'cafemom.com',
'cbs.com',
'cbssports.com',
'charter.net',
'chase.com',
'chicagotribune.com',
'citrixonline.com',
'city-data.com',
'citysearch.com',
'cltrda.com',
'cnn.com',
'comcast.com',
'comcast.net',
'cox.com',
'cracked.com',
'craigslist.org',
'custhelp.com',
'delta.com',
'demonoid.me',
'discovercard.com',
'domaintools.com',
'ebay.com',
'ed.gov',
'eonline.com',
'espn.go.com',
'etsy.com',
'eventbrite.com',
'ew.com',
'ezinearticles.com',
'facebook.com',
'filestube.com',
'flickr.com',
'force.com',
'foxnews.com',
'gizmodo.com',
'go.com',
'godaddy.com',
'goodreads.com',
'google.com',
'googleusercontent.com',
'howstuffworks.com',
'hubspot.com',
'huffingtonpost.com',
'hulu.com',
'icontact.com',
'ikea.com',
'imageshack.us',
'imdb.com',
'imgur.com',
'kat.ph',
'ksl.com',
'lifehacker.com',
'linkedin.com',
'linkwithin.com',
'list-manage.com',
'live.com',
'livestrong.com',
'm-w.com',
'mailchimp.com',
'media.tumblr.com',
'merchantcircle.com',
'mgid.com',
'microsoft.com',
'mint.com',
'mlb.com',
'msn.com',
'mtv.com',
'myfreecams.com',
'nbc.com',
'nbcsports.com',
'netflix.com',
'netteller.com',
'newsmax.com',
'nhl.com',
'noaa.gov',
'nordstrom.com',
'nytimes.com',
'optimum.net',
'optmd.com',
'patch.com',
'paypal.com',
'pbskids.org',
'pinterest.com',
'pnc.com',
'realclearpolitics.com',
'redbox.com',
'reddit.com',
'rottentomatoes.com',
'scout.com',
'scrippsnetworks.com',
'searchqu.com',
'secureserver.net',
'skype.com',
'slate.com',
'soundcloud.com',
'sourceforge.net',
'spankwire.com',
'sprint.com',
't-mobile.com',
't.co',
'tagged.com',
'td.com',
'theblaze.com',
'thedailybeast.com',
'thefreedictionary.com',
'themeforest.net',
'tigerdirect.com',
'toysrus.com',
'travelocity.com',
'tribalfusion.com',
'tumblr.com',
'tvguide.com',
'twitpic.com',
'twitter.com',
'urbandictionary.com',
'usaa.com',
'usmagazine.com',
'victoriassecret.com',
'walgreens.com',
'walmart.com',
'weather.com',
'weebly.com',
'weightwatchers.com',
'wellsfargo.com',
'wikipedia.org',
'wordpress.com',
'worldstarhiphop.com',
'xhamstercams.com',
'xvideoslive.com',
'yahoo.com',
'yelp.com',
'youtube.com',
'zap2it.com',
'zazzle.com',
'zedo.com',
'zimbio.com',
]

def read_chunked(str):
  clen = 0
  body = ''
  rest = str

  while 1:
    len, rest = rest.split('\r\n', 1)
    len = int(len, 16)
    clen += len
    body += rest[:len]
    rest = rest[len + 2:]
    if len == 0:
      break
  return body, rest

def read_http(str):
  while str:
    headers, rest = str.split('\r\n\r\n', 1)
    headers = headers.split('\r\n')
    request, headers = headers[0], headers[1:]
    kvs = [tuple(line.split(': ', 1)) for line in headers]
    headers = dict([(k.lower(), v) for k, v in kvs])

    # if a chunked response, just guess.
    chunked = headers.get('transfer-encoding', None) == 'chunked'
    if chunked:
      body, str = read_chunked(rest)
    else:
      clen = int(headers.get('content-length', 0))
      body = rest[:clen]
      str = rest[clen:]

    if request.startswith('GET'):
      url = request.split(' ')[1]
    else:
      url = ''


    yield url, body

def extract_content(filename):
  contents = {}
  print filename
  with tarfile.open(filename, 'r') as tf:
    # we need to associate request/response streams
    names = set(sorted([f.name for f in tf if f.name.endswith('.dat')]))
    while names:
      req = names.pop()
      prefix, rfrom, rto, suffix = re.search(r'(.*/)([a-z]+)2([a-z]+)(_contents.dat)',
                                             req).groups()
      resp = ''.join([prefix, rto, '2', rfrom, suffix])

      if not resp in names:
        print 'Missing response stream %s' % resp
        continue

      names.remove(resp)

      req_blob = tf.extractfile(req).read()
      if not req_blob.startswith('GET'):
        resp, req = req, resp

      print '::', os.path.basename(req), os.path.basename(resp)
      req_urls = []
      req_blob = tf.extractfile(req).read()
      resp_blob = tf.extractfile(resp).read()

      try:
        req_urls = [url for url, _ in read_http(req_blob)]
        req_urls.reverse()

        for _, body in read_http(resp_blob):
          url = req_urls.pop()
          try:
            body = zlib.decompress(body)
          except Exception:
            pass
          try:
            body = gzip.GzipFile(fileobj=StringIO(body)).read()
          except Exception:
            pass
          contents[url] = body
      except:
        print 'Parsing error for %s' % filename

  return contents

uniq = 0
def clean_url(url):
  url = url[1:].strip()
  if not url:
    global uniq
    uniq += 1
    return 'index.html_%d' % uniq

  return re.sub(r'[^a-zA-Z0-9\.-]', '_', url)[:100]

for site in top500:
  try:
    base_tar = glob.glob('%s/%s_%s*dats.tar.bz2' % (DATA, BASE, site))[0]
    test_tar = glob.glob('%s/%s_%s*dats.tar.bz2' % (DATA, TEST, site))[0]
  except:
    print 'Missing file for %s' % site
  bc = extract_content(base_tar)
  tc = extract_content(test_tar)

  # file paths can often be unique between sessions - index instead based
  # on the content, then look for different keys
  rev_bc = dict([(v, k) for k, v in bc.items()])
  rev_tc = dict([(v, k) for k, v in tc.items()])

  dump_dir = 'diff/%s' % site
  os.system('mkdir %s' % dump_dir)
  for resource, url in sorted(rev_bc.items()):
    if not rev_tc.has_key(resource):
      print 'Missing in TEST: "%s"' % url
      open('%s/base-%s' % (dump_dir, clean_url(url)), 'w').write(resource)

  for resource, url in sorted(rev_tc.items()):
    if not rev_bc.has_key(resource):
      print 'Missing in BASE: "%s"' % url
      open('%s/test-%s' % (dump_dir, clean_url(url)), 'w').write(resource)

