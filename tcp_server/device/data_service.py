# coding: utf-8
from unity.service import mysql_service
from unity import common
import json


def login(username, password, serailNum, ipAddress):
    mysqlService = mysql_service.MysqlExcuter()
    md5_password = common.md5(common.md5(common.md5(password)[:16]))
    nowstr = common.get_now_datetime()

    sql = "select id, phone, username from t_user where username = '%s' " \
          "and password = '%s' and expireTime > '%s' and status = 1" % (username, md5_password, nowstr)
    user = mysqlService.execute_query(sql, type=dict, single=True)
    # 修改其他信息
    if user is not None:
        nowstr = common.get_now_datetime()
        update_sql = "update t_user set online = 1, serailNum = '%s', latestLoginTime = '%s'," \
                     " latestLoginIp = '%s' where id = %d"
        update_sql = update_sql % (serailNum, nowstr, ipAddress, user["id"])
        mysqlService.execute_update(update_sql)

        # 插入登陆记录
        log_sql = "insert into t_user_login_record(userId, loginTime, loginIp, serailNum) values(%d, '%s', '%s', '%s')"
        log_sql = log_sql % (user["id"], nowstr, ipAddress, serailNum)
        mysqlService.execute_update(log_sql)
        mysqlService.commit()

        user["serailNum"] = serailNum
    return user


def reset_online():
    mysqlService = mysql_service.MysqlExcuter()
    update_sql = "update t_user set online = 0 where online = 1"
    mysqlService.execute_update(update_sql)
    mysqlService.commit()


def offline(user):
    mysqlService = mysql_service.MysqlExcuter()
    update_sql = "update t_user set online = 0 where id = %d"
    update_sql = update_sql % (user["id"])
    mysqlService.execute_update(update_sql)
    mysqlService.commit()


def find_config(userId):
    # 查询该事件段的场次
    mysqlService = mysql_service.MysqlExcuter()
    nowstr = common.get_now_datetime()

    sql = "select id from t_round where (startTime <= '%s' and endTime >= '%s' and status = 1) " \
          "or status = 2 order by status,updateTime desc limit 1" % (nowstr, nowstr)
    round = mysqlService.execute_query(sql, type=dict, single=True)
    if round is None:
        return -1
    roundId = round["id"]

    configSql = "select configName, attributes, id from t_config t where t.roundId = %d and (t.id = (select " \
                "configId from t_related_user_round_config where userId = %d and roundId = %d) or t.status = 2)" \
                " and status <> 0 order by t.status asc limit 1"
    configSql = configSql % (roundId, userId, roundId)

    config = mysqlService.execute_query(configSql, type=dict, single=True)

    # log
    sql = "insert into t_request_record(userId, referId, module, requestTime, requestBody, requestSource, result," \
          "responseTime, responseBody, responseSource)" \
          " values(%d, %d, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')"
    sql = sql % (userId, 0 if config is None or "id" not in config else config["id"], 'get_config',
                 common.get_now_datetime(), "", "client", "" if config is None else json.dumps(config, ensure_ascii=False),
                 common.get_now_datetime(), '', "tcp_server")
    r = mysqlService.execute_update(sql)

    mysqlService.commit()

    return config


def save_screenshots(screenshots):
    mysqlService = mysql_service.MysqlExcuter()
    nowstr = common.get_now_datetime()

    sql = "select id from t_round where (startTime <= '%s' and endTime >= '%s' and status=1) " \
          "or status = 2 order by status,updateTime desc limit 1" % (nowstr, nowstr)
    round = mysqlService.execute_query(sql, type=dict, single=True)
    if round is None:
        roundId = 0
    else:
        roundId = round["id"]

    sql = "insert into t_screenshots(userId, url, fileName, accuracy, uploadTime, updateTime, status, roundId)" \
          " values(%d, '%s', '%s', '%s', %d, %d, %d, %d)"
    userId = screenshots["userId"] if "userId" in screenshots else 0
    row = mysqlService.execute_update(sql % (userId, screenshots["url"], screenshots["fileName"],
                                             screenshots["accuracy"], common.current_timesecond(),
                                             common.current_timesecond(), 1, roundId))
    mysqlService.commit()
    return row


def save_log(log):
    mysqlService = mysql_service.MysqlExcuter()
    nowstr = common.get_now_datetime()

    sql = "select id from t_round where (startTime <= '%s' and endTime >= '%s' and status=1) " \
          "or status = 2 order by status,updateTime desc limit 1" % (nowstr, nowstr)
    round = mysqlService.execute_query(sql, type=dict, single=True)
    if round is None:
        roundId = 0
    else:
        roundId = round["id"]

    sql = "insert into t_client_log(userId, url, fileName, uploadTime, updateTime, status, roundId)" \
          " values(%d, '%s', '%s', %d, %d, %d, %d)"
    userId = log["userId"] if "userId" in log else 0
    r = mysqlService.execute_update(sql % (userId, log["url"], log["fileName"], common.current_timesecond(),
                                           common.current_timesecond(), 1, roundId))

    mysqlService.commit()
    return r