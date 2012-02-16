#!/bin/sh

for carrier in wired t-mobile
do
    for browser in firefox chrome android
    do
        cat rtt_${carrier}_${browser}.log | python /scratch/bin/create-cdf-data.py > rtt_${carrier}_${browser}.log.cdf
        sed "s/DATAFILE/${carrier}_${browser}.log/g" /scratch/bin/cdf.plt > /scratch/bin/${carrier}_${browser}.plt
        gnuplot /scratch/bin/${carrier}_${browser}.plt
        rm rtt_${carrier}_${browser}.log.cdf
        rm /scratch/bin/${carrier}_${browser}.plt
    done
done
