#!/bin/sh

for pcap in ~/data/pcaps_Feb_20/*.pcap
do
    DURATION=`./plot_content_length_response.py -f ${pcap} -d`
    echo $DURATION ${pcap}
    echo $DURATION ${pcap} >> duration.Feb20.log
done
