#!/usr/bin/env ruby
##
## Copyright 2007 Matthew Lee Hinman
## matthew [dot] hinman [at] gmail [dot] com
##
## Generate a file to plot pcap traffic flows over time
## To get usage: ./flowtime --help
##

if ARGV.length < 3  or ARGV.to_s =~ /--help/
  STDERR.puts "Usage:"
  STDERR.puts "flowtime [-w #] [-h #] [-g] [--help] <pcapfile> <ipaddr> <outfile_bas>"
  STDERR.puts "-w specify the width, default: 2000"
  STDERR.puts "-h specify the height, default: 2000"
  STDERR.puts "-g automatically try generate a png (requires 'EasyTimeline' and 'pl' in path)"
  STDERR.puts "<pcapfile> the packet file to generate a graph of"
  STDERR.puts "<ipaddr> source address to generate a graph for, 'all' for all IPs"
  STDERR.puts "<outfile_base> basename for the output file"
  exit(0)
end

$WIDTH = ARGV.to_s =~ /-w\s*(\d+)/i ? $1.to_i : 2000
$HEIGHT = ARGV.to_s =~ /-h\s*(\d+)/i ? $1.to_i : 2000
$autograph = ARGV.to_s =~ /-g/i ? true : false
STDERR.puts "Width  : #{$WIDTH}"
STDERR.puts "Height : #{$HEIGHT}"

$filename = ARGV[ARGV.length-3].to_s
$ipaddr = ARGV[ARGV.length-2].to_s
$outfile = ARGV[ARGV.length-1].to_s
STDERR.puts "Outfile: #{$outfile}.txt"
$stdout = File.new("#{$outfile}.txt","w")
unless File.exist?($filename)
  puts "File: #{$filename} does not exist."
  exit(0)
end

events = []
$flow_start = 0.0
$flow_finish = 0.0

class TimeLine
  attr_accessor :stime,:etime,:sport,:dport,:addr

  def initialize(stime,etime,sport, dport,addr)
    @stime = stime
    @etime = etime
    @sport = sport.to_i
    @dport = dport.to_i
    @addr = addr
  end

end

STDERR.puts "Generating flow data..."
tshark_output = `tshark -n -e frame.time_relative -e ip.src -e tcp.srcport -e udp.srcport -e ip.dst -e tcp.dstport -e udp.dstport -T fields -r #{$filename}`

STDERR.puts "Parsing tshark output..."
tshark_output.each_line do |line|
  line.strip!
  data = line.split(/\s+/)
  if data.length < 4
    next
  end

  STDERR.puts data.join ','

  events.unshift(
    TimeLine.new(
      data[0].to_f,
      data[0].to_f + 0.01,
      data[2],
      data[4],
      data[3]))

   $flow_finish = 1 + data[0].to_f if $flow_finish < 1 + data[0].to_f

end
STDERR.puts "done."

events.each { |e|
  e.stime -= $flow_start
  e.etime -= $flow_start
#  STDERR.puts "#{e.stime}, #{e.etime}"
}

$flow_finish -= $flow_start
$flow_start = 0

STDERR.print "Generating graph data..."
puts "ImageSize  = width:#{$WIDTH} height:#{$HEIGHT}"
puts "PlotArea   = width:#{$WIDTH-155} height:#{$HEIGHT-50} left:150 bottom:40"
puts "AlignBars  = justify"

puts "Colors ="
puts "  id:http       value:blue        legend:HTTP"
puts "  id:ssl        value:red         legend:SSL"
puts "  id:dns        value:powderblue        legend:DNS"
puts "  id:noport     value:pink  legend:NoPort"
puts "  id:other      value:gray(0.1)      legend:Other"
puts "  id:lightgrey  value:gray(0.9)"
puts "  id:darkgrey   value:gray(0.1)"

puts "Period     = from:#{$flow_start} till:#{$flow_finish}"
puts "TimeAxis   = orientation:horizontal"
inc = ($flow_finish - $flow_start) / ($WIDTH / 50)
inc = inc.to_i
inc = 1 if inc < 1
puts "ScaleMajor = increment:#{inc} start:#{$flow_start.ceil} gridcolor:lightgrey"

puts "PlotData="

events.each { |e|
  if e.dport == 5353
    next
  end

  print "  bar: #{e.addr}-#{e.sport}-#{e.dport} "
  case e.dport
  when 0
    print "color:noport "
  when 80
    print "color:http "
  when 443
    print "color:ssl "
  when 22
    print "color:ssh "
  when 23
    print "color:telnet "
  when 21
    print "color:ftp "
  when 25
    print "color:smtp "
  when 53
    print "color:dns "
  when 67..68
    print "color:bootp "
  when 110
    print "color:pop3 "
  when 137..139
    print "color:netbios "
  when 6666..6669,7000
    print "color:irc "
  else
    print "color:other "
  end
#  puts "mark:(line,white) width:7 align:left fontsize:M"
  puts "  from:#{e.stime}  till:#{e.etime}"
}

puts "Legend = orientation:vertical position:bottom columns:4 columnwidth:200"
STDERR.puts "done."

$defout.close

if $autograph
  STDERR.print "Automatically creating graph..."
  system("EasyTimeline -b -i #{$outfile}.txt 2>&1 > /dev/null")
  STDERR.puts "done. (returned #{$?})"
end
