#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: hanabi_verify_all mon_programme"
    exit 1
fi

for dir in ../data/*; do
    for f in $dir/*.in; do 
        base=`basename $f .in`
        $1 < $f > $base.ans 
        ./hanabi_trace.py $f $base.ans > $base.txt 
        diff -q $base.txt $dir/$base.txt
    done
done 
