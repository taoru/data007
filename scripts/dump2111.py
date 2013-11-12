#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import time
import redis
import struct
import socket
from cqlutils import ConnectionPool

r1 = redis.Redis()
r2 = redis.Redis(host='192.168.2.111')
db1 =  ConnectionPool(['localhost:9160'])
db2 =  ConnectionPool(['192.168.2.111:9160'])

schemafile = os.path.join(os.path.dirname(__file__), '..', 'schema.cql')

schemacontent = open(schemafile).read()

schemas = {}
for table, schema in re.compile(r'CREATE TABLE IF NOT EXISTS (\S+) \((.*?)\);', re.DOTALL).findall(schemacontent):
    fields = []
    for col in schema.split('\n'):
        col = col.strip()
        if col and not col.startswith('PRIMARY'):
            col = col.split(' ', 1)[0]
            fields.append(col)
    schemas['ataobao2.'+table] = fields

def sync_table(table, fields):
    f1 = ', '.join(fields)
    print 'migrating {}'.format(table)

    with db1.connection() as cur:
        print f1, table
        cur.execute('select {} from {} limit 1000000'.format(f1, table), consistency_level='ONE')
        for i, row in enumerate(cur):
            if i % 1000 == 0:
                print 'syncd {}'.format(i)
            params = {}
            fs = list(fields)
            for k,v in zip(fields, row):
                if k == 'date':
                    v = struct.unpack('!q', v)[0]
                if v is not None:
                    params[k] = v 
                else:
                    fs.remove(k) 
            f1 = ', '.join(fs)
            f2 = ', '.join([':'+f for f in fs])
            #print 'INSERT INTO {} ({}) VALUES ({})'.format(table, f1, f2), params
            db2.execute('insert into {} ({}) values ({})'.format(table, f1, f2), params)
    
def sync_all():
    for table, fields in schemas.iteritems():
        if table not in ['ataobao2.item_attr']:
            sync_table(table, fields)

def sync_redis():
    r2.slaveof('no', 'one')
    ip = socket.gethostbyname(socket.gethostname())
    print "slaveof {} {}".format(ip, 6379)
    ok = r2.slaveof(ip, 6379)
    if not ok:
        print "can't do slaveof to {}:{}".format(ip, 6379)
        return 
    while True:
        time.sleep(3)
        print('check for sync')
        sync = True
        r2info = r2.info()
        for key, value in r1.info().items():
            if key.startswith('db'):
                if key not in r2info: 
                    sync = False
                    break
                if value['keys'] != r2info[key]['keys']:
                    sync = False
                    break
        if sync:
            break
    r2.slaveof('no', 'one')

if __name__ == '__main__':
    sync_redis()
    sync_all()
