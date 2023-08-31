from threading import Thread
import threading
from orca_nw_lib.common import Speed
from orca_nw_lib.device import getDeviceFromDB
from orca_nw_lib.gnmi_pb2 import (
    Encoding,
    Path,
    SubscribeRequest,
    SubscribeResponse,
    Subscription,
    SubscriptionList,
    SubscriptionMode,
)
from orca_nw_lib.gnmi_util import _logger, getGrpcStubs


from typing import List
from orca_nw_lib.interfaces import (
    get_intfc_config_path,
    get_intfc_speed_path,
    getAllInterfacesNameOfDeviceFromDB,
    set_interface_config_in_db,
)

from orca_nw_lib.interfaces import get_interface_base_path
from orca_nw_lib.mclag import (
    create_mclag_peerlink_relations_in_db,
    createMclagGraphObjects,
    delMCLAGGatewayMacOfDeviceInDB,
    delMCLAGOfDeviceFromDB,
    get_mclag_domain_path,
    get_mclag_gateway_mac_path,
    get_mclag_path,
    insert_device_mclag_in_db,
)
from orca_nw_lib.utils import get_logging

_logger = get_logging().getLogger(__name__)


def subscribe_to_path(request):
    yield request


def handle_interface_config_update(device_ip: str, resp: SubscribeResponse):
    ether = ""
    for ele in resp.update.prefix.elem:
        if ele.name == "interface":
            ether = ele.key.get("name")
            break

    for u in resp.update.update:
        for ele in u.path.elem:
            if ele.name == "enabled" and ether:
                # Send set only once after collecting all updates.
                set_interface_config_in_db(device_ip, ether, enable=u.val.bool_val)
            if ele.name == "mtu" and ether:
                set_interface_config_in_db(device_ip, ether, mtu=u.val.uint_val)
            if ele.name == "port-speed":
                set_interface_config_in_db(
                    device_ip, ether, speed=Speed[u.val.string_val]
                )


def handle_mclag_domain_update(device_ip, resp):
    if resp.update.update:
        _logger.debug(f"MCLAG domain update received on {device_ip} \n {resp}")
        # TODO: not the best way to rediscover mc lag  but robust,
        # May be selective update can be performed in DB, because info is avilable in update message.
        # Challenges would be to create peerlinks and member chnl and rel to device, in that case.

        # Also subscription is not possible to MCLAG mem path, discovering mclag again discovers member interfaces.

        insert_device_mclag_in_db(
            getDeviceFromDB(device_ip), createMclagGraphObjects(device_ip)
        )
        create_mclag_peerlink_relations_in_db()

    elif resp.update.delete:
        _logger.debug(f"MCLAG domain delete received on {device_ip} \n {resp}")
        domain_id = 0
        for p in resp.update.delete:
            for path_ele in p.elem:
                if path_ele.name == "mclag-domain":
                    domain_id = path_ele.key.get("domain-id")
                    if domain_id:
                        delMCLAGOfDeviceFromDB(device_ip, domain_id)
                elif path_ele.name == "mclag-gateway-mac":
                    delMCLAGGatewayMacOfDeviceInDB(device_ip)


def handle_update(device_ip: str, subscriptions: List[Subscription]):
    device_gnmi_stub = getGrpcStubs(device_ip)
    try:
        subscriptionlist = SubscriptionList(
            subscription=subscriptions,
            mode=SubscriptionList.Mode.Value("STREAM"),
            encoding=Encoding.Value("PROTO"),
            updates_only=True,
        )

        sub_req = SubscribeRequest(subscribe=subscriptionlist)
        for resp in device_gnmi_stub.Subscribe(subscribe_to_path(sub_req)):
            _logger.debug(
                f"gnmi subscription notification received on {device_ip} \n{resp}"
            )
            if not resp.sync_response:
                for ele in resp.update.prefix.elem:
                    if ele.name == get_interface_base_path().elem[0].name:
                        ## Its an interface config update
                        handle_interface_config_update(device_ip, resp)
                        break
                    if ele.name == get_mclag_path().elem[0].name:
                        handle_mclag_domain_update(device_ip, resp)
    except Exception as e:
        _logger.error(e.with_traceback())


def gnmi_subscribe(device_ip: str):
    subscriptions=[]
    
    for eth in getAllInterfacesNameOfDeviceFromDB(device_ip):
       subscriptions.append(Subscription(path=get_intfc_config_path(eth),mode=SubscriptionMode.ON_CHANGE))
        
    for eth in getAllInterfacesNameOfDeviceFromDB(device_ip):
       subscriptions.append(Subscription(path=get_intfc_speed_path(eth),mode=SubscriptionMode.ON_CHANGE))
       
    thread_name = f"subscription_{device_ip}"
    for thread in threading.enumerate():
        if thread.name == thread_name:
            _logger.warn(f"Already subscribed for {device_ip}")
            return False
        else:
            thread = Thread(
                name=thread_name, target=handle_update, args=(device_ip, subscriptions)
            )
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
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread.ident), exc)
    if res == 0:
        raise ValueError("nonexistent thread id")
    elif res > 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")
