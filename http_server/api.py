#!/usr/bin/env python2.7
# coding:utf-8
import sys, os
reload(sys)
sys.setdefaultencoding('utf-8')
from os import path
sys.path.append(
    path.realpath(
        path.join(path.dirname(__file__), "../..")
    )
)
import unity.common
unity.common.ApplicationInstance(__file__)
from gevent.pywsgi import WSGIServer
logfile_path = path.join(path.dirname(__file__))
import logging.config
logging.config.fileConfig(logfile_path+"/api_logging.conf")
import logging
from unity.http import dispatcher
from unity import service, core, common
logger = logging.getLogger()


def hello(request_body):
    return core.CommonResult(0, {"key": "value"})
	
dispatcher.init_path_handler({
    "helloworld": hello,
})

if __name__ == '__main__':
    http_port = 5009

    #service.init_redis_service("120.25.65.11", 6379, 6, 'adsfewtexxv21')
    #service.init_mysql_service('mysql://smart:Smart2014@rdsegx50os45b62evour.mysql.rds.aliyuncs.com:3306/elife_device?charset=utf8')

    http_server = WSGIServer(('', http_port), dispatcher.default_cmd_handle)
    http_server.start()
    http_server.serve_forever()
