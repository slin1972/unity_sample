# coding: utf-8

import sys
import re
from os import path
import logging.config
import device
import unity


logfile_path = path.join(path.dirname(__file__))
logging.config.fileConfig(logfile_path+"/logging.conf")

unity.http.dispatcher.init_path_handler({
    "command/send": device.http_handler.action,
})

# init console cmd args
console_cmd_args = {}
for cmd in sys.argv:
    match = re.search("--.*=", cmd)
    if match:
        key = match.group()[2:-1]
        value = cmd[match.end():]
        console_cmd_args[key] = value

print "CMD ARGS", console_cmd_args

config_g = {}

SERVER_PORT = 10051
SERVER_NAME = "mart_3351"

from unity import service

service.init_mysql_service("mysql://gorilla:App@09Z!@121.199.18.180:3306/hupai?charset=utf8")
# service.init_redis_service("192.168.0.140", 6379, 6, 'foobared')
# service.init_mysql_service('mysql://root:root@192.168.0.140:3306/costmanage?charset=utf8')
##service.init_mysql_service('mysql://smart:Devond_0224@devond-test-db.cd7fjqjzvwpd.ap-southeast-1.rds.amazonaws.com:3306/costmanage?charset=utf8')


