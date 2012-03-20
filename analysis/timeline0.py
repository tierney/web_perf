"""
Light Pink - DNS
Dark Pink - DNS
Blue - GET (outgoing)
Green - response (incoming)
Light Gray - ACK
Dark Gray - SYNACK
Red - Retransmission

"""
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, MinuteLocator, SecondLocator
import numpy as np
from StringIO import StringIO
import datetime as dt

a = StringIO("""
Convo 8.163473000	8.260164000	SYNACK
Convo 8.260488000	8.360089000	GET
Convo 8.434873000 8.434873000	RESP
Convo 8.434915000 8.434915000	ACK
Convo 8.434933000	8.434933000 RESP
Convo 8.434941000 8.434941000	ACK
Convo 12.473271000 12.761878000	GET
Convo 12.761895000	12.761895000 ACK
Convo 12.775673000	12.775673000 RESP
Convo 12.775692000	12.775692000 ACK
Convo 12.784929000	12.784929000 RESP
Convo 12.784933000	12.784933000 ACK
Convo 13.707613000	13.707613000 ACK
""")

data=np.genfromtxt(a, converters={1: float,2: float},
                   names=['caption','start','stop','state'], dtype=None)
cap, start, stop=data['caption'], data['start'], data['stop']
print cap, start, stop

synack = (data['state'] == 'SYNACK')
get = (data['state'] == 'GET')
resp = (data['state'] == 'RESP')
ack = (data['state'] == 'ACK')

print ack
captions, unique_idx, caption_inv = np.unique(cap, 1,1)
print captions, unique_idx, caption_inv

y=(caption_inv+1)/float(len(captions)+1)

def timelines(y, xstart, xstop,color='b'):
  """Plot timelines at y from xstart to xstop with given color."""
  plt.hlines(y,xstart,xstop,color, lw=4)
  plt.vlines(xstart, y+0.03,y-0.03, color,lw=1)
  plt.vlines(xstop, y+0.03,y-0.03,color, lw=1)

timelines(y[synack],start[synack],stop[synack],'black')
timelines(y[get],start[get],stop[get],'blue')
timelines(y[resp],start[resp],stop[resp],'green')
timelines(y[ack],start[ack],stop[ack],'gray')

#Setup the plot
ax=plt.gca()
delta=(stop.max()-start.min()) / 10

plt.yticks(y[unique_idx],captions)
plt.ylim(0,1)
plt.xlim(start.min() - delta, stop.max() + delta)
plt.xlabel('Time')
plt.show()
