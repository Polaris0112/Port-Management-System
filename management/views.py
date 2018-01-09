# -*- coding:utf-8 -*- 
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.models import User
from django.contrib import auth
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from management.models import MyUser, Port, Host
from django.core.urlresolvers import reverse
from management.utils import permission_check
from management.gen_iptables import gen_rules 

import re, os 
import csv
import operator  
reg=re.compile(r"((2[0-4][0-9]|25[0-5]|[01]?[0-9]{1,2})\.){3}(2[0-4][0-9]|25[0-5]|[01]?[0-9]{1,2})(?![0-9.])")
reg_ip=re.compile(r"((2[0-4][0-9]|25[0-5]|[01]?[0-9]{1,2})\.){3}(2[0-4][0-9]|25[0-5]|[01]?[0-9]{1,2})(?![0-9.])/((2[0-4][0-9]|25[0-5]|[01]?[0-9]{1,2})\.){3}(2[0-4][0-9]|25[0-5]|[01]?[0-9]{1,2})(?![0-9.])")
#reg=re.compile(r"([0-9]{1,2}|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.([0-9]{1,2}|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.([0-9]{1,2}|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.([0-9]{1,2}|1[0-9][0-9]|2[0-4][0-9]|25[0-5])")
sub=re.compile(r"(((2[0-4][0-9]|25[0-5]|[01]?[0-9]{1,2})\.){3}(2[0-4][0-9]|25[0-5]|[01]?[0-9]{1,2})(?![0-9.])(/(\d){1,2}){0,1},){0,}((2[0-4][0-9]|25[0-5]|[01]?[0-9]{1,2})\.){3}(2[0-4][0-9]|25[0-5]|[01]?[0-9]{1,2})(?![0-9.])(/(\d){1,2}){0,1}")
#sub=re.compile(r"([0-9]{1,2}|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.([0-9]{1,2}|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.([0-9]{1,2}|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.([0-9]{1,2}|1[0-9][0-9]|2[0-4][0-9]|25[0-5])(/(\d){1,2}){0,1}")


def index(request):
    user = request.user if request.user.is_authenticated() else None
    content = {
        'active_menu': 'homepage',
        'user': user,
    }
    return render(request, 'management/index.html', content)


def signup(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('homepage'))
    state = None
    if request.method == 'POST':
        password = request.POST.get('password', '')
        repeat_password = request.POST.get('repeat_password', '')
        if password == '' or repeat_password == '':
            state = 'empty'
        elif password != repeat_password:
            state = 'repeat_error'
        else:
            username = request.POST.get('username', '')
            if User.objects.filter(username=username):
                state = 'user_exist'
            else:
                new_user = User.objects.create_user(username=username, password=password,
                                                    email=request.POST.get('email', ''))
                new_user.save()
                new_my_user = MyUser(user=new_user, nickname=request.POST.get('nickname', ''))
                new_my_user.save()
                state = 'success'
    content = {
        'active_menu': 'homepage',
        'state': state,
        'user': None,
    }
    return render(request, 'management/signup.html', content)


def login(request):
    print request.read()
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('homepage'))
    state = None
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return HttpResponseRedirect(reverse('homepage'))
        else:
            state = 'not_exist_or_password_error'
    content = {
        'active_menu': 'homepage',
        'state': state,
        'user': None
    }
    return render(request, 'management/login.html', content)


def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(reverse('homepage'))


@login_required
def set_password(request):
    user = request.user
    state = None
    if request.method == 'POST':
        old_password = request.POST.get('old_password', '')
        new_password = request.POST.get('new_password', '')
        repeat_password = request.POST.get('repeat_password', '')
        if user.check_password(old_password):
            if not new_password:
                state = 'empty'
            elif new_password != repeat_password:
                state = 'repeat_error'
            else:
                user.set_password(new_password)
                user.save()
                state = 'success'
        else:
            state = 'password_error'
    content = {
        'user': user,
        'active_menu': 'homepage',
        'state': state,
    }
    return render(request, 'management/set_password.html', content)


