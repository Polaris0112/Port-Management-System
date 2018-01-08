#!/bin/bash

path="$( cd "$( dirname "$0"  )" && pwd  )"

for host in $(ls $path|grep -vE '.sh$')
do
    mv $path/$host/tmp/grap_data.txt  $path/$host/
    rm -rf $path/$host/tmp
done



