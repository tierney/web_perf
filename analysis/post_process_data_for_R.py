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

MEDIA_TYPE = re.compile('(.*)\/([a-zA-Z\-\+]*);*(.*)')

FLAGS=gflags.FLAGS

gflags.DEFINE_string('read', None, 'file to read', short_name='r')
gflags.DEFINE_string('write', None, 'file to write', short_name='w')

gflags.MarkFlagAsRequired('read')

GENERAL_SUBTYPES = {
  'JavaScript' : 'javascript',
  'jpeg': 'jpeg',
  'gif' : 'gif',
  'javascript' : 'javascript',
  'JPEG' : 'jpeg',
  'GIF' : 'gif',
  'jpg' : 'jpeg',
}

MEDIA_TYPES = {
  'text/JavaScript' : 'text/javascript',
  'image/JPEG' : 'image/jpeg',
  'image/jpg' : 'image/jpeg',
  'image/GIF' : 'image/gif',
}

def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  dr = csv.DictReader(open(FLAGS.read, 'rb'), delimiter=',')

  full_labels = set()
  labels = set()
  for row in dr:
    _label = row['label']
    abbrev_label = _label

    full_labels.add(_label)

    m = re.search(MEDIA_TYPE, _label)
    if m:
      media_type, subtype, parameter = m.groups()
      abbrev_label = '/'.join((media_type, subtype))
    labels.add((_label, abbrev_label))

  for _ in labels:
    (key, value) = _
    if value in MEDIA_TYPES:
      value = MEDIA_TYPES.get(value)
    print '"%s"="%s",' % (key, value)

    # if _ in MEDIA_TYPES:
    #   value = MEDIA_TYPES.get(_)
    # print '"%s"="%s",' % (_, value)

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
    if subtype in GENERAL_SUBTYPES:
      print GENERAL_SUBTYPES[subtype]
    else:
      print subtype

  for _ in full_labels:
    print _
if __name__=='__main__':
  main(sys.argv)
