#!/bin/sh

for pcap in *pcap
do
    mkdir ${pcap}_data
    tcptrace -nlWrG $pcap > ${pcap}_data/${pcap}.log
    mv *.xpl ${pcap}_data
done