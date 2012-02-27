#!/bin/sh

for carrier in wired t-mobile
do
    for browser in firefox chrome android
    do
        for pcap in ${carrier}_${browser}_*.pcap
        do
            echo $pcap
            tshark -r ${pcap} -e tcp.analysis.ack_rtt -T fields >> rtt_${carrier}_${browser}.log
        done
    done
done
