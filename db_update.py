#!/usr/bin/env python
# -*- coding:utf-8 -*-
# update users data in servers
import MySQLdb
from os import walk, path, getcwd, makedirs, _exit
import re, sys, json
import socket

system_port_ignore = [25, 53, 111, 631, 953]
system_task_ignore = ["rpc","cpusd"]
port_data_path = sys.path[0]+"/port_data"
build_data_path = sys.path[0]+"/build_data"
mysql_host = ""
mysql_db = ""
mysql_username = ""
mysql_password = ""


def buildupdata():
    host_data = {}
    if not path.exists(sys.path[0]+"/build_data"):
        makedirs(sys.path[0]+"/build_data")
    
    for (dirpath, dirnames, filenames) in walk(port_data_path):
        if len(dirpath) == 0 or len(filenames) == 0 or filenames[0] == "change_dir.sh" or filenames[0] == "clean_dir.sh":
            continue
        
        with open(path.join(dirpath,filenames[0])) as o:
            out_scan_port_data = o.readlines() 
        out_scan_port_list = []
        for line in out_scan_port_data:
            out_scan_port_list.append(int(line.replace("\n","").split("/")[0]))

        with open(path.join(dirpath,filenames[1])) as p:
            port_data = p.readlines()
        sshname = dirpath.split("/")[-1]
        hostname = port_data[0].replace("\n","")
        inip = port_data[1].replace("\n","")
        exip = port_data[-1].replace("\n","")
        acceptip = ''
        combind_ip = exip+"/"+inip
        host_data[sshname] = {"ipaddr": combind_ip, "hostname": hostname, "ssh_name": sshname}
        insert_internal_network(combind_ip, inip, sshname)

        if not path.exists(sys.path[0]+"/build_data/"+dirpath.split("/")[-1]):
            makedirs(sys.path[0]+"/build_data/"+dirpath.split("/")[-1])
         
        for linenum in range(2,len(port_data)-1):
            flag = 0
            try:
                split_port_data = port_data[linenum].split()[3].split(":") 
            except IndexError:
                print "IndexError:\n"
                print port_data[linenum]
                sys.exit(2)
            if len(split_port_data) <> 2:
                acceptip = "0.0.0.0/0"
            else:
                if split_port_data[0] == "127.0.0.1":
                    acceptip = "127.0.0.1"
                else:
                    if split_port_data[0] == "0.0.0.0":
                        acceptip = "0.0.0.0/0"
                    else:
                        acceptip = inip.split(".")[0]+"."+inip.split(".")[1]+".0.0/16"    
            port = split_port_data[-1]
            if int(port) in system_port_ignore:
                flag = 1
            usage = ''.join(port_data[linenum].split()[-1].split("/")[1:])
            for task in system_task_ignore:
                if re.search("^"+task+".*$", usage):
                    flag = 1
                    break
            #print flag,dirpath.split("/")[-1],port,acceptip
            if flag == 1:
                continue
            else:
                if int(port) in out_scan_port_list:
                    acceptip = "0.0.0.0/0"
                elif acceptip == "127.0.0.1":
                    acceptip = "127.0.0.1"
                else:
                    acceptip = inip.split(".")[0]+"."+inip.split(".")[1]+".0.0/16"
                pd = {"hostname": hostname, "ipaddr": combind_ip, "port": port, "usage": usage, "acceptip":acceptip, "record_id": combind_ip+str(port), "protocol": "TCP"}
                with open(sys.path[0]+"/build_data/"+dirpath.split("/")[-1]+"/"+port,'w') as w:
                    w.write(json.dumps(pd))
                w.close()

#    for (dirpath, dirnames, filenames) in walk(build_data_path):
#        if dirnames == []:
#            continue
    for key in host_data.keys():
        updatehost(key, host_data[key])


def insert_internal_network(combind_ip, inip, sshname):
    db = MySQLdb.connect(mysql_host,mysql_username,mysql_password,mysql_db )
    cursor = db.cursor()
    acceptip = inip.split(".")[0]+"."+inip.split(".")[1]+".0.0/16" 
    port = "0"
    usage = "internal-network"
    protocol = "TCP"
    record_id = combind_ip + port
    check_sql = "select port from management_port where record_id = '%s'"%(record_id)
    try:
        cursor.execute(check_sql)
        if len(cursor.fetchall()) == 0:
            insert_sql = "INSERT INTO management_port VALUES ('NULL','%s', '%s', '%s', '%s', '%s', '%s', '%s')"%(combind_ip, port, usage, acceptip, record_id, protocol, sshname)
            try:
                cursor.execute(insert_sql)
                print "INSERT internal network rules for "+sshname
                db.commit()
            except:
                db.rollback()
        else:
            delete_sql = "DELETE FROM management_port where record_id ='%s'"%(record_id)
            insert_sql = "INSERT INTO management_port VALUES (NULL, '%s', '%s', '%s', '%s', '%s', '%s', '%s')"%(combind_ip, port, usage, acceptip, record_id, protocol, sshname)
            try:
                cursor.execute(delete_sql)
                cursor.execute(insert_sql)
                print "UPDATE internal network rules for "+sshname
                db.commit()
            except:
                db.rollback()

    except:
        db.rollback()
    db.close()



