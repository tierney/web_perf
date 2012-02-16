#!/bin/sh

for pcap in *.pcap;
do
    DURATION=`./plot_content_length_response.py -f ${pcap} -d`
    echo $DURATION ${pcap}
    echo $DURATION ${pcap} >> duration.log
done