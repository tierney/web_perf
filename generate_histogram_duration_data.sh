#!/bin/sh

for pcap in ~/data/pcaps/*.pcap;
do
    DURATION=`./plot_content_length_response.py -f ${pcap} -d`
    echo $DURATION ${pcap}
    echo $DURATION ${pcap} >> duration.Feb7.log
done
