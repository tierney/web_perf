#!/usr/bin/env python

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, MinuteLocator, SecondLocator
import numpy as np
from StringIO import StringIO
import datetime as dt

### The example data
a=StringIO("""a 10:15:22 10:15:30 OK
b 10:15:23 10:15:28 OK
c 10:16:00 10:17:10 FAILED
b 10:16:30 10:16:50 OK
""")

#Converts str into a datetime object.
conv=lambda s:dt.datetime.strptime(s,'%H:%M:%S')

#Use numpy to read the data in.
data=np.genfromtxt(a, converters={1: conv,2: conv},
                   names=['caption','start','stop','state'], dtype=None)
cap, start, stop=data['caption'], data['start'], data['stop']

#Check the status, because we paint all lines with the same color
#together
is_ok= (data['state']=='OK')
not_ok=np.logical_not(is_ok)

#Get unique captions and there indices and the inverse mapping
captions, unique_idx, caption_inv = np.unique(cap, 1,1)
print captions, unique_idx, caption_inv

#Build y values from the number of unique captions.
y=(caption_inv+1)/float(len(captions)+1)

#Plot function
def timelines(y, xstart, xstop,color='b'):
  """Plot timelines at y from xstart to xstop with given color."""
  plt.hlines(y,xstart,xstop,color,lw=4)
  plt.vlines(xstart, y+0.03,y-0.03,color,lw=2)
  plt.vlines(xstop, y+0.03,y-0.03,color,lw=2)

#Plot ok tl black
timelines(y[is_ok],start[is_ok],stop[is_ok],'k')
#Plot fail tl red
timelines(y[not_ok],start[not_ok],stop[not_ok],'r')

#Setup the plot
ax=plt.gca()
ax.xaxis_date()
myFmt = DateFormatter('%H:%M:%S')
ax.xaxis.set_major_formatter(myFmt)
ax.xaxis.set_major_locator(SecondLocator(interval=20))

#To adjust the xlimits a timedelta is needed.
delta=(stop.max()-start.min()) / 10

plt.yticks(y[unique_idx],captions)
plt.ylim(0,1)
plt.xlim(start.min() - delta, stop.max() + delta)
plt.xlabel('Time')
plt.show()