@user_passes_test(permission_check)
def add_host(request):
    user = request.user
    state = None
    get_hostname = ''
    get_sshname = ''
    get_iipaddr = ''
    get_eipaddr = ''


    if request.method == 'POST':
        if request.POST.get('hostname', '') != '' and not re.search(r"\.",request.POST.get('hostname', '')):
            get_hostname = request.POST.get('hostname', '')
            get_sshname = request.POST.get('sshname', '')
            if request.POST.get('eipaddr', '') != '' and reg.search(request.POST.get('eipaddr', '')):
                get_eipaddr = request.POST.get('eipaddr', '')
                get_iipaddr = request.POST.get('iipaddr', '')
                if reg.search(get_eipaddr) and reg.search(get_iipaddr):
                    get_ipaddr = get_eipaddr + " / " + get_iipaddr
                    if Host.objects.filter(ipaddr=get_ipaddr).count() is 0 and Host.objects.filter(hostname=get_hostname).count() is 0:
    	         	# add host 
                        new_host = Host(
                            hostname=get_hostname,
                            ipaddr=get_ipaddr,
                            ssh_name=get_sshname,
                        )
                        new_host.save()            
                        state = 'success'
                    else:
                        state = 'ip_hostname_exist'
                else:
                    state = 'illegal_ipaddress'
            else:
                state = 'illegal_ipaddress'
        else:
            state = 'illegal_hostname'
    else:
        pass

    content = {
        'user': user,
        'active_menu': 'add_host',
        'hostname': get_hostname,
        'sshname': get_sshname,
        'eipaddr': get_eipaddr,
        'iipaddr': get_iipaddr,
        'state': state,
    }
    return render(request, 'management/add_host.html', content)


@user_passes_test(permission_check)
def add_port(request):
    user = request.user
    state = None
    exists_port = []
    get_ipaddr = ''
    get_port = ''
    get_usage = ''
    acceptip = '0.0.0.0'
    query_ipaddr = request.GET.get('selectd_ipaddr', 'all')
    host_list = Host.objects.values('hostname','ssh_name','ipaddr').distinct().order_by('ssh_name')
    

    if request.method == 'POST':
        get_ipaddr = request.POST.get('ipaddr', '')
        get_ssh_name = request.POST.get('sshname', '')
        if request.POST.get('port', '') != '':
            get_port = request.POST.get('port', '')
        if request.POST.get('acceptip', '') != '':
            acceptip = request.POST.get('acceptip', '')
        get_usage = request.POST.get('usage', '')
        get_protocol = request.POST.get('protocol', '')

        if reg.match(get_ipaddr) and sub.match(acceptip):
            chgeip = request.POST.get('ipaddr', '').replace('.','')
            if re.match(r"^\d+$",get_port):
                if int(get_port) < 0 or int(get_port) > 65535: 
                    state = "port_over_limit" 
                elif int(get_port) == 0:
                    combine_id = chgeip + get_port + acceptip.replace("/","").replace(".","")
                    if Port.objects.filter(record_id=combine_id).count() is 0:
                        new_port = Port(
                            ipaddr=get_ipaddr,
                            port=get_port,
                            usage=get_usage,
                            acceptip=acceptip,
                            protocol="TCP",
                            record_id=combine_id,
                            ssh_name=get_ssh_name,
                        )
                        new_port.save()
                        state = 'success'
                    else:
                        state = 'subnet_exist'
                else:
                    combine_id = chgeip + get_port
                    if Port.objects.filter(record_id=combine_id).count() is 0:
                        new_port = Port(
                            ipaddr=get_ipaddr,
                            port=get_port,
                            usage=get_usage,
                            protocol=get_protocol,
                            acceptip=acceptip,
                            record_id=combine_id,
                            ssh_name=get_ssh_name,
                        )
                    	new_port.save()
                        state = 'success'
                    else:
                        state = 'port_exist'


            elif re.match(r"^(\d+)~(\d+)$",get_port):
                add_port_list = re.match(r"^(\d+)~(\d+)$",get_port).group(0).split('~')
                lport = add_port_list[0]
                rport = add_port_list[1]
                if int(rport) - int(lport) > 0 and int(lport) > 1 and int(rport) < 65535 and int(lport) > 1 and int(rport) < 65535 and int(rport) - int(lport) < 100:
                    for port in range(int(lport),(int(rport)+1)):
                        combine_id = chgeip + str(port)
                        if Port.objects.filter(record_id=combine_id).count() is 0: 
                            new_port = Port(
                                ipaddr=get_ipaddr,
                                port=str(port),
                                usage=get_usage,
                	            protocol=get_protocol,
                                acceptip=acceptip,
                                record_id=combine_id,
                                ssh_name=get_ssh_name,
                            )
                            new_port.save()
                            state = 'success'
                        else:
                            exists_port.append(str(port)) 
                            state = "some_add_port_fail"
                else:
                    state = 'illegal_port'


            elif re.match(r"^((\d+),)+(\d+)$",get_port):
                add_port_list = re.match(r"((\d+),)+(\d+)",get_port).group(0).split(',') 
                for port in add_port_list:
                    if int(port) < 1 or int(port) > 65535:
                        state =" illegal_port"
                    else:
                        combine_id = chgeip + port
                        if Port.objects.filter(record_id=combine_id).count() is 0:
                            new_port = Port(
                                ipaddr=get_ipaddr,
                                port=port,
                                usage=get_usage,
                	            protocol=get_protocol,
                                acceptip=acceptip,
                                record_id=combine_id,
                                ssh_name=get_ssh_name,
                            )
                            new_port.save()
                            state = 'success'
                        else:
                            exists_port.append(port)
                            state = "some_add_port_fail"
            else:
                state = 'illegal_port'

        elif sub.match(acceptip):
            get_ipaddr = ''
            state = 'illegal_ipaddress'
        else:
            acceptip = ''
            state = 'illegal_subnet'
    else:
        pass


    content = {
        'user': user,
        'active_menu': 'add_port',
        'host_list': host_list,
        'ipaddr': get_ipaddr,
        'port': get_port,
        'usage': get_usage,
        'acceptip': acceptip,
        'exists_port': exists_port,
        'query_ipaddr': query_ipaddr,
        'state': state,
    }
    return render(request, 'management/add_port.html', content)



