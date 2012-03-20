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

b = StringIO("""
192.168.42.196:38829<->74.125.65.9380 5.178600000 5.533309000 SYNACK
192.168.42.196:38829<->74.125.65.9380 5.533374000 5.533374000 ACK
192.168.42.196:38829<->74.125.65.9380 5.533580000 5.874572000 GET
192.168.42.196:38829<->74.125.65.9380 6.623299000 6.623299000 RESP
192.168.42.196:38829<->74.125.65.9380 8.002547000 8.002547000 RESP
192.168.42.196:38829<->74.125.65.9380 8.002588000 8.002588000 ACK
192.168.42.196:38829<->74.125.65.9380 8.011734000 8.011734000 RESP
192.168.42.196:38829<->74.125.65.9380 8.011783000 8.011783000 ACK
192.168.42.196:38829<->74.125.65.9380 8.011849000 8.011849000 RESP
192.168.42.196:38829<->74.125.65.9380 8.011865000 8.011865000 ACK
192.168.42.196:38829<->74.125.65.9380 8.011877000 8.011877000 RESP
192.168.42.196:38829<->74.125.65.9380 8.011889000 8.011889000 ACK
192.168.42.196:38829<->74.125.65.9380 8.011899000 8.011899000 RESP
192.168.42.196:38829<->74.125.65.9380 8.011908000 8.011908000 ACK
192.168.42.196:38829<->74.125.65.9380 8.020482000 8.020482000 RESP
192.168.42.196:38829<->74.125.65.9380 8.020502000 8.020502000 ACK
192.168.42.196:38829<->74.125.65.9380 8.020510000 8.020510000 RESP
192.168.42.196:38829<->74.125.65.9380 8.020512000 8.020512000 ACK
192.168.42.196:38829<->74.125.65.9380 8.020515000 8.020515000 RESP
192.168.42.196:38829<->74.125.65.9380 8.020517000 8.020517000 ACK
192.168.42.196:38829<->74.125.65.9380 8.020519000 8.020519000 RESP
192.168.42.196:38829<->74.125.65.9380 8.020521000 8.020521000 ACK
192.168.42.196:38829<->74.125.65.9380 8.031074000 8.031074000 RESP
192.168.42.196:38829<->74.125.65.9380 8.031098000 8.031098000 RESP
192.168.42.196:38829<->74.125.65.9380 8.031102000 8.031102000 ACK
192.168.42.196:38829<->74.125.65.9380 8.031111000 8.031111000 ACK
192.168.42.196:38829<->74.125.65.9380 8.031212000 8.031212000 RESP
192.168.42.196:38829<->74.125.65.9380 8.031220000 8.031220000 ACK
192.168.42.196:38829<->74.125.65.9380 8.031225000 8.031225000 RESP
192.168.42.196:38829<->74.125.65.9380 8.031229000 8.031229000 ACK
192.168.42.196:38829<->74.125.65.9380 8.031232000 8.031232000 RESP
192.168.42.196:38829<->74.125.65.9380 8.031235000 8.031235000 ACK
192.168.42.196:38829<->74.125.65.9380 8.039857000 8.039857000 RESP
192.168.42.196:38829<->74.125.65.9380 8.039887000 8.039887000 ACK
192.168.42.196:38829<->74.125.65.9380 8.049991000 8.049991000 RESP
192.168.42.196:38829<->74.125.65.9380 8.050007000 8.050007000 ACK
192.168.42.196:38829<->74.125.65.9380 8.050028000 8.050028000 RESP
192.168.42.196:38829<->74.125.65.9380 8.050041000 8.050041000 ACK
192.168.42.196:38829<->74.125.65.9380 8.122910000 8.122910000 RESP
192.168.42.196:38829<->74.125.65.9380 8.122952000 8.122952000 ACK
192.168.42.196:38829<->74.125.65.9380 8.122972000 8.122972000 RESP
192.168.42.196:38829<->74.125.65.9380 8.122979000 8.122979000 ACK
192.168.42.196:38829<->74.125.65.9380 8.130233000 8.130233000 RESP
192.168.42.196:38829<->74.125.65.9380 8.130265000 8.130265000 ACK
192.168.42.196:38829<->74.125.65.9380 13.707514000 13.707514000 ACK""")

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
print 'Done'
