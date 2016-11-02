# coding: utf-8
import cmd_handler
import http_handler

__version__ = '0.0.1'
VERSION = tuple(map(int, __version__.split('.')))

cmd_handler.init()
g_session_manager = None

__all__ = [
    'cmd_handler',
    'http_handler',
    'protocol',
    'g_session_manager',
]


def create_session_manager(server_name):
    from unity.tcp import sessions
    from device_session import DeviceSession
    global g_session_manager
    g_session_manager = sessions.create_session_manager(server_name, DeviceSession)
    import data_service
    data_service.reset_online()
    return g_session_manager
