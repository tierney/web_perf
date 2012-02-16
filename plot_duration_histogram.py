#!/usr/bin/env python

# cat duration.log  | awk '{print $2 " " $1}' | sort -n | awk '{print $1}' > /tmp/cumulative.log
# cat duration.log | grep verizon  | awk '{print $2 " " $1}' | sort -n | awk '{print $1}' > /tmp/verizon.log
# cat duration.log | grep 't-mobile'  | awk '{print $2 " " $1}' | sort -n | awk '{print $1}' > /tmp/t-mobile.log

import numpy as np
import scikits
import scikits.statsmodels as sm
import matplotlib.pyplot as plt
from scikits.statsmodels import tools

# files = ['cumulative','wired','t-mobile']
files = ['cumulative', 'wired','verizon', 't-mobile']
for to_plot in files:
  num_domains = 0
  with open('/tmp/%s.log' % to_plot) as fh:
    durations = []
    for line in fh.readlines()[:-5]:
      try:
        duration = float(line.strip())
        if duration < 1:
          print 'Bad measurement: %s.' % (line)
          continue
        durations.append(duration)
        num_domains += 1
      except ValueError:
        continue

  if to_plot == 'cumulative':
    num_domains /= 2 # number of carriers
    num_domains /= 3 # number of browsers
  else:
    num_domains /= 3 # number of browsers

  ecdf = tools.tools.ECDF(durations)
  try:
    x = np.linspace(min(durations), max(durations))
    y = ecdf(x)
    fig = plt.figure()
    plt.title('Alexa Top ~%d Sites - Page Load Time CDF (%s)' % (num_domains, to_plot))
    plt.xlabel('Time (seconds) for page to load in Selenium.')
    plt.ylabel('Fraction of pages loading.')
    plt.step(x, y)
    fig.savefig('page_load_cdf_%s.png' % to_plot)
  except ValueError:
    print '%s' % to_plot
