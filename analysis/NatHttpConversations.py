#!/usr/bin/env python

import gflags
import logging
import re
import shlex
import subprocess
import sys

TCP_CONVO_FOUR_TUPLE = re.compile(
  '([0-9]+(?:\.[0-9]+){3}):([0-9]+)\ +<-> ([0-9]+(?:\.[0-9]+){3}):([0-9]+)')
TCP_IP_ADDRS = re.compile(
  '([0-9]+(?:\.[0-9]+){3})\ +-> ([0-9]+(?:\.[0-9]+){3})')

PORTS = ['80', '443', '34343']

FLAGS = gflags.FLAGS
gflags.DEFINE_string('fileprefix', None, 'prefix for client and server pcap files', short_name = 'p')
gflags.DEFINE_integer('httpport', 80, 'port to decode as http', short_name = 'h')
gflags.DEFINE_string('client_filename', None, 'client-side pcap file name', short_name = 'c')
gflags.DEFINE_string('server_filename', None, 'server-side pcap file name', short_name = 's')
gflags.DEFINE_boolean('conv_backwards', False, '-z conv,tcp', short_name = 'b')

class ConvoParser(object):
  def __init__(self, client_filename, server_filename, port_http = 80):
    self.client_filename = client_filename
    self.server_filename = server_filename
    self.port_http = port_http

  def client_convos(self):
    return self.convo(self.client_filename, True)

  def server_convos(self):
    return self.convo(self.server_filename, False)

  def convo(self, filename, client):
    convos = subprocess.Popen(
      shlex.split('tshark -r %s -z conv,tcp -n' % filename),
      stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    convos_file_time = {}
    convos_rtt = {}
    for line in convos.stdout.readlines():
      # file_time = {}
      file_time = []
      if '<->' in line:
        convo_line = line.strip()
        m = re.search(TCP_CONVO_FOUR_TUPLE, convo_line)
        if m:
          # Initial assignment attempt.
          ip_client, port_client, ip_server, port_server = m.groups()

          # Filter uninteresting conversations
          if port_server not in PORTS and port_client not in PORTS:
            # print 'Rejected:', ip_client, port_client, ip_server, port_server
            continue

          # Switch order if that makes sense.
          if port_server not in PORTS and port_client in PORTS:
            ip_server, port_server, ip_client, port_client = m.groups()

          convo_tuple = (ip_client, port_client, ip_server, port_server)
          if convo_tuple not in convos_rtt:
            convos_rtt[convo_tuple] = {}

          if client:
             ack_rtts = subprocess.Popen(
               shlex.split('tshark -r %s -n -d tcp.port=%d,http -R "ip.dst == %s and tcp.dstport == %s '\
                             'and ip.src == %s and tcp.srcport == %s" -e tcp.analysis.ack_rtt -T fields' % \
                             (filename, self.port_http, ip_client, port_client,
                              ip_server, port_server)), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
          else:
             ack_rtts = subprocess.Popen(
               shlex.split('tshark -r %s -n -d tcp.port=%d,http -R "ip.src == %s and tcp.srcport == %s '\
                             'and ip.dst == %s and tcp.dstport == %s" -e tcp.analysis.ack_rtt -T fields' % \
                             (filename, self.port_http, ip_client, port_client,
                              ip_server, port_server)), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

          ack_rtts_values = [ack_rtt.strip() for ack_rtt in ack_rtts.stdout.readlines() if ack_rtt.strip()]
          convos_rtt[convo_tuple] = ack_rtts_values

          # print 'tshark -r %s -n -d tcp.port==%d,http -R "ip.addr == %s and tcp.port == %s '\
          #     'and ip.addr == %s and tcp.port == %s"' % \
          #     (filename, self.port_http, ip_client, port_client, ip_server, port_server)
          convo = subprocess.Popen(
            shlex.split('tshark -r %s -n -d tcp.port==%d,http -R "ip.addr == %s and tcp.port == %s '\
                          'and ip.addr == %s and tcp.port == %s"' % \
                          (filename, self.port_http, ip_client, port_client,
                           ip_server, port_server)), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

          # Parse for difference between HTTP Response ACK and GET.
          for packet in convo.stdout.readlines():
            packet = packet.strip()

            # if 'GET' in packet and client:
            #   print ip_client, ip_server, packet

            # Find timestamp for client -> server packet.
            m = re.search('([0-9.]+)\ +%s\ +->\ +%s' % (ip_client, ip_server), packet)
            if not m:
              continue
            timestamp, = m.groups()

            # Figure out if this is a GET request.
            if 'GET' not in packet:
              last_client_to_server_timestamp = timestamp
              continue

            gap = float(timestamp) - float(last_client_to_server_timestamp)
            m = re.search('GET (.*) HTTP', packet)
            if m:
              request, = m.groups()
            # file_time[request] = gap
            file_time.append((request, gap))

        # print file_time
        convos_file_time[(ip_client, port_client, ip_server, port_server)] = file_time
    return convos_file_time, convos_rtt

def print_convos_file_time(convos_file_time):
  for convo in convos_file_time:
    request_time_tuples = convos_file_time.get(convo)
    print convo, [key for key, value in request_time_tuples]

def intersect(a, b):
  return list(set(a) & set(b))

def average(l):
  if len(l) == 0:
    return 0
  return sum(l) / (1. * len(l))

def ordered_intersect(a, b):
  intersection = intersect(a, b)
  out = []
  for val in a:
    if val in intersection:
      out.append(val)
  return out

def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    logging.error('%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS))
    sys.exit(1)

  if FLAGS.fileprefix:
    client_filename = FLAGS.fileprefix + '.client.pcap'
    server_filename = FLAGS.fileprefix + '.server.pcap'
  else:
    client_filename = FLAGS.client_filename
    server_filename = FLAGS.server_filename

  cp = ConvoParser(client_filename, server_filename, FLAGS.httpport)
  client_convos_file_time, client_convos_rtt = cp.client_convos()
  server_convos_file_time, server_convos_rtt = cp.server_convos()

  for convo in client_convos_file_time:
    print '%s:%s -> (%s:%s)' % (convo[0], convo[1], convo[2], convo[3])
    client_rtts = [float(val) for val in client_convos_rtt.get(convo)]
    if client_rtts:
      print 'client rtt min/avg/max = %.3f/%.3f/%.3f ms' % (1000 * min(client_rtts), 1000 * average(client_rtts), 1000 * max(client_rtts))
    print

  for convo in client_convos_file_time:
    convo_dict = {k:v for k,v in client_convos_file_time.get(convo)}
    convo_keys = [key for key, value in client_convos_file_time.get(convo)]
    for possible_match in server_convos_file_time:
      # print 'Match?:', possible_match
      possible_match_keys = [key for key, value in server_convos_file_time.get(possible_match)] #.keys()
      intersection = ordered_intersect(convo_keys, possible_match_keys)
      if len(intersection) == 0: continue

      # Found a match!
      print '%s:%s -> %s:%s -> %s:%s' % \
          (convo[0], convo[1], possible_match[0], possible_match[1],
           possible_match[2], possible_match[3])
      match_dict = {k:v for k,v in server_convos_file_time.get(possible_match)}
      client_rtts = [float(val) for val in client_convos_rtt.get(convo)]
      print 'client rtt min/avg/max = %.3f/%.3f/%.3f ms' % (1000 * min(client_rtts), 1000 * average(client_rtts), 1000 * max(client_rtts))
      server_rtts = [float(val) for val in server_convos_rtt.get(possible_match)]
      print 'server rtt min/avg/max = %.3f/%.3f/%.3f ms' % (1000 * min(server_rtts), 1000 * average(server_rtts), 1000 * max(server_rtts))

      for match in intersection:
        print '  %-30s %.6f %.6f' % \
            (match, convo_dict.get(match), match_dict.get(match))
        # print '%30s %.6f %.6f' % \
        #     (match, client_convos_file_time.get(convo).get(match),
        #      server_convos_file_time.get(possible_match).get(match))
      print


if __name__=='__main__':
  main(sys.argv)
