#!/bin/bash
# Script to run tcpdump libpcap files through tcptrace and produce all graphs
# and summaries. Copies output files to similarly-named directory.
#
# Author: tierney@cs.nyu.edu (Matt Tierney)
# License: GPLv2

function analyze {
    for pcap in *.pcap;
    do
        echo $pcap
        local new_dir=${pcap}_data
        local log=${pcap}.log
        mkdir ${new_dir}
        tcptrace -nlWrG $pcap > $log
        mv *.xpl $new_dir
        mv $log $new_dir
    done
}

# Run tcptrace and copy the files to the associated directory.
analyze