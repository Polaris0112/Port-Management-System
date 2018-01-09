#!/bin/bash
# the script use for update all server port data

set -e

env_location="/xxx/xxx/env"

group=$1
if [ ! $group ];then
    echo -e "usage: sh update.sh [group-name or all]\n"
    exit 2
fi

hosts_file="external_hosts"
path="$( cd "$( dirname "$0"  )" && pwd  )"


echo "Begin to update $group hosts port data..."

if [ "$group" = "all"];then
    for gp in  $(grep -E "\[(.*)\]" $hosts_file|cut -d '[' -f2|cut -d ']' -f1)
    do
        echo "Begin to update $gp hosts port data..."
        rm -rf $path/build_data/*
        sed -i "s/- hosts: .*$/- hosts: $gp/g" Fetch_files.yml 
        # run playbook
        sh $path/port_data/clean_dir.sh
        env_location/bin/ansible-playbook -i $hosts_file Fetch_files.yml 
        sh $path/port_data/change_dir.sh
        for host in $(ls ${path}/port_data|grep -Ev ".sh")
        do
            hn=$(grep -w $host $hosts_file|awk '{print $2}'|awk -F'=' '{print $2}')
            echo "Scanning outsite port of $host ..."
            nmap -sT -p- $hn|grep open > $path/port_data/$host/out_scan_port.txt && echo "Scan $host done..." &
        done
        wait
        echo "Start to update mysql..."
        $env_location/bin/python $path/db_update.py
        sh $path/port_data/clean_dir.sh
        echo "group $gp update done."
    done
else
    for gp in  $(grep -E "\[($group.*)\]" ${hosts_file}|cut -d '[' -f2|cut -d ']' -f1)
    do
        rm -rf $path/build_data/*
        sed -i "s/- hosts: .*$/- hosts: $gp/g" Fetch_files.yml 
        # run playbook
        sh $path/port_data/clean_dir.sh
        env_location/bin/ansible-playbook -i $hosts_file Fetch_files.yml
        sh $path/port_data/change_dir.sh
        for host in $(ls ${path}/port_data|grep -Ev ".sh")
        do
            hn=$(grep -w $host $hosts_file|awk '{print $2}'|awk -F'=' '{print $2}')
            echo "Scanning outsite port of $host ..."
            nmap -sT -Pn -p1-65535 $hn|grep open > $path/port_data/$host/out_scan_port.txt && echo "Scan $host done..." & 
        done
        wait
        echo "Start to update mysql..."
        env_location/bin/python $path/db_update.py
        #sh $path/port_data/clean_dir.sh
        echo "group $gp update done."
    done
fi
