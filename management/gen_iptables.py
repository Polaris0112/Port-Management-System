#!/usr/bin/env python
#-*- coding:utf-8 -*-
'''
  用于生成防火墙脚本的逻辑部分
  作者：cjj0596
  时间：2017-02-13 15:17
'''
import re, os
sub=re.compile(r"(((2[0-4][0-9]|25[0-5]|[01]?[0-9]{1,2})\.){3}(2[0-4][0-9]|25[0-5]|[01]?[0-9]{1,2})(?![0-9.])(/(\d){1,2}){0,1},){1,}((2[0-4][0-9]|25[0-5]|[01]?[0-9]{1,2})\.){3}(2[0-4][0-9]|25[0-5]|[01]?[0-9]{1,2})(?![0-9.])(/(\d){1,2}){0,1}")


def gen_rules(name, detail_port):
    data = {}
    iptables = """#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
iptables -F
iptables -A INPUT -i lo -j ACCEPT
iptables -A INPUT -s 127.0.0.1 -d 127.0.0.1 -j ACCEPT
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

## for ping:
iptables -A INPUT -p icmp --icmp-type echo-reply -j ACCEPT
iptables -A INPUT -p icmp --icmp-type echo-request -j ACCEPT
"""
## ## for dns:
## iptables -A INPUT -p tcp --source-port 53 -j ACCEPT
## iptables -A OUTPUT -p tcp --source-port 53 -j ACCEPT
## """
    for info in detail_port:
        if int(info.port) == 0:
            for ap in info.acceptip.split(","):
                iptables += """
## internal
iptables -A INPUT -p tcp -s """+ str(ap) +"""  -j ACCEPT"""

    for info in detail_port:
        port = info.port
        usage = info.usage
        acceptip = info.acceptip
        protocol = info.protocol
        if int(port) == 0:
            continue
        tmp = {"acceptip":acceptip,"protocol":protocol,"port":port}
        data.setdefault(usage,[]).append(tmp)  

    for key in data.keys():
        iptables += """

### """+ key
        for d in data[key]:
            if d["acceptip"] == "127.0.0.1":
                continue
            if d["protocol"] == "TCP":
                if d["acceptip"] == "0.0.0.0" or d["acceptip"] == "0.0.0.0/0":
                    iptables += """
iptables -A INPUT -p tcp --dport """+ str(d["port"]) +""" -j ACCEPT
iptables -A OUTPUT -p tcp --sport """+ str(d["port"]) +""" -j ACCEPT
"""
                elif sub.match(d["acceptip"]):
                    subnet_list = d["acceptip"].split(",")
                    for ap in subnet_list:
                        if ap != '':
                            iptables += """
iptables -A INPUT -p tcp --dport """+str(d["port"])+""" -s """+str(ap)+""" -j ACCEPT
iptables -A OUTPUT -p tcp --sport """+str(d["port"])+""" -d """+str(ap)+""" -j ACCEPT
"""
                else:
                    iptables += """
iptables -A INPUT -p tcp --dport """+str(d["port"])+""" -s """+str(d["acceptip"])+""" -j ACCEPT
iptables -A OUTPUT -p tcp --sport """+str(d["port"])+""" -d """+str(d["acceptip"])+""" -j ACCEPT
"""
            elif d["protocol"] == "UDP":
                if d["acceptip"] == "0.0.0.0" or d["acceptip"] == "0.0.0.0/0":
                    iptables += """
iptables -A INPUT -p udp --dport """+ str(d["port"]) +""" -j ACCEPT
iptables -A OUTPUT -p udp --sport """+ str(d["port"]) +""" -j ACCEPT
"""                
                elif sub.match(d["acceptip"]):
                    subnet_list = d["acceptip"].split(",")
                    for ap in subnet_list:
                        if ap != '':
                            iptables += """
iptables -A INPUT -p udp --dport """+str(d["port"])+""" -s """+str(ap)+""" -j ACCEPT
iptables -A OUTPUT -p udp --sport """+str(d["port"])+""" -d """+str(ap)+""" -j ACCEPT
"""
                else:
                    iptables += """
iptables -A INPUT -p udp --dport """+str(d["port"])+""" -s """+str(d["acceptip"])+""" -j ACCEPT
iptables -A OUTPUT -p udp --sport """+str(d["port"])+""" -d """+str(d["acceptip"])+""" -j ACCEPT
"""
            else:
                if d["acceptip"] == "0.0.0.0" or d["acceptip"] == "0.0.0.0/0":
                    iptables += """
iptables -A INPUT -p tcp --dport """+ str(d["port"]) +""" -j ACCEPT
iptables -A OUTPUT -p tcp --sport """+ str(d["port"]) +""" -j ACCEPT
iptables -A INPUT -p udp --dport """+ str(d["port"]) +""" -j ACCEPT
iptables -A OUTPUT -p udp --sport """+ str(d["port"]) +""" -j ACCEPT
"""
                elif sub.match(d["acceptip"]):
                    subnet_list = d["acceptip"].split(",")
                    for ap in subnet_list:
                        if ap != '':
                            iptables += """
iptables -A INPUT -p tcp --dport """+str(d["port"])+""" -s """+str(ap)+""" -j ACCEPT
iptables -A OUTPUT -p tcp --sport """+str(d["port"])+""" -d """+str(ap)+""" -j ACCEPT
iptables -A INPUT -p udp --dport """+str(d["port"])+""" -s """+str(ap)+""" -j ACCEPT
iptables -A OUTPUT -p udp --sport """+str(d["port"])+""" -d """+str(ap)+""" -j ACCEPT
"""
                else:
                    iptables += """
iptables -A INPUT -p tcp --dport """+str(d["port"])+""" -s """+str(d["acceptip"])+""" -j ACCEPT
iptables -A OUTPUT -p tcp --sport """+str(d["port"])+""" -d """+str(d["acceptip"])+""" -j ACCEPT
iptables -A INPUT -p udp --dport """+str(d["port"])+""" -s """+str(d["acceptip"])+""" -j ACCEPT
iptables -A OUTPUT -p udp --sport """+str(d["port"])+""" -d """+str(d["acceptip"])+""" -j ACCEPT
"""

    iptables += """
iptables -A INPUT -p tcp -j REJECT --reject-with tcp-reset
iptables -A INPUT -j DROP
iptables -A FORWARD -j DROP

service iptables save
"""

    #if not os.path.exists(os.path.join(os.getcwd(),"script-iptables",name)):
    #    os.makedirs(os.path.join(os.getcwd(),"script-iptables",name))
    #with open(os.path.join(os.getcwd(),"script-iptables",name)+"/iptables.sh",'w+') as f:
    #    f.truncate()
    #    f.write(iptables)
    #f.close()

    return iptables 



if __name__ == "__main__":
    pass