@user_passes_test(permission_check)
def view_port(request):
    state = None
    user = request.user if request.user.is_authenticated() else None
    ipaddr_list = Host.objects.values('ssh_name','hostname','ipaddr').distinct().order_by('ssh_name')
    query_ipaddr = request.GET.get('ipaddr', 'all')
    if (not query_ipaddr) or Port.objects.filter(ipaddr=query_ipaddr).count() is 0:
        query_ipaddr = 'all'
        port_list = Port.objects.all().order_by('ssh_name')
    else:
        port_list = Port.objects.filter(ipaddr=query_ipaddr).order_by('port')

    if request.method == 'POST':
        if request.POST.has_key('delete'):
            try:
                get_record_id = request.POST.get('record_id', '')
                Port.objects.filter(record_id=get_record_id).delete()
                query_ipaddr = request.POST.get('ipaddr', '')
                state = 'delete_success'
            except Exception as e:
                state = 'delete_fail'
        elif request.POST.has_key('modify'):
            try:
                get_record_id = request.POST.get('record_id', '')
                get_protocol = request.POST.get('protocol', '')
                get_usage = request.POST.get('usage', '')
                get_acceptip = request.POST.get('acceptip', '')
                if request.POST.get('port', '') != '':
                    get_port = request.POST.get('port', '')
                    chgeip = request.POST.get('ipaddr', '').replace('.','')
                    combine_id = chgeip + request.POST.get('port', '')
                    if Port.objects.filter(record_id=combine_id).count() is 0:
                        if get_acceptip != '' and sub.match(get_acceptip):
                            Port.objects.filter(record_id=get_record_id).update(acceptip=get_acceptip)
                            if get_usage != '':
                                Port.objects.filter(record_id=get_record_id).update(usage=get_usage)
                            Port.objects.filter(record_id=get_record_id).update(port=get_port) 
                            Port.objects.filter(record_id=get_record_id).update(protocol=get_protocol) 
                            Port.objects.filter(record_id=get_record_id).update(record_id=combine_id)
                            query_ipaddr = request.POST.get('ipaddr', '')
                            state = 'modify_success'
                        else:
                            state = 'illegal_subnet'
                    else:
                        state = 'port_exist'
                elif get_acceptip != '' and sub.match(get_acceptip):
                    Port.objects.filter(record_id=get_record_id).update(acceptip=get_acceptip)
                    if get_usage != '':
                        Port.objects.filter(record_id=get_record_id).update(usage=get_usage)
                    Port.objects.filter(record_id=get_record_id).update(protocol=get_protocol) 
                    get_ipaddr = request.POST.get('ipaddr', '')
                    port_list = Port.objects.filter(ipaddr=get_ipaddr)
                    state = 'modify_success'
                elif get_usage != '':
                    Port.objects.filter(record_id=get_record_id).update(usage=get_usage)
                    state = 'modify_success'
                elif get_acceptip !='' and not sub.match(get_acceptip):
                    state = 'illegal_subnet'
                else:
                    Port.objects.filter(record_id=get_record_id).update(protocol=get_protocol)
                    state = 'modify_success'

            except Exception as e:
                state = 'modify_fail'
                print e
        else:
            pass 
    else:
        pass

    paginator = Paginator(port_list, 30)
    page = request.GET.get('page')
    try:
        port_list = paginator.page(page)
    except PageNotAnInteger:
        port_list = paginator.page(1)
    except EmptyPage:
        port_list = paginator.page(paginator.num_pages)
    content = {
        'user': user,
        'active_menu': 'view_port',
        'ipaddr_list': ipaddr_list,
        'query_ipaddr': query_ipaddr,
        'port_list': port_list,
        'state': state,
    }
    return render(request, 'management/view_port.html', content)


