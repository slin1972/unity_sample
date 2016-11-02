# coding: utf-8

import device
import unity


def handle(params):
    """
        params contains
            imei
            command
            content
            createTime
            taskId
    """
    internal_traffic_params = unity.common.get_url_param(params)
    serail_num = internal_traffic_params.get("serail_num")
    func = internal_traffic_params.get("func")
    params = internal_traffic_params.get("params")

    if params is None:
        params = []
    else:
        params = params.split(",")

    return device.g_session_manager.handle_cmd(serail_num, func, params)
