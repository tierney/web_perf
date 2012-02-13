#!/bin/sh

for pcap in *.pcap;
do ./plot_content_length_response.py -g -f $pcap;
done