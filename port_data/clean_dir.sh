#!/bin/bash

path="$( cd "$( dirname "$0"  )" && pwd  )"

for host in $(ls $path|grep -vE '.sh$')
do
    rm -rf $path/$host
done
