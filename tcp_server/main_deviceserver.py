# coding: utf-8
import sys
#from gevent import monkey; monkey.patch_all()
from gevent import pool
from gevent.server import StreamServer
from gevent.pywsgi import WSGIServer
import sys,os

from os import path
root_path = path.realpath(
        path.join(path.dirname(__file__), "../..")
    )
print root_path
sys.path.append(root_path)
import device
from unity.http import dispatcher
import logging

logger = logging.getLogger()


g_session_manager = device.create_session_manager("test")


def device_handle(sock, address):
    logger.info('start new sock[%s] address[%s]', sock, address)

    sock.settimeout(10)
    session = g_session_manager.create_session(sock, address)

    session.run()

    g_session_manager.remove_session(session.get_idt())
    

def make_param(cgi_param):
    params = []
    for k in cgi_param:
        v = cgi_param[k][0]
        v = v.replace("'", r"\'") 
        params.append("%s='%s'" % (k, v))
    return ','.join(params)


if __name__ == '__main__':
    
    tcp_port = 9011
    http_port = 20011
    tcp_connect_size = 1024

    pool = pool.Pool(tcp_connect_size)
    tcp_server = StreamServer(('', tcp_port), device_handle, spawn=pool)
    http_server = WSGIServer(('', http_port), dispatcher.default_cmd_handle)
    http_server.start()
    tcp_server.serve_forever()