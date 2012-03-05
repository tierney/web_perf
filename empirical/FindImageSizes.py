#!/usr/bin/env python

import bz2
import os
import shlex
import sqlite3
import subprocess

DIR = '2012_03_02_05_28_53'

files = os.listdir(DIR)
fh_images_count = open('images_count.txt','w')
fh_images_size = open('images_size.txt', 'w')
fh_images_avg = open('images_avg.txt', 'w')

for filename in files:
  if not filename.endswith('.pcap.bz2'):
    continue

  filepath = os.path.join(DIR, filename)
  subprocess.call(['bunzip2', filepath])
  cmd = 'tshark -r %s -T fields -e http.content_length '\
      '-e http.content_type -R http.response' % (filepath.replace('.bz2',''))
  tshark = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE)

  tshark_lines = tshark.stdout.readlines()
  image_count = 0
  sum_image_sizes = 0
  for size_type in tshark_lines:
    size_content_type = size_type.rstrip().split('\t')
    if len(size_content_type) != 2:
      continue

    size, content_type = size_content_type
    if not size or int(size) <= 0:
      continue

    if content_type.startswith('image'):
      fh_images_size.write('%s\n' % size)
      fh_images_size.flush()
      image_count += 1
      sum_image_sizes += int(size)

  fh_images_count.write('%d\n' % image_count)
  fh_images_count.flush()

  image_avg_size = 0.0
  if image_count > 0:
    image_avg_size = ((1. * sum_image_sizes) / image_count)
  fh_images_avg.write('%f\n' % image_avg_size)
  fh_images_avg.flush()

  subprocess.call(['bzip2', filepath.replace('.bz2','')])

fh_images_count.close()
fh_images_size.close()
fh_images_avg.close()
