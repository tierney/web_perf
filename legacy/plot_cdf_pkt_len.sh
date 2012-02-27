#!/bin/bash

for carrier in t-mobile wired
do
    for direction in incoming outgoing
    do
        ./plot_cdf_pkt_len.py -f ${carrier}.len.${direction}.log \
            -t "${carrier} ${direction} packet lengths" \
            -x 'Packet length [bytes]' \
            -y 'CDF Percentile'
    done
done
