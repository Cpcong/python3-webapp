# python3 webapp

**基于python3.5编写**

[博客地址](http://119.29.119.139/)

基本按照[廖雪峰的python3教程](http://www.liaoxuefeng.com/wiki/0014316089557264a6b348958f449949df42a6d3a2e542c000/001432170876125c96f6cc10717484baea0c6da9bee2be4000)编写,并加了比较详尽的注释

# 用到的模块

前端框架

[vue](https://vuejs.org.cn/)
[uikit](http://getuikit.com/index.html)

第三方模块

[aiohttp](http://aiohttp.readthedocs.io/en/stable/index.html)
[jinja2](http://jinja.pocoo.org/docs/dev/)
[aiomysql](http://aiomysql.readthedocs.io/en/latest/)
    
部署工具

[fabric](http://www.fabfile.org/)
    
web服务器(处理静态资源和反向代理)

[nginx](http://nginx.org/en/)

markdown的python实现

[python-markdown2](https://github.com/trentm/python-markdown2)

# 代码结构

- www/app.py : 程序入口
- orm.py : 实现一个orm框架
- models.py : users, blogs, comments表对应的models
- coroweb.py ：在aiohttp基础上封装的web框架
- handlers.py : url处理函数
- apis.py : 自定义异常类
- config.py : 处理服务器配置文件
- config_default.py, config_override.py : 服务器配置文件(ip, dbuser...)
- fabric.py : 项目的打包和部署功能实现
- markdown2.py : python实现的markdown功能
- templates/ : 存放模板文件
- static : 存放静态资源
- conf : 存放nginx和supervisor的配置文件


# 部署命令

打包: `$ fab build`

部署: `$ fab deploy`

# 环境搭建问题

python3.5安装有问题的同学可参考以下方法

python3.5的安装(ubuntu):

1. 增加python源 `$ sudo add-apt-repository ppa:fkrull/deadsnakes`
2. update 软件列表 `$ sudo apt-get update`
3. 安装python3.5 `$ sudo apt-get install python3.5`

安装后输入`$ python3.5 -V`验证成功

接下来pip的安装:

`$ wget https://bootstrap.pypa.io/get-pip.py`

`$ sudo python3.5 get-pip.py`

安装后输入`$ pip3 -V`验证成功


        
