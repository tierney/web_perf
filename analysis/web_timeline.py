#!/usr/bin/env python

import re
import subprocess
import sqlite3

TCP_CONVO_FOUR_TUPLE = re.compile(
  '([0-9]+(?:\.[0-9]+){3}):([0-9]+)\ +<-> ([0-9]+(?:\.[0-9]+){3}):([0-9]+)')

filename = 'youtube.pcap'
decode_as_http = 80
command = 'tshark -n -d tcp.port==%d,http -e frame.number -e frame.len '\
    '-e frame.time_relative -e ip.src -e tcp.srcport -e ip.dst -e tcp.dstport '\
    '-e tcp.flags.syn -e tcp.flags.ack -e http.request.full_uri '\
    '-e http.response.code -T fields -r %s' % (decode_as_http, filename)


class PcapTimeline(object):
  window_updates = None
  tcp_convos = None
  conn = sqlite3.connect('timeline.sqlite')

  def __init__(self, pcap):
    self.pcap = pcap

  def build_db(self):
    c = self.conn.cursor()
    c.execute('''CREATE TABLE convos (tcp_tuple text, frame_num text, frame_len text,
rel_time text, ip_src text, srcport text, ip_dst text, dstport text, syn text,
ack text, req_uri text, resp_code text)''')

  def _shark_tcp_tuple(self, a_ip, a_port, b_ip, b_port):
    return ' -R "ip.addr == %s and tcp.port == %s and ip.addr == %s '\
        'and tcp.port == %s" ' % (a_ip, a_port, b_ip, b_port)


  def _window_update(self):
    window_update = subprocess.Popen(
      'tshark -n -d tcp.port==%d,http -e frame.number -T fields -r %s '\
        '-R "tcp.analysis.window_update"' % (decode_as_http, self.pcap),
      shell=True, stdout=subprocess.PIPE)
    self.window_updates = [int(wu.strip()) for wu in
                           window_update.stdout.readlines()]


  def tcp_convos(self):
    convos = subprocess.Popen(
      'tshark -n -z conv,tcp -r %s | grep "<->"' % self.pcap, shell=True,
      stdout = subprocess.PIPE)
    convo_tuples = []
    for convo_line in [line.strip() for line in convos.stdout.readlines()]:
      m = re.search(TCP_CONVO_FOUR_TUPLE, convo_line)
      if m: convo_tuples.append(m.groups())
    self.tcp_convos = convo_tuples


  def convos(self):
    convos = {}
    for a_ip, a_port, b_ip, b_port in self.tcp_convos:
      if (a_ip, a_port, b_ip, b_port) not in convos:
        convos[(a_ip, a_port, b_ip, b_port)] = {}
      ts_cmd = command + self._shark_tcp_tuple(a_ip, a_port, b_ip, b_port)
      print ts_cmd
      tcp_tuple = str((a_ip, a_port, b_ip, b_port))
      ts = subprocess.Popen(ts_cmd, shell=True, stdout=subprocess.PIPE)
      for line in [line.strip() for line in ts.stdout.readlines()]:
        print line
        splitted = line.split('\t')
        if 9 == len(splitted):
          frame_num, frame_len, rel_time, ip_src, srcport, ip_dst, dstport, syn, ack = splitted
          self.conn.execute('''insert into convos (tcp_tuple, frame_num, frame_len,
rel_time, ip_src, srcport, ip_dst, dstport, syn, ack) values (?, ?, ?, ?, ?,
?, ?, ?, ?, ?)''', (tcp_tuple, frame_num, frame_len, rel_time, ip_src, srcport, ip_dst,
                    dstport, syn, ack))
        elif 10 == len(splitted):
          frame_num, frame_len, rel_time, ip_src, srcport, ip_dst, dstport, syn, ack, req_uri = splitted
          self.conn.execute('''insert into convos (tcp_tuple, frame_num, frame_len,
rel_time, ip_src, srcport, ip_dst, dstport, syn, ack, req_uri) values (?, ?, ?, ?, ?,
?, ?, ?, ?, ?, ?)''', (tcp_tuple, frame_num, frame_len, rel_time, ip_src, srcport, ip_dst,
                       dstport, syn, ack, req_uri))
        elif 11 == len(splitted):
          frame_num, frame_len, rel_time, ip_src, srcport, ip_dst, dstport, syn, ack, req_uri, resp_code = splitted
          self.conn.execute('''insert into convos (tcp_tuple, frame_num, frame_len,
rel_time, ip_src, srcport, ip_dst, dstport, syn, ack, req_uri, resp_code) values (?, ?, ?, ?, ?,
?, ?, ?, ?, ?, ?, ?)''', (tcp_tuple, frame_num, frame_len, rel_time, ip_src, srcport, ip_dst,
                          dstport, syn, ack, req_uri, resp_code))
      self.conn.commit()

  def dns(self):
    dns_shark = 'tshark -e frame.number -e frame.time_relative -e ip.src '\
        '-e udp.srcport -e ip.dst -e udp.dstport  -e dns.qry.name '\
        '-e dns.resp.addr -T fields dns -r %s' % (self.pcap)
    dns = subprocess.Popen(dns_shark, shell=True, stdout=subprocess.PIPE)
    lines = [line.strip() for line in dns.stdout.readlines()]
    for line in lines:
      splitted = line.split('\t')
      if len(splitted) == 8:
        frame_num, frame_time_rel, ip_src, src_port, ip_dst, dst_port, \
            dns_qry, dns_resp = splitted
      else:
        frame_num, frame_time_rel, ip_src, src_port, ip_dst, dst_port, \
            dns_qry = splitted

      print frame_num, frame_time_rel, ip_src, src_port, ip_dst, dst_port, dns_qry

pt = PcapTimeline(filename)
pt.build_db()
pt.tcp_convos()
pt.convos()
pt.dns()

# pt._window_update()
# window_update_frames = _window_update(filename)


