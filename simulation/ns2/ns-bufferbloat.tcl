set FlowNumber 1

#Create a simulator object
set ns [new Simulator]

#Define different colors for data flows (for NAM)
$ns color 1 Blue
$ns color 2 Red

#Open the NAM trace file
set nf [open out.nam w]
$ns namtrace-all $nf

#Define a 'finish' procedure
proc finish {} {
        global ns nf
        $ns flush-trace
        #Close the NAM trace file
        close $nf
        #Execute NAM on the trace file
        exec nam out.nam &
        exit 0
}

proc monitor {interval} {
    global FlowNumber tcp ns
    set nowtime [$ns now]

    for {set i 0} {$i < $FlowNumber} {incr i 1} {
        set win [open result$i a]
        puts $win "$nowtime [$tcp set cwnd_] [$tcp set ack_]"
        close $win
    }
    $ns after $interval "monitor $interval"
}

#Create three nodes
set theseus [$ns node]
set beaker [$ns node]
set operator [$ns node]
set tower [$ns node]
set mobile [$ns node]

$ns duplex-link $theseus $beaker 100Mb 1ms DropTail
$ns duplex-link $beaker $operator 10Mb 50ms DropTail
$ns duplex-link $operator $tower 100Mb 5ms DropTail
$ns duplex-link $tower $mobile 300Kb 250ms DropTail

# $ns queue-limit $beaker $operator 10
$ns queue-limit $operator $tower 10
$ns queue-limit $tower $mobile 7

# $ns duplex-link-op $theseus $mobile orient right-down
# $ns duplex-link-op $tower $mobile orient right-up

# Monitor the queue for link (theseus-operator). (for NAM)
$ns duplex-link-op $operator $tower queuePos 0.5

#Setup a TCP connection
set tcp [new Agent/TCP/Linux]
$tcp set class_ 2
$ns attach-agent $theseus $tcp
set sink [new Agent/TCPSink]
# Agent/TCPSink/Sack1/DelAck
$ns attach-agent $mobile $sink
$ns connect $tcp $sink
$tcp set fid_ 1

#Setup a FTP over TCP connection
set ftp [new Application/FTP]
$ftp attach-agent $tcp
$ftp set type_ FTP

$ns at 0.1 "$ftp start"
$ns at 45.0 "$ftp stop"

#Detach tcp and sink agents (not really necessary)
$ns at 45.0 "$ns detach-agent $theseus $tcp ; $ns detach-agent $mobile $sink"

#call the monitor at the end
$ns at 0 "monitor 0.1"

#Call the finish procedure after 5 seconds of simulation time
$ns at 45.1 "finish"

#Run the simulation
$ns run
