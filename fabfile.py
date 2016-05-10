#!/usr/bin/env python
# -*- coding:utf-8 -*-

__auth__ = 'pcer'

'''
Deployment toolkit
'''

import os, re

from datetime import datetime
from fabric.api import *

env.user = 'ubuntu'
env.sudo_user = 'root'
env.hosts = ['119.29.119.139']

db_user = 'www'
db_password = 'www'

_TAR_FILE = 'dist-awesome.tar.gz'

_REMOTE_TMP_TAR = '/tmp/%s' % _TAR_FILE

_REMOTE_BASE_DIR = '/srv/awesome'

def _current_path():
    return os.path.abspath('.')

def _now():
    return datetime.now().strftime('%y-%m-%d_%H.%M.%S')

def build():
    '''
    Build dist package
    '''
    includes = ['static', 'templates', 'favicon.ico', '*.py']
    excludes = ['test', '.*', '*.pyc', '*.pyo']
    local('rm -f dist/%s' % _TAR_FILE)
    # with lcd(path)可以把当前命令的目录设定为lcd()指定的目录
    with lcd(os.path.join(_current_path(), 'www')):
        cmd = ['tar', '--dereference', '-czvf', '../dist/%s' % _TAR_FILE] # --dereference: 归档符号链接指向的文件
        cmd.extend(['--exclude=\'%s\'' % ex for ex in excludes])
        cmd.extend(includes)
        # 执行命令
        local(' '.join(cmd))

def deploy():
    newdir = 'www-%s' % _now()
    # 删除已有的tar文件:
    run('rm -f %s' % _REMOTE_TMP_TAR) # run: Run a shell command on a remote host
    # 上传新的tar文件:
    put('dist/%s' % _TAR_FILE, _REMOTE_TMP_TAR)
    with cd(_REMOTE_BASE_DIR):
         # 创建新目录:
        sudo('mkdir %s' % newdir)
    with cd('%s/%s' % (_REMOTE_BASE_DIR, newdir)):
        # 解压到新目录:
        sudo('tar -xzvf %s' % _REMOTE_TMP_TAR)
    # 重置软链接:
    with cd(_REMOTE_BASE_DIR):
        sudo('rm -f www')
        sudo('ln -s %s www' % newdir)
        sudo('chown ubuntu:ubuntu www')
        sudo('chown -R ubuntu:ubuntu %s' % newdir)
    # 重启Python服务和nginx服务器:
    with settings(warn_only = True):
        sudo('supervisorctl stop awesome')
        sudo('supervisorctl start awesome')
        sudo('/etc/init.d/nginx reload')

RE_FILES = re.compile('\r?\n')

