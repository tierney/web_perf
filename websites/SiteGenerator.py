#!/usr/bin/env python

# Parameters to control:
# 1. number of objects
# 2. size of objects
# 3. dependencies (add GET javascript RTT)

import logging
import os
import random
import re
import sys
import gflags
from PIL import Image

FLAGS = gflags.FLAGS

gflags.DEFINE_multistring(
  'object_count_dim', None,
  'comma-separated object count and dimension (<count>,<dimension>)',
  short_name = 'o')
gflags.MarkFlagAsRequired('object_count_dim')

class SiteGenerator(object):
  def __init__(self, count_dimensions):
    self.count_dimensions = count_dimensions
    self.generated_images = {}
    self.index_page_html = ''
    self.site_directory = ''
    self.level_javascript = {}

  def _level_javascript(self, level, final_level, dimension):
    output_javascript = '''
if (document.images)
{
%s
}
''' % '\n'.join(
      ['pic%d = new Image(%d,%d);\npic%d.src="%s";' % \
         (i, dimension, dimension, i, name)
       for i, name in enumerate(self.generated_images[level])])
    if not final_level:
      output_javascript += '''loadjscssfile("level_%d.js", "js");''' % \
          (int(level) + 1)
    return output_javascript

  def generate_dependent_requests_javascript(self):
    num_levels = len(self.generated_images.keys())
    final_level = False
    for level in self.generated_images:
      if level + 1 == num_levels:
        final_level = True
      level_js = self._level_javascript(
        level, final_level, self.count_dimensions[level][1])
      level_js_fn = os.path.join(
        self.site_directory, 'level_%d.js' % level)

      with open(level_js_fn, 'w') as fh:
        fh.write(level_js)

  def create_site_directory(self):
    site_directory = ''
    for count, dimension in self.count_dimensions:
      site_directory += '%d_%dx%d_'% (count, dimension, dimension)
    site_directory += 'example'
    if not os.path.exists(site_directory):
      os.mkdir(site_directory)
    self.site_directory = site_directory


  def generate_images(self):
    for level, (count, dimension) in enumerate(self.count_dimensions):
      if level not in self.generated_images:
        self.generated_images[level] = []

      for imagei in range(count):
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
        image_file_name = '%02d_%03d_%d.jpg' % (level, imagei, image_file_size)
        os.rename('image.jpg', os.path.join(self.site_directory,
                                            image_file_name))
        self.generated_images[level].append(image_file_name)


  def generate_index_page(self):
    index_page_html = self._build_index_page_html()
    with open(os.path.join(self.site_directory, 'index.html'),'w') as fh:
      fh.write(index_page_html)

  def _build_index_page_html(self):
    output_html = '''<html>\n<head>\n<title>Example Site</title>
</head>\n<body>'''
    for name in self.generated_images[0]:
      output_html += '''<img src='%s' />\n''' % name

    output_html += '''
  <script type="text/javascript">
  <!--
  function loadjscssfile(filename, filetype){
   if (filetype=="js"){ //if filename is a external JavaScript file
    var fileref=document.createElement('script')
    fileref.setAttribute("type","text/javascript")
    fileref.setAttribute("src", filename)
   }
   else if (filetype=="css"){ //if filename is an external CSS file
    var fileref=document.createElement("link")
    fileref.setAttribute("rel", "stylesheet")
    fileref.setAttribute("type", "text/css")
    fileref.setAttribute("href", filename)
   }
   if (typeof fileref!="undefined")
    document.getElementsByTagName("head")[0].appendChild(fileref)
  };
  //-->
  </script>
  '''
    output_html += '''<script type="text/javascript" src="level_1.js">
</script>'''
    output_html += '''</body>'''
    output_html += '''</html>'''
    return output_html

def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  # Process the object count dimension flags.
  count_dimensions = []
  for count_dimension in FLAGS.object_count_dim:
    count, dimension = count_dimension.split(',')
    count_dimensions.append((int(count),int(dimension)))

  # Generate the site.
  sg = SiteGenerator(count_dimensions)
  sg.create_site_directory()

  sg.generate_images()
  sg.generate_index_page()
  sg.generate_dependent_requests_javascript()


if __name__=='__main__':
  main(sys.argv)
