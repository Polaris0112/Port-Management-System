# Port-Management-System
# 端口管理系统



Github 开源项目地址： https://github.com/Polaris0112/Port-Management-System ，欢迎Start ：）



## 简述
该项目是基于Django编写的端口管理系统，可以通过Django后台更改密码。本管理系统包含了基础用户注册、登入登出功能，根据主机分类和根据端口分类的界面，提供增、删、改、查功能，通过页面管理导入或者导出csv进行批量添加和删除主机和端口信息，还有根据端口信息生成对应的iptables规则脚本。

部分效果图如下：

### 主页

![index.png](https://github.com/Polaris0112/Port-Management-System/blob/master/demonstration/index.png)

### 主机信息查看页面

![view_hosts.png](https://github.com/Polaris0112/Port-Management-System/blob/master/demonstration/view_hosts.png)

### 端口信息查看页面

![view_ports.png](https://github.com/Polaris0112/Port-Management-System/blob/master/demonstration/view_ports.png)



更多效果图展示请按[这里](https://github.com/Polaris0112/Port-Management-System/tree/master/demonstration)



## 部署环境

-  python2.7.x

-  mysql

-  nmap




## 安装部署

-  安装好mysql，确定数据库名、数据库用户名和数据库密码

-  推荐：进入virtualenv，安装所需要的依赖包，`pip install  -r requirement.txt`

-  需要对几个文件进行配置编辑：
  -  ./PM/setting.py  ：这个文件76行开始的json需要补充db相关信息，如数据库名，用户名和密码
  -  ./db_update.py  ：这个文件13-16行也是需要补充db信息如上
  -  ./roles/fetch_files/tasks/main.yml   ：这个文件第10行`dest: "{ pwd }/port_data/"`其中的`{ pwd }`换成当前目录，也就是`dest:`的值是指向当前目录下的`port_data`文件夹
  -  ./external_hosts ：这个文件是按照ansible的格式来定义，`test`是组别名（可自定义），然后下面每一行的第一列是服务器的备注名（我一般是用ssh名来命名，不过可以自定义），第二列是`ansible_ssh_host=`后面是需要收集的服务器ip地址
  -  （需要域名访问才更改）./port_uWSGI.ini  ：这个文件第6行的`chdir`对应的路径改成当前文件夹路径，第10行的`home`对应的路径改成当前使用的env路径

-  建立数据库模板，进入`Port-Management-System`文件夹，执行`python manage.py migrate`

正常情况下出现的信息是：

```bash
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, management, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying auth.0007_alter_validators_add_error_messages... OK
  Applying auth.0008_alter_user_username_max_length... OK
  Applying management.0001_initial... OK
  Applying management.0002_auto_20170925_1115... OK
  Applying sessions.0001_initial... OK
```

再查看数据库对应的表，会发现模板已经建好

-  **先创建Django超级管理员账号`python manage.py createsuperuser`，按提示输入即可，需要记住账号密码**

-  **登录入数据库，进入你所创建的库中，输入`insert into management_myuser (nickname,permission,user_id) values ("admin","3","1");`（假设你创建的管理员账号名为`admin`）**

-  再运行`python manage.py runserver 0.0.0.0:10066`（端口可以自定义，只要不要用到已使用端口就可以），从浏览器访问对应http://ip:10066 ，就能看到登录界面，初始账号密码为上述两步所创建的。

- （域名访问的看这里）确认已经修改好port_uWSGI.ini文件，然后在nginx上创建好对应域名监听对应的端口，然后uwsgi --ini port_uWSGI.ini（注意：如果是这种方式的话，不需要执行上一步的runserver，这一步的uwsgi已经会启动程序）





## 项目模块解释

- PM：Django的容器，Port-Management缩写
  -  ./PM/__init__.py： 一个空文件，告诉 Python 该目录是一个 Python 包。
  -  ./PM/settings.py： 该 Django 项目的设置/配置。
  -  ./PM/urls.py： 该 Django 项目的 URL 声明; 一份由 Django 驱动的网站"目录"。
  -  ./PM/wsgi.py： 一个 WSGI 兼容的 Web 服务器的入口，以便运行你的项目。

- management：Django的app内容，存放网页对应操作逻辑脚本
  - ./management/admin.py： 用户管理定义
  - ./management/apps.py： django的app定义
  - ./management/gen_iptables.py：生成iptables的逻辑脚本
  - ./management/migrations：该文件夹下的都是每次数据库迭代、迁移用的
  - ./management/models.py：当前数据库存储的数据类型模型
  - ./management/static：网页所需css、fonts、images、js文件
  - ./management/urls.py：定义了网页uri跳转到指定的网页文件中
  - ./management/views.py：定义了网页中所有操作触发的逻辑

- templates：存储网页文件模板
  - ./templates/management/base.html：定义整个网页导航栏的部分
  - ./templates/management/index.html：定义管理界面主页
  - ./templates/management/set_password.html：定义设置密码页面
  - ./templates/management/login.html：定义登录页面
  - ./templates/management/signup.html：定义注册页面
  - ./templates/management/add_host.html：定义添加主机页面
  - ./templates/management/add_port.html：定义添加端口页面
  - ./templates/management/view_host.html：定义查看主机页面
  - ./templates/management/view_port.html：定义查看端口页面
  - ./templates/management/import_csv.html：定义导入csv批量操作页面
  - ./templates/management/export_csv.html：定义导出csv批量操作页面

- rules：该目录是用于定义生成防火墙配置的固有规则
  -  该目录下的文件，文件名以`external_hosts`中的组别名为名，里面以json形成，不能修改key的情况下填入对应的值。
  
  （原意：是因为远程登录到服务器上取端口信息并不能获取到该端口允许哪些服务器发过来的包，如我只想我的zabbix客户端10050端口只收到某服务端发来的请求信息，那么我就可以在这里定义`acceptip`来批量设置指定组下服务器的统一规则。）

-  port_data：该目录是存放抓取到的端口信息（未整理）

-  build_data：该目录是从`port_data`中获取数据源来规范化端口信息（已整理）

-  upload：接受上传的csv文件，这个是网页中的其中一个功能，批量处理相关

-  script-iptables：保存生成的iptables.sh文件

-  external_hosts：调用ansible时候使用的hosts文件

-  Fetch_files.yml：运行ansible使用的playbook

-  roles：该文件夹是运行playbook对应的roles逻辑

-  db_update.py：用于对`port_data`数据清洗，并对已处理的`build_data`中的数据进行入库

-  update.sh：用于简单调用的工具，一条命令更新对应的信息


## 工具使用

- update.sh：添加、更新工具，依赖db_update.py和ansible
   - usage : sh update.sh [组名或all] 
   这里组名是根据`external_hosts`（ansible hosts文件格式）的组名来定义，如果`all`就代表hosts文件所有的服务器都会逐个去抓取信息并更新到数据库中。


## 交流、反馈和建议

- 邮箱：jjc27017@gmail.com

- 欢迎各位Fork和Star，也欢迎各位提issue，我会尽快回答
