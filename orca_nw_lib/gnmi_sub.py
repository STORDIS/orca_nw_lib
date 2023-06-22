from threading import Thread
import threading
from orca_nw_lib.gnmi_pb2 import (
    Encoding,
    Path,
    PathElem,
    SubscribeRequest,
    SubscribeResponse,
    Subscription,
    SubscriptionList,
    SubscriptionMode,
    Update,
)
from orca_nw_lib.gnmi_util import _logger, getGrpcStubs


from typing import List
from orca_nw_lib.graph_db_utils import set_interface_enable

from orca_nw_lib.interfaces import get_interface_base_path
from orca_nw_lib.utils import get_logging

_logger = get_logging().getLogger(__name__)


def subscribe_to_path(request):
    yield request


def handle_interface_config_update(device_ip:str,resp:SubscribeResponse):
    ether=''
    for ele in resp.update.prefix.elem:
        if ele.name == "interface":
            ether=ele.key.get('name')
    
    
    
    for u in resp.update.update:
        for ele in u.path.elem:
            if ele.name == "enabled" and ether:
                set_interface_enable(device_ip, ether, enable=u.val.bool_val)
            if ele.name == "mtu":
                set_interface_enable(device_ip, ether, mtu=u.val.uint_val)


def handle_update(device_ip: str, paths: List[Path]):
    device_gnmi_stub = getGrpcStubs(device_ip)
    try:
        subscriptionlist = SubscriptionList(
            subscription=[
                Subscription(
                    path=path,
                    mode=SubscriptionMode.ON_CHANGE,
                )
                for path in paths
            ],
            mode=SubscriptionList.Mode.Value("STREAM"),
            encoding=Encoding.Value("PROTO"),
            updates_only=True,
        )

        sub_req = SubscribeRequest(subscribe=subscriptionlist)
        for resp in device_gnmi_stub.Subscribe(subscribe_to_path(sub_req)):
            for ele in resp.update.prefix.elem:
                if ele.name == get_interface_base_path().elem[0].name:
                    ## Its an interface config update
                    handle_interface_config_update(device_ip,resp)
                    break
    except Exception as e:
        _logger.error(e)


def gnmi_subscribe(device_ip: str, paths: List[Path]):
    thread_name = f"subscription_{device_ip}"
    for thread in threading.enumerate():
        if thread.name == thread_name:
            _logger.warn(
                f"Already subscribed for {device_ip}"
            )
            return False
        else : 
            thread = Thread(
            name=thread_name, target=handle_update, args=(device_ip, paths))
            thread.start()
            return True


def gnmi_unsubscribe(device_ip: str):
    thread_name = f"subscription_{device_ip}"
    for thread in threading.enumerate():
        if thread.name == thread_name:
            _logger.warn(f"Removing subscription for {device_ip}")
            terminate_thread(thread)
            break


import ctypes

def terminate_thread(thread):
    exc = ctypes.py_object(SystemExit)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_long(thread.ident), exc)
    if res == 0:
        raise ValueError("nonexistent thread id")
    elif res > 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")