@user_passes_test(permission_check)
def view_host(request):
    state = None
    user = request.user if request.user.is_authenticated() else None
    ipaddr_list = Host.objects.values('ipaddr','hostname','ssh_name').order_by('ssh_name')

    for hn_ip in ipaddr_list:
        query_ipaddr = hn_ip["ipaddr"]
        detail_port = Port.objects.filter(ipaddr=query_ipaddr)
        host = Host.objects.values('hostname').filter(ipaddr=query_ipaddr)[0]['hostname']
        iptables = gen_rules(host, detail_port)
        hn_ip["iptables"] = iptables

    ## 表格输入请求处理
    if request.method == 'POST':
        keyword = request.POST.get('keyword', '')
        if Host.objects.filter(hostname__contains=keyword).count() is 0:
            if Host.objects.filter(ipaddr__contains=keyword).count() is 0:
                ipaddr_list = Host.objects.filter(ssh_name__contains=keyword).values().order_by('ssh_name')
            else:
                ipaddr_list = Host.objects.filter(ipaddr__contains=keyword).values().order_by('ssh_name')
        else:
            ipaddr_list = Host.objects.filter(hostname__contains=keyword).values().order_by('ssh_name')

        for hn_ip in ipaddr_list:
            query_ipaddr = hn_ip["ipaddr"]
            detail_port = Port.objects.filter(ipaddr=query_ipaddr)
            iptables = gen_rules(host, detail_port)
            hn_ip["iptables"] = iptables
        ## 删除请求
        if request.POST.has_key('delete'):
            try:
                get_sshname = request.POST.get('sshname', '') 
                get_ipaddr = Host.objects.filter(ssh_name=get_sshname).values('ipaddr')[0]["ipaddr"]
                Port.objects.filter(ipaddr=get_ipaddr).delete() 
                Host.objects.filter(ipaddr=get_ipaddr).delete()
                state = 'delete_success'
            except Exception as e:
                state = 'delete_fail'
                print e
        ## 修改请求
        elif request.POST.has_key('modify'):
            try:
                get_hostname = request.POST.get('hostname', '')
                get_sshname = request.POST.get('sshname', '')
                get_ipaddr = request.POST.get('ipaddr', '')
                if reg_ip.search(get_ipaddr):
                    origin_ipaddr = request.POST.get('originip', '')
                    match_hostname = Host.objects.filter(ipaddr=origin_ipaddr).values('hostname')[0]["hostname"]
                    if Host.objects.filter(ssh_name=get_sshname).count() is 0 or get_hostname == match_hostname:
                        if Host.objects.filter(ipaddr=get_ipaddr).count() is 0 :
                            port_list = Port.objects.values('port').filter(ipaddr=origin_ipaddr) 
                            for port in port_list:
                                up_record_id = get_ipaddr + str(port)
                                Port.objects.filter(ipaddr=get_ipaddr).update(record_id=up_record_id)
                            if Host.objects.filter(ssh_name=get_sshname).count() is 0 :
                                Host.objects.filter(ipaddr=origin_ipaddr).update(hostname=get_hostname)
                                Host.objects.filter(ipaddr=origin_ipaddr).update(ssh_name=get_sshname)
                                Host.objects.filter(ssh_name=get_sshname).update(ipaddr=get_ipaddr)
                            else:
                                state = 'sshname_exists'
                        else:
                            Host.objects.filter(ipaddr=origin_ipaddr).update(hostname=get_hostname)
                        state = 'modify_success'
                    else:
                        state = 'hostname_exists'
                else:
                    state = "ip_formate_fail"
            except Exception as e:
                state = str(e) 
        ## 批量删除请求
        elif request.POST.has_key('delete_many'):
            try:
                for ip in request.POST.getlist("subcheck"):
                    Port.objects.filter(ipaddr=ip).delete()
                    Host.objects.filter(ipaddr=ip).delete()
                state = "delete_success"
            except Exception as e:
                state = str(e)
        else:
            pass
            #state = 'error'
    else:
        pass
    paginator = Paginator(ipaddr_list, 30)
    page = request.GET.get('page') 
    try:
        ipaddr_list = paginator.page(page)
    except PageNotAnInteger:
        ipaddr_list = paginator.page(1)
    except EmptyPage:
        ipaddr_list = paginator.page(paginator.num_pages)

    content = {
        'user': user,
        'active_menu': 'view_host',
        'ipaddr_list': ipaddr_list,
        'state': state,
    }
    return render(request, 'management/view_host.html', content)


