#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'pcer'

import asyncio, os, inspect, logging, functools

from urllib import parse

from aiohttp import web

from apis import APIError

def get(path):
    '''
    Define decorator @get('/path')
    '''
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'GET'
        wrapper.__route__ = path
        return wrapper
    return decorator

def post(path):
    '''
    Define decorator @post('/path')
    '''
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'POST'
        wrapper.__route__ = path
        return wrapper
    return decorator

# 得到没有默认值的命名关键字参数
def get_required_kw_args(fn):
    args = []
    # 获得函数签名的参数，返回一个mapping
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        # KEYWORD_ONLY:参数的类型必须是命名关键字参数
        # inspect.Parameter.empty : 没有默认值
        if param.kind == inspect.Parameter.KEYWORD_ONLY and param.default == inspect.Parameter.empty:
            args.append(name)
    return tuple(args)

# 得到所有命名关键字参数
def get_named_kw_args(fn):
    args = []
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            args.append(name)
    return tuple(args)

# 是否有命名关键字参数
def has_named_kw_args(fn):
    params = inspect.signature(fn).parameters
    for name, param in params.items():
            if param.kind == inspect.Parameter.KEYWORD_ONLY:
                return True

# 是否有关键字参数
def has_var_kw_arg(fn):
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        # VAR_KEYWORD: 
        #A dict of keyword arguments that aren’t bound to any other parameter. This corresponds to a **kwargs parameter in a Python function definition
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            return True

def has_request_arg(fn):
    sig = inspect.signature(fn)
    params = sig.parameters
    found = False
    for name, param in params.items():
        if name == 'request':
            found = True
            continue
        # VAR_POSTITIONAL: This corresponds to a *args parameter in a Python function definition.
        if found and (param.kind != inspect.Parameter.VAR_POSITIONAL and param.kind != inspect.Parameter.KEYWORD_ONLY and param.kind != inspect.Parameter.VAR_KEYWORD):
            raise ValueError('request parameter must be the last named parameter in function: %s%s' % (fn.__name__, str(sig)))
    return found


class RequestHandler(object):
    def __init__(self, app, fn):
        self._app = app
        self._func = fn
        self._has_request_arg = has_request_arg(fn)
        self._has_var_kw_arg = has_var_kw_arg(fn)
        self._has_named_kw_args = has_named_kw_args(fn)
        self._named_kw_args = get_named_kw_args(fn)
        self._required_kw_args = get_required_kw_args(fn)



    # __call__: Instances of arbitrary classes can be made callable by defining a __call__() method in their class.
    async def __call__(self, request):
        kw = None
        # 如果URL处理函数有"**kw", "*, arg"形式参数，则需要解析HTTP请求的数据
        if self._has_var_kw_arg or self._has_named_kw_args or self._required_kw_args:
            # 如果是POST方法，kw等于请求体的数据
            if request.method == 'POST':
                if not request.content_type:
                    return web.HTTPBadRequest('Missing Content-Type.')
                ct = request.content_type.lower()
                # startswith: The method startswith() checks whether string starts with str
                if ct.startswith('application/json'):
                	# request.json: Read request body decoded as json.
                    params = await request.json()
                    if not isinstance(params, dict):
                        return web.HTTPBadRequest('JSON body must be object')
                    kw = params
                elif ct.startswith('application/x-www-form-urlencodeed') or ct.startswith('multipart/form-data'):
                    # request.post: A coroutine that reads POST parameters from request body. Returns MultiDictProxy instance filled with parsed data.
                    params = await request.post()   
                    kw = dict(**params)
                else:
                    return web.HTTPBadRequest('Unsupported Content-Type: %s' % request.content_type)
            # 如果是GET方法，kw等于query_string数据
            if request.method == 'GET':
                qs = request.query_string
                if qs:
                    kw = dict()
                    # parse_qs: Parse a query string given as a string argument (data of type application/x-www-form-urlencoded). Data are returned as a dictionary.
                    for k, v in parse.parse_qs(qs, True).items():
                        kw[k] = v[0]

        # 若kw为空，那么kw将等于请求url的匹配数据（example：'/hello/{name}'， match_info['name']）
        if kw is None:
            kw = dict(**request.match_info)
        # 若kw非空，根据URL处理函数签名中的参数从kw中取出数据
        else:
            if not self._has_var_kw_arg and self._named_kw_args:
                # remove all unamed kw:
                copy = dict()
                for name in self._named_kw_args:
                    if name in kw:
                        copy[name] = kw[name]
                    kw = copy
            # check named arg:
            for k, v in request.match_info.items():
                if k in kw:
                    logging.warning('Duplicate arg name in named arg and kw arg: %s' % k)
                kw[k] = v
        # 若URL处理函数中有request参数，则将request存入kw
        if self._has_request_arg:
            kw['request'] = request
        # check require kw:
        if self._required_kw_args:
            for name in self._required_kw_args:
                if not name in kw:
                    return web.HTTPBadRequest('Missing argument: %s' % name)
        logging.info('call with args: %s' % str(kw))
        try:
            # 调用URL处理函数
            r = await self._func(**kw)          
            return r
        except APIError as e:
            return dict(error = e.error, data = e.data, message = e.message)

# Adds a router and a handler for returning static files.
def add_static(app):
    # static目录的绝对路径
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    app.router.add_static('/static/', path)
    logging.info('add static %s => %s' % ('/static/', path))


# 注册一个URL处理函数
def add_route(app, fn):
    method = getattr(fn, '__method__', None)
    path = getattr(fn, '__route__', None)
    if path is None or method is None:
        raise ValueError('@get or @post not defined in %s.' % str(fn))
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
        fn = asyncio.coroutine(fn)
    logging.info('add route %s %S => %s(%s)' % (method, path, fn.__name__, ', '.join(inspect.signature(fn).parameters.keys())))
    app.router.add_route(method, path, RequestHandler(app, fn))

def add_routes(app, module_name):
    # The method rfind() returns the last index where the substring str is found, or -1 if no such index exists
    n = module_name.rfind('.')
    if n == (-1):
        mod = __import__(module_name, globals(), locals())
    else:
        name = module_name[n + 1:]
        # __import__:This function is invoked by the import statement
        mod = getattr(__import__(module_name[:n], globals(), locals(), [name]), name)
    # dir: Without arguments, return the list of names in the current local scope. With an argument, attempt to return a list of valid attributes for that object.
    for attr in dir(mod):
        # 私有成员(_前缀)不访问
        if attr.startswith('_'):
            continue
        # 将所有url处理函数就进行注册
        fn = getattr(mod, attr)
        if callable(fn):
            method = getattr(fn, '__method__', None)
            path = getattr(fn, '__route__', None)
            if method and path:
                add_route(app, fn)