def check_exists_port():
    db = MySQLdb.connect(mysql_host,mysql_username,mysql_password,mysql_db )
    cursor = db.cursor()
    for (dirpath, dirnames, filenames) in walk(sys.path[0]+"/build_data"):
        ssh_name = dirpath.split("/")[-1]
        port_list = filenames
        check_port_sql = "select port from management_port where ssh_name = '%s'"%(ssh_name)
        try:
            cursor.execute(check_sql)
            results = cursor.fetchall()
            for row in results:
                if row[0] in port_list:
                    continue
                else:
                    delete_sql = "DELETE FROM management_port where port = '%s' and ssh_name = '%s'"%(row[0], ssh_name)
                    print "Database update : DELETE "+row[0]+"  of  "+ ssh_name
                    cursor.execute(delete_sql)
                    db.commit()
        except:
            db.rollback()
    db.close()


def port_rule_update():
    if path.exists(sys.path[0]+"/rules"):
        for (dirpath, dirnames, filenames) in walk(sys.path[0]+"/rules"):
            for fe in filenames:
                with open (dirpath+"/"+fe) as f:
                    rules = f.readlines()
                for line in rules:
                    line = line.replace("\n","")
                    rule = json.loads(line)
                    port = rule["port"]
                    acceptip = rule["acceptip"]
                    update_rules_to_db(fe, port,acceptip)
    else:
        pass

def update_rules_to_db(match_name, port,acceptip):
    db = MySQLdb.connect(mysql_host,mysql_username,mysql_password,mysql_db )
    cursor = db.cursor()
    update_sql = "UPDATE management_port SET acceptip='"+acceptip+"' where port='"+port+"' and ssh_name LIKE \"%"+match_name+"%\" "
    try:
        cursor.execute(update_sql)
        print "Update acceptip="+acceptip+"  of  port="+port
        db.commit()
    except Exception as e:
        print e
        db.rollback()
    db.close()

def update_port_data():
    db = MySQLdb.connect(mysql_host,mysql_username,mysql_password,mysql_db )
    cursor = db.cursor()
    for (dirpath, dirnames, filenames) in walk(sys.path[0]+"/build_data"):
        ssh_name = str(dirpath.split("/")[-1])
        for fe in filenames:
            with open(dirpath+"/"+fe) as f:
                port_data = json.loads(f.read())
            ipaddr = str(port_data["ipaddr"])
            port = str(port_data["port"])
            usage = str(port_data["usage"])
            acceptip = str(port_data["acceptip"])
            protocol = str(port_data["protocol"])
            combine_ipaddr = str(port_data["ipaddr"]+fe)
            check_sql = "select port from management_port where record_id = '%s'"%(combine_ipaddr)
            cursor.execute(check_sql)
            if len(cursor.fetchall()) == 0:
                insert_sql="INSERT INTO management_port VALUES (NULL, '%s', '%s', '%s', '%s', '%s', '%s', '%s')"%(ipaddr, port, usage, acceptip, combine_ipaddr, protocol, ssh_name)
                try:
                    cursor.execute(insert_sql)
                    print "Database update : INSERT "+ port_data["port"]+"   of    "+port_data["hostname"]
                    db.commit()
                except Exception as e:
                    print e
                    db.rollback()
            else:
                delete_sql="DELETE FROM management_port where record_id ='%s'"%(combine_ipaddr)
                cursor.execute(delete_sql)
                #update_sql="UPDATE management_port SET ipaddr='%s', port='%s', usage='%s', acceptip='%s', protocol='%s', ssh_name='%s' where record_id ='%s'"%(ipaddr, port, usage, acceptip, protocol, ssh_name, combine_ipaddr)
                insert_sql="INSERT INTO management_port VALUES (NULL, '%s', '%s', '%s', '%s', '%s', '%s', '%s')"%(ipaddr, port, usage, acceptip, combine_ipaddr, protocol, ssh_name)
                try:
                    #cursor.execute(update_sql)
                    cursor.execute(insert_sql)
                    print "Database update : UPDATE "+ port_data["port"]+"   of    "+port_data["hostname"]
                    db.commit()
                except Exception as e:
                    print e
                    db.rollback()
    db.close()
    
    


