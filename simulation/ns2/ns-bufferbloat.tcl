# ns script for simulating bufferbloat

proc getopt {argc argv} {
  global opt
  for {set i 0} {$i < $argc} {incr i} {
    set arg [lindex $argv $i]
    if {[string range $arg 0 0] != "-"} \
      continue
    set name [string range $arg 1 end]
    set opt($name) \
        [lindex $argv [expr $i+1]]
  }
}

getopt $argc $argv

# Globals
set FlowNumber 1

#Create a simulator object
set ns [new Simulator]

#Define different colors for data flows (for NAM)
$ns color 1 Blue

# Open the NAM trace file
global nf
set nf [open out.nam w]
$ns namtrace-all $nf
set tracefd [open out.trace w]
$ns trace-all $tracefd

#Define a 'finish' procedure
proc finish {} {
    global ns nf opt
    # nf
    $ns flush-trace
    #Close the NAM trace file
    close $nf
    #Execute NAM on the trace file
    if {$opt(nam)} {
        exec nam out.nam &
    }
    exit 0
}

proc monitor {interval} {
    global FlowNumber tcp ns
    set nowtime [$ns now]

    for {set i 0} {$i < $FlowNumber} {incr i 1} {
        set win [open result$i a]
        puts $win "$nowtime [$tcp set cwnd_] [$tcp set ack_] [$tcp set rtt_]"
        close $win
    }
    $ns after $interval "monitor $interval"
}

# Create nodes.
set theseus [$ns node]
set beaker [$ns node]
set level3 [$ns node]
set operator [$ns node]
set tower [$ns node]
set mobile [$ns node]

$ns duplex-link $theseus $operator 1Gb 3ms DropTail
$ns duplex-link $operator $tower 1Gb 1ms DropTail
$ns duplex-link $tower $mobile 200Kb 10ms DropTail

# Queue-limits
$ns queue-limit $tower $operator $opt(ot)
$ns queue-limit $operator $tower $opt(tm)

$ns queue-limit $tower $mobile $opt(tm)


# $ns duplex-link-op $theseus $mobile orient right-down
# $ns duplex-link-op $tower $mobile orient right-up

# Monitor the queue for link (theseus-operator). (for NAM)
# $ns duplex-link-op $operator $tower queuePos 0.5

#Setup a TCP connection
set tcp [new Agent/TCP/Linux]
$tcp set class_ 2
$ns attach-agent $theseus $tcp
set sink [new Agent/TCPSink]
# Agent/TCPSink/Sack1/DelAck
$ns attach-agent $mobile $sink
$ns connect $tcp $sink
$tcp set fid_ 1
$tcp set window_ 1000

#Setup a FTP over TCP connection
set ftp [new Application/FTP]
$ftp attach-agent $tcp
$ftp set type_ FTP

# # create the error model;
set loss_module [new ErrorModel]

# # set error rate to \(0.1 = 10 / (100 - 0)\);
$loss_module set rate_ 0
$loss_module unit packet
$loss_module drop-target [new Agent/Null]
set lossyLink [$ns link $tower $mobile]
$lossyLink install-error $loss_module

$ns at 0.1 "$ftp start"
$ns at 45.0 "$ftp stop"

#Detach tcp and sink agents (not really necessary)
$ns at 45.0 "$ns detach-agent $theseus $tcp ; $ns detach-agent $mobile $sink"

#call the monitor at the end
$ns at 0 "monitor 0.01"

#Call the finish procedure after 5 seconds of simulation time
$ns at 45.1 "finish"

#Run the simulation
$ns run
