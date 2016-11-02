# coding: utf-8
import json
import unity
import logging
import base64
from unity import common
import os
import data_service

logger = logging.getLogger()

cmd_factory = {}


file_root_path = "/home/app/upload"

COMMON_MSG = 1
# cmd_list = ['handshake','login','heart_beat','position_report','heart_beat']


class CommonCmdProcess:
    def __init__(self):
        pass

    def process(self,request_body, client_session):
        logger.info('recv CommonCmd ' + client_session.get_idt())

        data = None
        try:
            data = json.loads(request_body, encoding="utf-8")
        except Exception, e:
            print 'CommonCmdProcess load json data error ' + client_session.get_idt()
            logger.error('CommonCmdProcess load json data error ' + client_session.get_idt())
            client_session.stop()
            return None

        cmd = unity.common.safe_get(data, 'cmd', None)
        seq = int(unity.common.safe_get(data, 'seq', None))
        if cmd is None:
            logger.info('recv error cmd %s', data)
            if "resp_body" in data:
                resp_body = data["resp_body"]
                # client_session.resp_list[seq]
                if "base64file" in resp_body:
                    base64file = resp_body["base64file"]
                    fileName = resp_body["fileName"]
                    module = resp_body["module"]
                    imgdata = base64.b64decode(base64file)
                    path = "/" + module + "/" + common.get_now_datetime("%Y/%m/%d")
                    if not os.path.exists(file_root_path + path):
                        os.makedirs(file_root_path + path)
                    path = path + "/" + client_session.get_idt() + "_" + fileName
                    file = open(file_root_path + path, 'wb')
                    file.write(imgdata)
                    file.close()
                    resp_body["base64file"] = path
            client_session.resp_list[seq] = data
            if "resp_body" in data:
                resp_body = data["resp_body"]
                if "module" in resp_body:
                    if resp_body["module"] == "client_log":
                        log = {
                               "url": resp_body["base64file"],
                               "fileName": resp_body["fileName"]
                               }
                        if hasattr(client_session, "user"):
                            log["userId"] = client_session.user["id"]
                        data_service.save_log(log)
                    elif resp_body["module"] == "client_screenshots":
                        screenshots = {"userId": client_session.user["id"],
                               "url": resp_body["base64file"],
                               "fileName": resp_body["fileName"],
                                "accuracy":  resp_body["accuracy"],
                               }
                        if hasattr(client_session, "user"):
                            screenshots["userId"] = client_session.user["id"]
                        data_service.save_screenshots(screenshots)

            return None
        else:
            cmd_body = unity.common.safe_get(data,'cmd_body', None)
            func_make = 'client_session.process_%s(cmd_body,seq)' % cmd
            resp = eval(func_make)
            return resp


def init_cmd_factory():
    
    cmd_factory[COMMON_MSG] = CommonCmdProcess()


def init():
    init_cmd_factory()


