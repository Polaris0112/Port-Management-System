#!/bin/bash

rm -f /tmp/grap_data.txt
hostname > /tmp/grap_data.txt

tip=$(sudo ifconfig|grep -iE 'mask.255.255.255.0'|grep 'inet '|grep -v '127.0'|xargs|awk -F ' ' '{print $2}'|cut -d':' -f 2|head -1)
if [ ! $tip ];then
    tip=$(sudo ifconfig|grep -iE 'mask.255.255.240.0'|grep 'inet '|grep -v '127.0'|xargs|awk -F ' ' '{print $2}'|cut -d':' -f 2|head -1)
    if [ ! $tip ];then
        tip=$(sudo ifconfig|grep -iE 'mask.255.255.248.0'|grep 'inet '|grep -v '127.0'|xargs|awk -F ' ' '{print $2}'|cut -d':' -f 2|head -1)
        if [ ! $tip ];then
            tip=$(sudo ifconfig|grep -iE 'mask.255.0.0.0'|grep 'inet '|grep -v '127.0'|xargs|awk -F ' ' '{print $2}'|cut -d':' -f 2|head -1)
            if [ ! $tip ];then
                tip=$(sudo ifconfig|grep -iE 'mask.255.255.0.0'|grep 'inet '|grep -v '127.0'|xargs|awk -F ' ' '{print $2}'|cut -d':' -f 2|head -1)
                if [ ! $tip ];then
                    tip=$(sudo ifconfig|grep -iE 'mask.255.255.255.224'|grep 'inet '|grep -v '127.0'|xargs|awk -F ' ' '{print $2}'|cut -d':' -f 2|head -1)
                    if [ ! $tip ];then
                         tip=$(sudo ifconfig|grep -iE 'mask.255.255.252.0'|grep 'inet '|grep -v '127.0'|xargs|awk -F ' ' '{print $2}'|cut -d':' -f 2|head -1)
                    fi
                fi
            fi
        fi
    fi
fi
if [ ! $tip ];then
    exit 1
fi

echo $tip >> /tmp/grap_data.txt
sudo netstat -tnlp|grep tcp >> /tmp/grap_data.txt
eip=$(curl icanhazip.com)
echo $eip >> /tmp/grap_data.txt
