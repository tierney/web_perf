#!/bin/bash

tmobile_IP=192.168.42.196
wired_IP=216.165.108.217

function analyze {
    local CARRIER_IP
    for carrier in wired t-mobile
    do
        for pcap in pcaps_Feb_16/${carrier}_*pcap
        do
            echo $pcap
            if [[ ${carrier} == t-mobile ]]
            then
                CARRIER_IP=${tmobile_IP}
            else
                CARRIER_IP=${wired_IP}
            fi
            tshark -r ${pcap} -e frame.len -T fields -R "tcp and not http and ip.src == ${CARRIER_IP}" >> ${carrier}.len.outgoing.log
            tshark -r ${pcap} -e frame.len -T fields -R "tcp and not http and ip.dst == ${CARRIER_IP}" >> ${carrier}.len.incoming.log
        done
    done
}
# Get rid of any old log files.
rm wired.len*.log

analyze
