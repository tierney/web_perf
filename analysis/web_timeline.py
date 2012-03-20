#!/usr/bin/env python

import re
import subprocess
import sqlite3

L4_CONVO_FOUR_TUPLE = re.compile(
  '([0-9]+(?:\.[0-9]+){3}):([0-9]+)\ +<-> ([0-9]+(?:\.[0-9]+){3}):([0-9]+)')

filename = 'youtube.pcap'
filename = '/scratch/data/ec2_017/2012-03-15-22-11-23_61ec49b3-9b38-4c36-bbbe-276847e2a67f_ap-northeast-1_tmobile_chrome_80.client.pcap'
decode_as_http = 80
command = 'tshark -n -d tcp.port==%d,http -e frame.number -e frame.len '\
    '-e frame.time_relative -e ip.src -e tcp.srcport -e ip.dst -e tcp.dstport '\
    '-e tcp.flags.syn -e tcp.flags.ack -e http.request.full_uri '\
    '-e http.response.code -T fields -r %s' % (decode_as_http, filename)

class TcpLine(object):
  # Call like this: TcpLine(*(line.split('\t')))
  def __init__(self, frame_num, size, timestamp, src_ip, src_port, dst_ip,
               dst_port, syn, ack, req_uri = None, resp_code = None):
    self.frame_num = frame_num
    self.size = size
    self.timestamp = timestamp
    self.src_ip = src_ip
    self.src_port = src_port
    self.dst_ip = dst_ip
    self.dst_port = dst_port
    self.syn = syn
    self.ack = ack
    self.req_uri = req_uri
    self.resp_code = resp_code

class PcapTimeline(object):
  window_updates = None
  tcp_convos_list = None
  dns_convos_list = None
  conn = sqlite3.connect(':memory:')

  def __init__(self, pcap):
    self.pcap = pcap

  def build_db(self):
    c = self.conn.cursor()
    c.execute('''CREATE TABLE convos (tcp_tuple text, frame_num text, frame_len text,
rel_time text, ip_src text, srcport text, ip_dst text, dstport text, syn text,
ack text, req_uri text, resp_code text)''')

  def _shark_four_tuple(self, a_ip, a_port, b_ip, b_port, tcp=True):
    if tcp: protocol = 'tcp'
    else: protocol = 'udp'
    return ' -R "ip.addr == %s and %s.port == %s and ip.addr == %s '\
        'and %s.port == %s" ' % (a_ip, protocol, a_port, b_ip, protocol, b_port)


  def _window_update(self):
    window_update = subprocess.Popen(
      'tshark -n -d tcp.port==%d,http -e frame.number -T fields -r %s '\
        '-R "tcp.analysis.window_update"' % (decode_as_http, self.pcap),
      shell=True, stdout=subprocess.PIPE)
    self.window_updates = [int(wu.strip()) for wu in
                           window_update.stdout.readlines()]

  def _dns_convos(self):
    convos = subprocess.Popen(
      'tshark -n -z conv,udp -r %s | grep "<->"' % self.pcap, shell=True,
      stdout = subprocess.PIPE)
    convo_tuples = []
    for convo_line in [line.strip() for line in convos.stdout.readlines()]:
      m = re.search(L4_CONVO_FOUR_TUPLE, convo_line)
      if m: convo_tuples.append(m.groups())
    self.dns_convos_list = convo_tuples


  def _tcp_convos(self):
    convos = subprocess.Popen(
      'tshark -n -z conv,tcp -r %s | grep "<->"' % self.pcap, shell=True,
      stdout = subprocess.PIPE)
    convo_tuples = []
    for convo_line in [line.strip() for line in convos.stdout.readlines()]:
      m = re.search(L4_CONVO_FOUR_TUPLE, convo_line)
      if m: convo_tuples.append(m.groups())
    self.tcp_convos_list = convo_tuples


  def dns_convos(self):
    convos = {}
    if not self.dns_convos_list:
      self._dns_convos()

    for four_tuple in self.dns_convos_list:
      a_ip, a_port, b_ip, b_port = four_tuple
      ts_cmd = command + self._shark_four_tuple(
        a_ip, a_port, b_ip, b_port, False)
      print ts_cmd
      ts = subprocess.Popen(ts_cmd, shell=True, stdout=subprocess.PIPE)
      for line in [line.strip() for line in ts.stdout.readlines()]:
        print line
        splitted = line.split('\t')


  def tcp_convos(self):
    convos = {}
    if not self.tcp_convos_list:
      self._tcp_convos()
    for a_ip, a_port, b_ip, b_port in self.tcp_convos_list:
      if (a_ip, a_port, b_ip, b_port) not in convos:
        convos[(a_ip, a_port, b_ip, b_port)] = {}
      ts_cmd = command + self._shark_four_tuple(a_ip, a_port, b_ip, b_port)
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
        print frame_num, frame_time_rel, ip_src, src_port, ip_dst, dst_port, dns_qry, dns_resp
      else:
        frame_num, frame_time_rel, ip_src, src_port, ip_dst, dst_port, \
            dns_qry = splitted
        print frame_num, frame_time_rel, ip_src, src_port, ip_dst, dst_port, dns_qry



pt = PcapTimeline(filename)
pt.build_db()
pt.dns_convos()
pt.tcp_convos()
# pt.dns()

# pt._window_update()
# window_update_frames = _window_update(filename)
