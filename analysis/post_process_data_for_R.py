#!/usr/bin/env python
import Queue
import csv
import logging
import os
import re
import subprocess
import sys
import threading
import time
from numpy import std,var,median,mean
import gflags

EXCLUDE_LABELS = ['SYN', 'FIN']
MEDIA_TYPE = re.compile('(.*)\/([a-zA-Z\-\+]*);*(.*)')

FLAGS=gflags.FLAGS

gflags.DEFINE_string('read', None, 'file to read', short_name='r')
gflags.DEFINE_string('write', None, 'file to write', short_name='w')

gflags.MarkFlagAsRequired('read')

# x-x
# JavaScript
# jpeg
# svg+xml
# ocsp-response
# unix-directory
# xml
# x-shockwave-flash
# unknown
# json
# gif
# octet-stream
# html
# x-woff
# css
# vnd
# javascript
# JPEG
# GIF
# jpg
# x-amf
# png
# plain
# opensearchdescription+xml
# x-cross-domain-policy
# x-javascript
# x-fcs
# x-flv
# x-multiad-json
# x-icon

def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  dr = csv.DictReader(open(FLAGS.read, 'rb'), delimiter=',')

  labels = set()
  for row in dr:
    _label = row['label']
    if _label in EXCLUDE_LABELS:
      continue
    labels.add(_label)
  print labels

  media_types = set()
  subtypes = set()
  for label in labels:
    m = re.search(MEDIA_TYPE, label)
    if m:
      media_type, subtype, parameter = m.groups()
      media_types.add(media_type)
      subtypes.add(subtype)
  print media_types
  print subtypes
  for subtype in subtypes:
    print subtype

if __name__=='__main__':
  main(sys.argv)
