#!/usr/bin/env ruby

$filename = ARGV[ARGV.length-1].to_s
is_server = $filename.include? 'server'
is_client = !is_server

unless File.exist?($filename)
  puts "File: #{$filename} does not exist."
  exit(0)
end

STDERR.puts "Generating flow data..."
tshark_fields = [ 'frame.time_relative',
                  'ip.src',
                  'tcp.srcport',
                  'udp.srcport',
                  'ip.dst',
                  'tcp.dstport',
                  'udp.dstport',
                  'frame.len']
derived_fields = ['srcport', 'dstport', 'server_ip', 'server_port', 'direction', 'stream_id']

SERVER_PORTS = [80, 443, 34343]

if is_client
  first_packet = `tshark -r #{$filename} -c 1 -e frame.number -T fields -R "dns.qry.name contains amazon"`.to_i
else
  server_condition = 'tcp.dstport == ' + SERVER_PORTS.join(' or tcp.dstport == ')
  first_packet = `tshark -r #{$filename} -c 1 -e frame.number -T fields -R "#{server_condition}"`.to_i
end

tshark_query = '-e ' + tshark_fields.join(' -e ')
tshark_output = `tshark -n #{tshark_query} -T fields -E separator=, -r #{$filename} -R "not dns.qry.name contains google and not arp and frame.number >= #{first_packet}"`

STDERR.puts "Parsing tshark output..."
STDOUT.puts tshark_fields.join(', ') + ', ' + derived_fields.join(', ')

DEST_PORTS = [53] + SERVER_PORTS

init_time = -1.0
tshark_output.each_line do |line|
  # Preprocess the line.
  line.strip!
  data = line.split(/,/)
  vars = Hash.new
  tshark_fields.each { |f| vars[f] = data.shift }

  vars['frame.time_relative'] = vars['frame.time_relative'].to_f
  if init_time < 0.0
    init_time = vars['frame.time_relative']
    STDERR.puts init_time
  end

  vars['frame.time_relative'] -= init_time

  vars['srcport'] = (vars['tcp.srcport'] != '' ? vars['tcp.srcport'] : vars['udp.srcport']).to_i
  vars['dstport'] = (vars['tcp.dstport'] != '' ? vars['tcp.dstport'] : vars['udp.dstport']).to_i

  # keep both directions on the same stream id
  if (is_client and DEST_PORTS.include?(vars['srcport'].to_i)) or
      (not is_client and not DEST_PORTS.include?(vars['srcport'].to_i))
    vars['stream_id'] = "#{vars['dstport']}-#{vars['ip.src']}:#{vars['srcport']}"
    vars['server_ip'] = vars['ip.src']
    vars['server_port'] = vars['srcport']
    vars['direction'] = 'incoming'
  else
    vars['stream_id'] = "#{vars['srcport']}-#{vars['ip.dst']}:#{vars['dstport']}"
    vars['server_ip'] = vars['ip.dst']
    vars['server_port'] = vars['dstport']
    vars['direction'] = 'outgoing'
  end

  if vars['server_ip'].match(/^74.125/) or
      vars['server_ip'].match(/^173.194/) or
      vars['srcport'] == 34344 or
      vars['dstport'] == 34344 # or
      # (vars['ip.src'].match(/^172.16/) and vars['srcport'] == 53)
    next
  end

  STDOUT.print tshark_fields.map{ |f| vars[f].to_s }.join(', ')
  STDOUT.print ','
  STDOUT.puts derived_fields.map{ |f| vars[f].to_s }.join(', ')
end

STDERR.puts "done."
