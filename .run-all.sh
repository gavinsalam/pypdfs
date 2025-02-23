#!/usr/bin/env bash
# short script to quickly check if all executables run OK.
# NB: does not test anything beyond that

for execs in pdf.py read_lhapdf.py mom.py lumi.py lumi-rapdist.py
do 
    ./$execs  > /dev/null && echo "$execs runs OK"
done
