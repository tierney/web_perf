#!/bin/sh

for pcap in *.pcap;
do
    DURATION=`./plot_content_length_response.py -f ${pcap} -d`
    echo ${pcap} $DURATION
    echo ${pcap} $DURATION >> duration.log
done