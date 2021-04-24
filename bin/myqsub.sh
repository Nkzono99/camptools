#!/bin/bash
# plasma.inpのノード数をjobファイルに適用する.

tmpfile='myjob.sh'

if [ $# -ne 1 ]; then
    echo 'jobファイルを指定してください.'
    exit 1
fi

python ~/large0/sc/myqsub.py $1 -o $tmpfile
# qsub $tmpfile