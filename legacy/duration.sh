#!/bin/sh

#DURATION=duration.Feb7.log
DURATION=duration.log

cat ${DURATION}  | sort -n | awk '{print $1}' > /tmp/cumulative.log
cat ${DURATION} | grep 'verizon_'  | sort -n | awk '{print $1}' > /tmp/verizon.log
cat ${DURATION} | grep 'wired_'  | sort -n | awk '{print $1}' > /tmp/wired.log
cat ${DURATION} | grep 't-mobile_'  | sort -n | awk '{print $1}' > /tmp/t-mobile.log
