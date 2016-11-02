# coding: utf-8
import struct
import time
import json
import unity
import logging
import cmd_handler
import common
from unity.tcp import sessions
import data_service
import binascii
import gevent

logger = logging.getLogger()

MESSAGE_HEAD = 4

g_user_list = {
}

def unpack_head(head_data):
    if len(head_data) is not MESSAGE_HEAD:
        return None
    fmt = ['!',
        'I',  #payload_length
    ]
    items = struct.unpack(''.join(fmt), head_data) 
    payload_len = items[0]

    return payload_len


def unpack_payload(data):
    if data is None:
        return None
    length = len(data)
    fmt=['!',]
    fmt.append('%ds' % (length,))  #payload
    #fmt.append('B') #checksum

    items = struct.unpack(''.join(fmt), data)
    payload = items[0]
    #checksum = items[1]

    return payload


def pack_msg(msg):
    if msg is None:
        return None
    length = len(msg)

    fmt = ['!',
        'I',  #payload_length
        '%ds'   %len(msg)
    ]
    data = struct.pack(''.join(fmt),length,msg)
    return data


class DeviceSession(sessions.session.Session):
    def __init__(self,sock,serail_num,cmd_factory):
        sessions.session.Session.__init__(self,sock,cmd_factory)
        self.seq = 1
        self.idt = serail_num
        self.resp_list = {}
        self.version = "1.0.0"
        logger.info('init new DeviceSession[%s]' % (serail_num))

    def create_finished(self):
        pass
        # self.data_service.add_online_device(self.server_identify, self.get_idt(), int(time.time()))

    def remove_finished(self):
        print "execute remove_finished."
        if hasattr(self, "user"):
            if self.user["username"] in g_user_list:
                user = g_user_list[self.user["username"]]
                print self.user["serailNum"], user["serailNum"]
                if self.user["serailNum"] == user["serailNum"]:
                    del g_user_list[self.user["username"]]
                    data_service.offline(self.user)
            pass
        # self.data_service.del_online_device(self.server_identify, self.get_idt())

    @staticmethod
    def create_session(sock,head,address):
        logger.info('create DeviceSession from address[%s]',address)

        sock.settimeout(5)
        head_data = ''
        body_data = ''
        left_data = ''
        if len(head) >= MESSAGE_HEAD:
            head_data = head[:MESSAGE_HEAD]
            body_data = head[MESSAGE_HEAD:]
        elif len(head) >= 0:
            head_data = head
            head_data += common.recv_n(sock,MESSAGE_HEAD - len(head))

        body_len = unpack_head(head_data)
        print 'body_len:',body_len
        print 'head[%s]' %binascii.b2a_hex(head_data)
        if len(body_data) >= body_len:
            left_data = body_data[body_len:]
            body_data = body_data[:body_len]
        else:
            body_data += common.recv_n(sock,body_len - len(body_data))

        left_data = head_data + body_data + left_data
        body = unpack_payload(body_data)
        logger.info('DeviceSession process_merchant_handshake handshake_data[%s]',body)

        handshake_data = None
        try:
            handshake_data = json.loads(body,encoding="utf-8")
        except Exception, e:
            logger.error('create DeviceSession error ' + str(e))
            return None,left_data

        print handshake_data

        cmd = unity.common.safe_get(handshake_data,'cmd',None)
        seq = unity.common.safe_get(handshake_data,'seq',None)
        
        if cmd is None or str(cmd) != 'handshake':
            logger.error('create DeviceSession error  not handshake_cmd ')
            return None,left_data

        cmd_body = unity.common.safe_get(handshake_data,'cmd_body',None)
        if cmd_body is None:
            logger.error('create DeviceSession error  not handshake_cmd body ')
            return None,left_data

        serail_num = unity.common.safe_get(cmd_body, 'serail_num', None)
        # password = unity.common.safe_get(cmd_body, 'password', None)
        #
        # if username is None or password is None:
        #     run_log.error('create DeviceSession error  not handshake_cmd body param lost ')
        #     return None, left_data
        #
        # user = data_service.login(username, password)
        #
        # if user is None:
        #     run_log.error('User not exist. ')
        #     return None, left_data
        # else:
        ed_session = DeviceSession(sock, serail_num, cmd_handler.cmd_factory)
        ed_session.send_result(0, "success", seq)
        return ed_session, None #left_data[MESSAGE_HEAD + body_len:]

    def recv_message(self):
        logger.info('DeviceSession recv_message')
        head_data = common.recv_n(self.sock,MESSAGE_HEAD)
        body_len = unpack_head(head_data)
        body_data = common.recv_n(self.sock,body_len)
        body = unpack_payload(body_data)
        print 'recv_message : ' + body
        logger.info('recv_message' + body)

        self.last_recv_time = int(time.time())
        return cmd_handler.COMMON_MSG, body

    def send_message(self,msg):
        print "send_message : %s" % msg
        logger.info('DeviceSession send_message[%s]',msg)
        msg = pack_msg(msg)
        self.send_queue.put(msg)
        return True

    def send_result(self, code, msg, seq, resp=None):
        self.send_message(json.dumps({
            "code": code,
            "msg": msg,
            "seq": seq + 1,
            "resp_body": resp
        }))

    def send_request(self, cmd, cmd_body=None):
        dt = {
            "cmd": cmd,
            "seq": self.seq,
            "version": self.version,
        }
        if cmd_body is not None:
            dt["cmd_body"] = cmd_body
        self.send_message(json.dumps(dt))
        seq = self.seq
        self.seq += 2
        ctime = time.time()
        while time.time() - ctime < 60:
            gevent.sleep(1)
            if seq + 1 in self.resp_list:
                v = self.resp_list[seq+1]
                del(self.resp_list[seq+1])
                return v
        return None

    def process_login(self, cmd_body, seq):
        username = unity.common.safe_get(cmd_body, 'username', None)
        password = unity.common.safe_get(cmd_body, 'password', None)

        if username is None or password is None:
            logger.error('create DeviceSession error  not handshake_cmd body param lost ')
            self.send_result(1, "密码错误或已过期",seq)
            return

        user = data_service.login(username, password, self.get_idt(), self.sock.getpeername()[0])
        if user is None:
            logger.error('User not exist. ')
            self.send_result(1, "密码错误或已过期", seq)
        else:
            # 查看是否重复登录
            if user["username"] in g_user_list:
                logger.info("the username has login, close first")
                from device import g_session_manager
                old_user = g_user_list[user["username"]]
                g_user_list[user["username"]] = user
                g_session_manager.sessions[old_user["serailNum"]].stop()
            else:
                g_user_list[user["username"]] = user
            # 如果重复登录  断开之前的链接  并且不设置为掉线
            self.user = user
            self.send_result(0, "success", seq)

    def process_heart_beat(self,cmd_data,seq):
        self.last_recv_time = int(time.time())
        logger.info('DeviceSession process_heart_beat data[%s]',cmd_data)
        self.send_result(0, "success", seq)
        return

    def process_get_config(self, cmd_data, seq):
        self.last_recv_time = int(time.time())
        logger.info('DeviceSession process_get_config data[%s]', cmd_data)

        config = data_service.find_config(self.user["id"])
        if config == -1:
            self.send_result(3, "No round.", seq)
            return
        elif config is None:
            self.send_result(4, "No config.", seq)
            return

        config["attributes"] = json.loads(config["attributes"])

        self.send_result(0, "success", seq, {"config": config})
        return

    def get_attr1(self, what):
        return getattr(self, what)

    def upload_config(self):
        response = self.send_request("upload_config")
        return response

    def update_config(self):
        config = data_service.find_config(self.user["id"])
        if config == -1:
            return "没有匹配的场次。"
        elif config is None:
            return "没有匹配的配置。"
        response = self.send_request("update_config", {"config": config})
        return response

    def upload_screenshots(self, accuracy="hign"):
        response = self.send_request("upload_screenshots", {"accuracy": accuracy})
        return response

    def upload_log(self, date_str=unity.common.get_now_datetime("%Y_%m_%d"), level="info"):
        response = self.send_request("upload_log", {"date_str": date_str, "level": level})
        return response








