#!/usr/bin/env python

import logging
import sys
import gflags

FLAGS = gflags.FLAGS

gflags.DEFINE_string('filepath', None, 'site directory path (abspath)',
                     short_name = 'f')
gflags.DEFINE_integer('port', None, 'port for site to listen on',
                      short_name = 'p')

gflags.MarkFlagAsRequired('filepath')
gflags.MarkFlagAsRequired('port')


def generate_site_file(filepath, port):
  site_file = '''<VirtualHost *:%(port)d>
	ServerAdmin webmaster@localhost

	DocumentRoot %(filepath)s
	<Directory />
		Options FollowSymLinks
		AllowOverride None
	</Directory>
	<Directory %(filepath)s/>
		Options Indexes FollowSymLinks MultiViews
		AllowOverride None
		Order allow,deny
		allow from all
	</Directory>

	ScriptAlias /cgi-bin/ /usr/lib/cgi-bin/
	<Directory "/usr/lib/cgi-bin">
		AllowOverride None
		Options +ExecCGI -MultiViews +SymLinksIfOwnerMatch
		Order allow,deny
		Allow from all
	</Directory>

	ErrorLog ${APACHE_LOG_DIR}/error_%(port)d.log

	# Possible values include: debug, info, notice, warn, error, crit,
	# alert, emerg.
	LogLevel warn

	CustomLog ${APACHE_LOG_DIR}/access_%(port)d.log combined

    Alias /doc/ "/usr/share/doc/"
    <Directory "/usr/share/doc/">
        Options Indexes MultiViews FollowSymLinks
        AllowOverride None
        Order deny,allow
        Deny from all
        Allow from 127.0.0.0/255.0.0.0 ::1/128
    </Directory>

</VirtualHost>
''' % locals()
  return site_file


def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  site_file = generate_site_file(FLAGS.filepath, FLAGS.port)
  with open('%d' % FLAGS.port, 'w') as fh:
    fh.write(site_file)


if __name__=='__main__':
  main(sys.argv)
