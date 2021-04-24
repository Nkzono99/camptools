#!/bin/bash
# jobを投入し記録する.

SCRIPT_DIR=$(cd $(dirname $0); pwd)

tmpfile='myjob.sh'

if [ $# -ne 1 ]; then
    echo 'jobファイルを指定してください.'
    exit 1
fi

python $SCRIPT_DIR/myqsub.py $1 --noem
# qsub $tmpfile