def updatehost(sshname, data):
    db = MySQLdb.connect(mysql_host,mysql_username,mysql_password,mysql_db )
    cursor = db.cursor()
    check_sql = "select hostname from management_host where ssh_name = '%s'"%(sshname)
    try:
        cursor.execute(check_sql)
        if len(cursor.fetchall()) == 0:
            insert_sql = "INSERT INTO management_host(ipaddr,hostname,ssh_name)VALUES ('%s', '%s', '%s')"%(data["ipaddr"], data["hostname"], data["ssh_name"])
            cursor.execute(insert_sql)
        else:
            update_sql = "UPDATE management_host SET ipaddr='%s', hostname='%s' where ssh_name='%s'"%(data["ipaddr"],data["hostname"],sshname)
            cursor.execute(update_sql)
        db.commit()
    except:
        db.rollback()
    db.close()

def repair_db():
    db = MySQLdb.connect(mysql_host,mysql_username,mysql_password,mysql_db )
    cursor = db.cursor()
    check_sql = "SELECT * FROM  management_port WHERE record_id IN ( SELECT  record_id  FROM  management_port GROUP BY  record_id  HAVING count(record_id) > 1 )"
    try:
        cursor.execute(check_sql)
        results = cursor.fetchall()
        if len(results) == 0:
            pass
        else:
            for data in results:
                ipaddr = data[1]
                port = data[2]
                usage = data[3]
                acceptip = data[4]
                record_id = data[5]
                protocol = data[6]
                ssh_name = data[7]
                delete_sql = "DELETE FROM management_port WHERE record_id = '%s'"%(record_id)
                cursor.execute(delete_sql)
                insert_sql = "INSERT INTO management_port VALUES ('', '%s', '%s', '%s', '%s', '%s', '%s', '%s')"%(ipaddr, port, usage, acceptip, record_id, protocol, ssh_name)
                cursor.execute(insert_sql)
                print "UPDATE %s port info of %s"%(port, ssh_name)
        db.commit()
    except:
        db.rollback()

    check_ip_sql = "SELECT ssh_name,ipaddr FROM management_host"
    try:
        cursor.execute(check_ip_sql)
        results = cursor.fetchall()
        for sn in results:
            sshname = sn[0]
            ipaddr = sn[1]
            get_internal_ip = ipaddr.split("/")[1]
            check_port_ip_sql = "SELECT ipaddr,port FROM management_port where ssh_name='%s'"%(sshname)
            # update data
            try:
                cursor.execute(check_port_ip_sql)
                results_ip = cursor.fetchall()
                # update data
                for data in results_ip:
                    old_ipaddr = data[0]
                    port = data[1]
                    old_record_id = str(old_ipaddr) + str(port)
                    new_record_id = str(ipaddr) + str(port)
                    if data[0] != ipaddr:
                         try:
                             update_record_id_sql = "UPDATE management_port SET record_id='%s' where record_id='%s'"%(new_record_id, old_record_id)
                             cursor.execute(update_record_id_sql)
                             db.commit()
                         except:
                             db.rollback()
                         try:
                             update_ipaddr_sql = "UPDATE management_port SET ipaddr='%s' where ipaddr='%s'"%(ipaddr, data[0])
                             cursor.execute(update_ipaddr_sql)
                             db.commit()
                         except:
                             db.rollback()
                         #print update_record_id_sql,update_ipaddr_sql
                         print "UPDATE port %s infomation of %s"%(port, ipaddr)
                
                # rm wrong ip data
                for data in results_ip:
                    port = data[1]
                    wrong_recordid = "/"+str(get_internal_ip)+str(port)
                    try:
                        delete_record_id_sql = "DELETE from management_port where record_id='%s'"%(wrong_recordid)
                        cursor.execute(delete_record_id_sql)
                        db.commit()
                    except:
                        continue
                        #db.rollback()
                    #print "delete record_id : %s"%(wrong_recordid)
                db.commit()
            except:
                db.rollback()

        db.commit()
    except:
        db.rollback()

    db.close()




def main():
    if len(sys.argv) != 1:
        if sys.argv[1] == "repair":
            repair_db()
    else:
        buildupdata()
        check_exists_port()
        update_port_data()
        port_rule_update()
        repair_db()

 


if __name__ == "__main__":
    main()