def dump_data(request):
    data = {} 
    host_list = Host.objects.all()
    for host in host_list:
        tmp = []
        port_list = Port.objects.filter(ipaddr=host.ipaddr).filter(acceptip__contains="0.0.0.0").filter(protocol__contains="TCP")
        for port in port_list:
            if port.port not in [0, 4369, 5672, 16302, 4949, 873]:
                tmp.append(int(port.port))
        data[host.hostname] = { "ip": host.ipaddr, "port_list": tmp }
    return JsonResponse(data)

def export_csv(request):
    sshname = request.GET.get('sshname')
    if sshname == "default":
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="'+sshname+'.csv"'
        writer = csv.writer(response)
        writer.writerow(['IP地址:', '(必填)', '', '主机名:', '(必填)', '', 'ssh名:', '(必填)'])
        writer.writerow(['说明：按列输入数据，端口范围0-65535，源地址需要网段格式，用途可以包含中英文，协议是TCP,UDP,TCPUDP三选一，留空即为TCP。'])
        writer.writerow(['端口', '', '源地址', '', '用途', '', '协议'])

        return response

    else:
        host_info = Host.objects.filter(ssh_name=sshname)[0]
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="'+host_info.ssh_name+'.csv"'

        data_list = Port.objects.filter(ssh_name=sshname)
    
        writer = csv.writer(response)
        writer.writerow(['IP地址:', host_info.ipaddr, '', '主机名:', host_info.hostname, ''])
        writer.writerow([])
        writer.writerow(['端口', '', '源地址', '', '用途', '', '协议'])
        for i in data_list: 
            if i.port == "0":
                continue
            if i.acceptip[-1] == ",":
                acceptip = i.acceptip[:-1]
            else:
                acceptip = i.acceptip
            writer.writerow([i.port, '', acceptip, '', i.usage, '', i.protocol])

        return response    


def import_csv(request):
    status = ""
    if request.method == 'POST' and request.FILES.getlist('file'):
        try:
            if not os.path.exists('upload/'):
                os.mkdir('upload/')
       
            for fs in request.FILES.getlist('file'):
                if re.match('(.*).csv$',fs.name):
                    fn_tag = True
                else:
                    fn_tag = False
                with open('upload/' + str(fs.name), 'wb+') as destination:
                    for chunk in fs.chunks():
                        destination.write(chunk)
                with open('upload/' + str(fs.name), 'r') as fr:
                    import_data = fr.readlines()

                get_ip = import_data[0].split(',')[1]
                get_hn = import_data[0].split(',')[4]
                get_ssh = import_data[0].split(',')[7]

                if reg.match(get_ip) and get_hn != "" and fn_tag:
                    check = True
                    for num in range(3,len(import_data)):
                        data = import_data[num].split(',,')
                        if re.match('\d+',data[0]) and int(data[0]) > 0 and int(data[0]) < 65535 and sub.match(data[1].replace('"','')) and data[2] != "":
                            continue
                        else:
                            check = False
                            break
                        if Host.objects.filter(ipaddr=get_ip).count() is 0 and Host.objects.filter(hostname=get_hn).count() is 0 and Host.objects.filter(ssh_name=get_ssh).count() is 0:
                            new_host = Host(
                                hostname=get_hn,
                                ipaddr=get_ip,
                                ssh_name=get_ssh,
                            )
                            new_host.save()
                            for num in range(3,len(import_data)):
                                combine_id = get_ip.replace(".","") + str(int(import_data[num].split(',,')[0]))
                                if Port.objects.filter(record_id=combine_id).count() is 0:
                                    data = import_data[num].split(',,')
                                    if data[3] == "":
                                        data[3] = "TCP"
                                    else:
                                        data[3] = data[3].split(",")[0]
                                    new_port = Port(
                                        ipaddr=get_ip,
                                        port=int(data[0]),
                                        usage=data[2],
                                        acceptip=data[1].replace('"',''),
                                        protocol=data[3],
                                        record_id=combine_id,
                                        ssh_name=get_ssh,
                                    )
                                    new_port.save()
                            state = "upload_success"
                        else:
                            state = "ip_or_hostname_exists"
                    else:
                        state = "file_content_error"
                else:
                    state = "file_format_error"
        except Exception as e:
            state = "unknown_error"
            status = str(e)
    else:
        state = "unknow_request"
        status = request
    content = {
        'state': state,
        'status': status,
    }
    return render(request, 'management/import_csv.html', content)

