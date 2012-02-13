#!/usr/bin/env python

# cat duration.log  | awk '{print $2 " " $1}' | sort -n | awk '{print $1}' > /tmp/cumulative.log
# cat duration.log | grep verizon  | awk '{print $2 " " $1}' | sort -n | awk '{print $1}' > /tmp/verizon.log
# cat duration.log | grep 't-mobile'  | awk '{print $2 " " $1}' | sort -n | awk '{print $1}' > /tmp/t-mobile.log

import numpy as np
import scikits
import scikits.statsmodels as sm
import matplotlib.pyplot as plt
from scikits.statsmodels import tools

for to_plot in ['cumulative', 'verizon', 't-mobile']:
  with open('/tmp/%s.log' % to_plot) as fh:
    durations = [float(line.strip()) for line in fh.readlines()][:-2]

  ecdf = tools.tools.ECDF(durations)

  x = np.linspace(min(durations), max(durations))
  y = ecdf(x)
  fig = plt.figure()
  plt.title('Alexa Top 230 Sites - Page Load Time CDF (%s)' % to_plot)
  plt.xlabel('Time (seconds) for page to load in Selenium.')
  plt.ylabel('Fraction of pages loading.')
  plt.step(x, y)
  fig.savefig('page_load_cdf_%s.png' % to_plot)
