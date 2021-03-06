#coding:utf-8
import datetime
from flask import Flask

from flask.ext import admin
from flask.ext.mongoengine import MongoEngine
from flask.ext.admin.contrib.mongoengine import ModelView
from flask.ext import admin, wtf
from wtforms import widgets
# Create application
from webadmin import app
from flask import request
from urlparse import urlparse
import pymongo
from bson.json_util import default
import json
import re
import time
import psutil
import subprocess
from multiprocessing import Process
from twisted.python import log
from bson.objectid import ObjectId
from flask import Flask,redirect
from flask import Markup



FPID = "/tmp/server_admin.pid"
FLOG = "/var/log/server_admin.log"

RUN_PATH = "{}/daemon".format(app.__rootdir__)

# Flask views
@app.route('/server_admin/')
def server_admin():
    act = request.args.get('act', '')
    if act == "status":
        try:
            pid = open(FPID, 'r').read()
            p = psutil.Process(int(pid))
            return '{"success":1, "msg":"%s"}' % p.name
        except Exception, e:
            return '{"success":0, "msg":"%s"}' % e
        
    elif act == "start":
        
        args = ["twistd",
                 "-y",
                 "%s/server.py" % RUN_PATH,
                 "--pidfile=%s" % FPID,
                 "--logfile=%s" % FLOG,
#                  "--rundir=%s/" % RUN_PATH
                 ]
        print args, "".join(args)
        
        try:
            out = subprocess.call(args)
            if out == 0:
                return '{"success":1, "msg":"ok"}'
            elif out == 1:
                return '{"success":1, "msg":"is seen already running."}'
            
        except Exception, e:
            log.err()
            return '{"success":0, "msg":"%s"}' % e


    elif act == "stop":
        try:
            pid = open(FPID, 'r').read()
            p = psutil.Process(int(pid))
            p.terminate()
            #os.system("kill -9 {}".format(pid))
            return '{"success":1, "msg":"%s"}' % p.name
        except Exception, e:
            return '{"success":0, "msg":"%s"}' % e


EC2PID = "/tmp/ec2_schd.pid"
EC2LOG = "/var/log/ec2_schd.log"

# Flask views
@app.route('/ec2_schd/')
def ec2_schd():
    act = request.args.get('act', '')
    if act == "status":
        try:
            pid = open(EC2PID, 'r').read()
            p = psutil.Process(int(pid))
            return '{"success":1, "msg":"%s"}' % p.name
        except Exception, e:
            return '{"success":0, "msg":"%s"}' % e
        
    elif act == "start":
        args = ["twistd",
                 "-y",
                 "%s/ec2_schd.py" % RUN_PATH,
                 "--pidfile=%s" % EC2PID,
                 "--logfile=%s" % EC2LOG,
#                  "--rundir=%s/" % RUN_PATH
                 ]
        try:
            out = subprocess.call(args)
            if out == 0:
                return '{"success":1, "msg":"ok"}'
            elif out == 1:
                return '{"success":1, "msg":"is seen already running."}'
            
        except Exception, e:
            log.err()
            return '{"success":0, "msg":"%s"}' % e

        
    elif act == "stop":
        try:
            pid = open(EC2PID, 'r').read()
            p = psutil.Process(int(pid))
            p.terminate()
            os.system("kill -9 %s" % pid)
            
            return '{"success":1, "msg":"%s"}' % p.name
        except Exception, e:
            return '{"success":0, "msg":"%s"}' % e


@app.route('/test_python_code/')
def test_python_code():
    act = request.args.get('act', '')
    



@app.route('/del_spider_navi/')
def del_spider_navi():
    spider_id = request.args.get('spider_id', '')
    navi_id = request.args.get('navi_id', '')
    spider = app.conn.taobao.spider.find_one({"_id":ObjectId(spider_id)})
    
    navi_list = []
    for navi in dict(spider)["navi_list"]:
        if str(navi) != navi_id:
            navi_list.append(navi)
    print navi_list
    app.conn.taobao.spider.update({"_id":ObjectId(spider_id)}, {"$set":{"navi_list":navi_list}})
    app.conn.taobao.spider_navi.remove({"_id":ObjectId(navi_id)})
    
    return redirect("/admin/Spider/")

@app.route('/schd_seed/')
def schd_seed():
    schd_id = request.args.get('schd_id', '')
    seed = app.conn.taobao.schd_seed.find_one({"_id":ObjectId(schd_id)})
    seed = dict(seed)
    
    for s in seed["seed_list"]:
        app.redis.lpush(seed["redis_key"], s)
    
    return redirect("/admin/SchdSeed/")



import os
import subprocess
import traceback
import sys
import thread
import signal

def monitor_exec(proc):
    timeout = 10
    for i in range(0, timeout):
        print "wait:%s" % i
        time.sleep(1)
    proc.kill()

@app.route('/test_py/', methods=['GET', 'POST'])
def test_py():
    
    f_name = "%s/daemon/models/test_py.py" % app.__rootdir__
    open(f_name, "w").write(request.data)
    out = subprocess.Popen(["python", f_name], stdout=subprocess.PIPE)
    td = thread.start_new_thread(monitor_exec, (out,))
        
    ret_lines = []
    for line in out.stdout:
        print(line)
        ret_lines.append(line)
    print td    
    return "</br>".join(ret_lines)

print "medule api s loaded."



@app.route('/store_remote_ip/', methods=['GET', 'POST'])
def store_remote_ip():
    from webadmin.modes import EcIP
    from flask import request
    ip = request.remote_addr
    EcIP(ip=ip).save()
    
    return ip

#------------------------------------------------------------------------------ 
try:
    from models import db
except Exception, e:
    print "#########", e
    
#http://192.168.2.201:9992/api/zhi_shu/?ktype=brand&key=%E6%90%9C%E7%B4%A2&stype=query&val=11111
    
@app.route('/api/zhishu/', methods=['GET', 'POST'])
def update_zhishu():
    from flask import request
    ktype = request.args.get('ktype')
    key = request.args.get('key')
    stype = request.args.get('stype')
    val = request.args.get('val')

    print ktype, key, stype, val, "##############"

    ret = None
    if ktype == "brand":
        if stype == "query":
            ret = db.execute('UPDATE ataobao2.brand SET search_index=:search_index WHERE name =:name',
                        dict(search_index=int(val), name=key)
                        )
        elif stype == "trade":
            ret = db.execute('UPDATE ataobao2.brand SET sales_index=:sales_index WHERE name =:name',
                        dict(sales_index=int(val), name=key)
                        )
    elif ktype == "cate":
        if stype == "query":
            ret = db.execute('UPDATE ataobao2.cate SET search_index=:search_index WHERE id =:id',
                        dict(search_index=int(val), id=int(key))
                        )
        elif stype == "trade":
            pass
    return str(ret)
