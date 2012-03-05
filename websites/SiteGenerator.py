#!/usr/bin/env python

# Parameters to control:
# 1. number of objects
# 2. size of objects
# 3. dependencies (javascript RTT)

import logging
import os
import random
import re
import sys
import gflags
from PIL import Image

FLAGS = gflags.FLAGS

gflags.DEFINE_multistring(
  'objectns', None,
  'comma-separated object number and dimension (<num>,<dimension>)',
  short_name = 'o')
gflags.MarkFlagAsRequired('objectns')


def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  num_dimensions = []
  for num_dimension in FLAGS.objectns:
    num, dimension = num_dimension.split(',')
    num_dimensions.append((int(num),int(dimension)))

  print num_dimensions
  for num, dimension in num_dimensions:
    print num, dimension

    for n in range(num):
      im = Image.new('RGBA', (int(dimension), int(dimension)))

      putpixel = im.im.putpixel
      for i in range(dimension):
        for j in range(dimension):
          red = random.randint(0,256)
          green = random.randint(0,256)
          blue = random.randint(0,256)
          putpixel((i,j), (red, green, blue))

      im.save('image.jpg')
      image_file_size = os.path.getsize('image.jpg')
      os.rename('image.jpg', '%03d_%d.jpg' % (n, image_file_size))


if __name__=='__main__':
  main(sys.argv)
