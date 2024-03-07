from threading import Thread
import threading
from typing import List
from orca_nw_lib.common import Speed
from orca_nw_lib.device_db import get_all_devices_ip_from_db
from orca_nw_lib.gnmi_pb2 import (
    Encoding,
    SubscribeRequest,
    SubscribeResponse,
    Subscription,
    SubscriptionList,
    SubscriptionMode,
)
from orca_nw_lib.gnmi_util import get_logging, getGrpcStubs

from orca_nw_lib.interface_db import (
    get_all_interfaces_name_of_device_from_db,
)
from orca_nw_lib.interface_db import set_interface_config_in_db

from orca_nw_lib.interface_gnmi import (
    get_interface_base_path,
    get_intfc_config_path,
    get_oc_ethernet_config_path,
)
from orca_nw_lib.portgroup_db import get_all_port_group_ids_from_db
from orca_nw_lib.portgroup_gnmi import _get_port_group_speed_path
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
    if not ether:
        _logger.debug(
            f"Ethernet interface not found in gNMI subscription response from {device_ip}"
        )
        return
    enable = None
    mtu = None
    speed = None
    description = None
    for u in resp.update.update:
        for ele in u.path.elem:
            if ele.name == "enabled" and ether:
                enable = u.val.bool_val
            if ele.name == "mtu" and ether:
                mtu = u.val.uint_val
            if ele.name == "port-speed":
                speed = Speed.get_enum_from_str(u.val.string_val)
            if ele.name == "description":
                description = u.val.string_val
    _logger.debug(
        "updating interface config in DB device_ip: %s ether: %s enable: %s mtu: %s speed: %s description: %s ",
        device_ip,
        ether,
        enable,
        mtu,
        speed,
        description,
    )
    set_interface_config_in_db(
        device_ip=device_ip,
        if_name=ether,
        enable=enable,
        mtu=mtu,
        speed=speed,
        description=description,
    )


def handle_update(device_ip: str, subscriptions: List[Subscription]):
    device_gnmi_stub = getGrpcStubs(device_ip)
    subscriptionlist = SubscriptionList(
        subscription=subscriptions,
        mode=SubscriptionList.Mode.Value("STREAM"),
        encoding=Encoding.Value("PROTO"),
        updates_only=True,
    )

    sub_req = SubscribeRequest(subscribe=subscriptionlist)
    for resp in device_gnmi_stub.Subscribe(subscribe_to_path(sub_req)):
        try:
            _logger.debug(
                "gNMI subscription notification received from %s -> %s", device_ip, resp
            )
            if not resp.sync_response:
                for ele in resp.update.prefix.elem:
                    if ele.name == get_interface_base_path().elem[0].name:
                        ## Its an interface config update
                        handle_interface_config_update(device_ip, resp)
                        break
        except Exception as e:
            _logger.error(e)


def is_device_subscribed(device_ip: str) -> bool:
    """
    Check if the device is already subscribed to GNMI notifications.

    Args:
        device_ip (str): The IP address of the device to check.

    Returns:
        bool: True if the device is already subscribed, False otherwise.
    """
    return gnmi_subscribe(device_ip)


def gnmi_subscribe(device_ip: str):
    """
    Subscribe to GNMI notifications for the given device.

    Args:
        device_ip (str): The IP address of the device to subscribe to.

    Returns:
        bool: True if the subscription was successful or already exists, False otherwise.
    """

    thread_name = f"subscription_thread_{device_ip}"

    if thread_name in [thread.name for thread in threading.enumerate()]:
        _logger.debug("Already subscribed for %s", device_ip)
    else:
        subscriptions = get_subscription_path(device_ip)
        if not subscriptions:
            _logger.warn(
                "No subscription paths created for %s, Check if device with its components and config is discovered in DB or rediscover device.",
                device_ip,
            )
            return False
        _logger.info("Subscribing for %s", device_ip)
        thread = Thread(
            name=thread_name, target=handle_update, args=(device_ip, subscriptions)
        )
        thread.start()

    _logger.debug("Currently running threads %s", threading.enumerate())
    if thread_name in [thread.name for thread in threading.enumerate()]:
        _logger.debug(
            "Subscribed for %s gnmi notifications from thread %s.",
            device_ip,
            thread_name,
        )
        return True
    _logger.error("Failed to subscribe for %s gnmi notifications.", device_ip)
    return False


def gnmi_subscribe_for_all_devices_in_db():
    """
    Subscribe to GNMI for all devices in the database.
    """
    for device_ip in get_all_devices_ip_from_db():
        gnmi_subscribe(device_ip)


def get_subscription_path(device_ip: str):
    """
    Get subscription path for the given device IP.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        list: A list of subscription paths.
    """
    subscriptions = []
    for eth in get_all_interfaces_name_of_device_from_db(device_ip) or []:
        subscriptions.append(
            Subscription(
                path=get_intfc_config_path(eth), mode=SubscriptionMode.TARGET_DEFINED
            )
        )
        subscriptions.append(
            Subscription(
                path=get_oc_ethernet_config_path(eth),
                mode=SubscriptionMode.TARGET_DEFINED,
            )
        )

    for pg_id in get_all_port_group_ids_from_db(device_ip) or []:
        subscriptions.append(
            Subscription(
                path=_get_port_group_speed_path(pg_id),
                mode=SubscriptionMode.TARGET_DEFINED,
            )
        )

    return subscriptions


def gnmi_unsubscribe(device_ip: str):
    thread_name = f"subscription_{device_ip}"
    for thread in threading.enumerate():
        if thread.name == thread_name:
            _logger.info(f"Removing subscription for {device_ip}")
            terminate_thread(thread)
            _logger.debug(f"Removed subscription thread {thread_name}.")
            break
    _logger.debug(f"Currently running threads {threading.enumerate()}")


def terminate_thread(thread):
    import ctypes

    exc = ctypes.py_object(SystemExit)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread.ident), exc)
    if res == 0:
        raise ValueError("nonexistent thread id")
    elif res > 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def subscription_check_decorator(config_func):
    """
    A decorator function that checks if a device is subscribed to GNMI update notifications before allowing configuration.
    Takes a configuration function as input and returns a wrapper function that performs the subscription check before executing the configuration function.
    """

    def wrapper(*args, **kwargs):
        if gnmi_subscribe(args[0]):
            result = config_func(*args, **kwargs)
            return result
        else:
            _logger.error(
                f"Device {args[0]} is not subscribed to GNMI update notifications. Configuration can't be done."
            )
            return None

    return wrapper
