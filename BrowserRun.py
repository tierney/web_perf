#!/usr/bin/env python

import gflags
import sys
from selenium import webdriver

FLAGS = gflags.FLAGS

gflags.DEFINE_boolean('debug', False, 'produces debugging output')
gflags.DEFINE_string('browser', None, 'Browser to use..')
gflags.DEFINE_string('domain', None, 'Domain to HTTP GET.')

gflags.MarkFlagAsRequired('browser')
gflags.MarkFlagAsRequired('domain')

class BrowserRun(object):
  def __init__(self, browser, domain):
    self.browser = browser
    self.domain = domain

  def _browser(self):
    browser_driver = None
    try:
      if 'chrome' == self.browser:
        browser_driver = webdriver.Chrome()
      elif 'firefox' == self.browser:
        browser_driver = webdriver.Firefox()
      elif 'android' == self.browser:
        # Restart the android selenium app before trying to call into it.
        subprocess.call(
          ['/home/tierney/repos/android/android-sdk-linux/platform-tools/adb',
           '-s','emulator-5554','shell','am','start','-S','-a',
           'android.intent.action.MAIN','-n',
           'org.openqa.selenium.android.app/.MainActivity'])
        time.sleep(2)
        subprocess.call(
          ['/home/tierney/repos/android/android-sdk-linux/platform-tools/adb',
           '-s','emulator-5554','forward','tcp:8080','tcp:8080'])
        time.sleep(2)
        browser_driver = webdriver.Remote("http://localhost:8080/wd/hub",
                                webdriver.DesiredCapabilities.ANDROID)
    except socket.error, e:
      logging.error("webdriver connection error (%s): %s." % \
                      (self.browser, str(e)))
    except Exception, e:
      logging.error("webdriver error (%s): %s." % (self.browser, str(e)))
    return browser_driver

  def start(self):
    browser = self._browser()
    browser.get('http://' + self.domain)
    browser.quit()

def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)
  if FLAGS.debug:
    logging.info('non-flag arguments:', argv)

  t = BrowserRun(FLAGS.browser, FLAGS.domain)
  t.start()

if __name__=='__main__':
  main(sys.argv)
