# coding: utf-8
import json
import base64


def recv_n(sock, length):
    data = ''
    need = length
    need_all = length
    while need > 0:
        data_get = sock.recv(need)
        if len(data_get) is 0:
            print 'recv error'
            return None
        data += data_get
        if len(data) is need_all:
            break
        else:
            need = need_all - len(data)

    return data


def aes_enc_b64(data):
    return base64.b64encode(data)


def b64_aes_dec(data, aes_key):
    b64_data = base64.b64decode(data)

    return b64_data


def ensure_param(need_params, cmd_body):
    for key in need_params:
        if key not in cmd_body:
            return False, key
    return True, None

