from threading import Thread
import threading
from typing import List
from .common import PortFec, Speed
from .device_db import get_all_devices_ip_from_db
from .gnmi_pb2 import (
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
    get_interface_counters_path,
    get_intfc_config_path,
    get_oc_ethernet_config_path,
)
from orca_nw_lib.portgroup_db import (
    get_all_port_group_ids_from_db,
    set_port_group_speed_in_db,
)
from orca_nw_lib.portgroup_gnmi import (
    get_port_group_speed_path,
    _get_port_groups_base_path,
)

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
            "Ethernet interface not found in gNMI subscription response from %s",
            device_ip,
        )
        return
    enable = None
    mtu = None
    speed = None
    description = None
    fec = None
    for u in resp.update.update:
        for ele in u.path.elem:
            if ele.name == "enabled":
                enable = u.val.bool_val
            if ele.name == "mtu":
                mtu = u.val.uint_val
            if ele.name == "port-speed":
                speed = Speed.get_enum_from_str(u.val.string_val)
            if ele.name == "description":
                description = u.val.string_val
            if ele.name == "port-fec":
                fec = PortFec.get_enum_from_str(u.val.string_val)
    _logger.debug(
        "updating interface config in DB, device_ip: %s, ether: %s, enable: %s, mtu: %s, speed: %s, description: %s .",
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
        fec=fec,
    )


def handle_port_group_config_update(device_ip: str, resp: SubscribeResponse):
    pg_id = 0
    for ele in resp.update.prefix.elem:
        if ele.name == "port-group":
            pg_id = ele.key.get("id")
            break
    if not pg_id:
        _logger.debug(
            "Ethernet interface not found in gNMI subscription response from %s",
            device_ip,
        )
        return
    for u in resp.update.update:
        for ele in u.path.elem:
            if ele.name == "speed":
                speed_enum = Speed.get_enum_from_str(u.val.string_val)
                if speed_enum:
                    _logger.debug(
                        "updating port-group config in DB, device_ip: %s, pg_id: %s, speed: %s .",
                        device_ip,
                        pg_id,
                        speed_enum,
                    )
                    set_port_group_speed_in_db(
                        device_ip=device_ip, group_id=pg_id, speed=speed_enum
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
            if not resp.sync_response:
                for ele in resp.update.prefix.elem:
                    if ele.name == get_interface_base_path().elem[0].name:
                        _logger.debug(
                            "gNMI subscription interface config update received from %s -> %s",
                            device_ip,
                            resp,
                        )
                        thread = Thread(
                            target=handle_interface_config_update,
                            args=(device_ip, resp),
                            daemon=True,
                        )
                        thread.start()
                        # handle_interface_config_update(device_ip, resp)
                    if ele.name == _get_port_groups_base_path().elem[0].name:
                        ## Its a port group config update
                        _logger.debug(
                            "gNMI subscription port group config update received from %s -> %s",
                            device_ip,
                            resp,
                        )
                        handle_port_group_config_update(device_ip, resp)
            elif resp.sync_response:
                global device_sync_responses
                _logger.info(
                    "gNMI subscription sync response received from %s -> %s",
                    device_ip,
                    resp,
                )
                device_sync_responses[device_ip] = resp.sync_response
                _logger.debug(
                    "Subscription sync response status for devices %s",
                    device_sync_responses,
                )
            else:
                _logger.debug(
                    "gNMI subscription response received from %s -> %s",
                    device_ip,
                    resp,
                )

        except Exception as e:
            _logger.error(e)
            raise


def ready_to_receive_subs_resp(device_ip: str):
    ## Although sync response will only be received if the device is fully subscribed to gNMI updates,
    ## Still cheking with gnmi_subscribe function will subscribe if not already due to any reason.
    return sync_response_received(device_ip) and gnmi_subscribe(device_ip)


device_sync_responses = {}


def sync_response_received(device_ip: str):
    if not device_sync_responses.get(device_ip):
        _logger.error(
            "Sync response not received for device %s , Hence not ready to receive subscription responses!!",
            device_ip,
        )
        return False
    return True


def get_subscription_thread_name(device_ip: str):
    """
    Returns the name of the subscription thread for the given device IP.

    Parameters:
    device_ip (str): The IP address of the device.

    Returns:
    str: The name of the subscription thread.
    """
    return f"subscription_thread_{device_ip}"


def get_running_thread_names():
    running_threads = threading.enumerate()
    thread_names = [thread.name for thread in running_threads]
    return thread_names


def gnmi_subscribe(device_ip: str):
    """
    Subscribe to GNMI notifications for the given device.

    Args:
        device_ip (str): The IP address of the device to subscribe to.

    Returns:
        bool: True if the subscription was successful or already exists, False otherwise.
    """

    thread_name = get_subscription_thread_name(device_ip)

    if thread_name in get_running_thread_names():
        _logger.debug("Already subscribed for %s", device_ip)
        _logger.debug("Currently running threads %s", get_running_thread_names())
        return True
    else:
        subscriptions = get_subscription_path_for_config_change(device_ip)
        ## add get_subscription_path_for_config_change to subscritions
        # subscriptions += get_subscription_path_for_monitoring(device_ip)
        if not subscriptions:
            _logger.warn(
                "No subscription paths created for %s, Check if device with its components and config is discovered in DB or rediscover device.",
                device_ip,
            )
            return False
        _logger.info("Subscribing for %s", device_ip)
        thread = Thread(
            name=thread_name,
            target=handle_update,
            args=(device_ip, subscriptions),
            daemon=True,
        )
        thread.start()
        _logger.debug("Currently running threads %s", get_running_thread_names())
        if thread_name in get_running_thread_names():
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


def get_subscription_path_for_config_change(device_ip: str):
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
                path=get_port_group_speed_path(pg_id),
                mode=SubscriptionMode.TARGET_DEFINED,
            )
        )

    return subscriptions


def get_subscription_path_for_monitoring(device_ip: str):
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
                path=get_interface_counters_path(eth),
                mode=SubscriptionMode.TARGET_DEFINED,
            )
        )

    return subscriptions


def gnmi_unsubscribe_for_all_devices_in_db():
    """
    Unsubscribes all devices in the database from GNMI.
    """
    for device_ip in get_all_devices_ip_from_db():
        gnmi_unsubscribe(device_ip)


def gnmi_unsubscribe(device_ip: str):
    """
    Unsubscribes from the GNMI device with the specified IP address.

    Args:
        device_ip (str): The IP address of the GNMI device.

    Returns:
        None
    """
    thread_name = get_subscription_thread_name(device_ip)
    for thread in threading.enumerate():
        if thread.name == thread_name:
            _logger.info("Removing subscription for %s", device_ip)
            terminate_thread(thread)
            break
    if thread_name in get_running_thread_names():
        _logger.error("Failed to remove subscription for %s", device_ip)
    else:
        _logger.info("Removed subscription for %s", device_ip)
    _logger.debug("Currently running threads %s", get_running_thread_names())


def terminate_thread(thread):
    """
    Terminate a thread by raising a SystemExit exception in the thread.

    Args:
        thread: The thread to be terminated.

    Raises:
        ValueError: If the thread id does not exist.
        SystemError: If PyThreadState_SetAsyncExc failed.
    """
    import ctypes

    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_long(thread.ident), ctypes.py_object(SystemExit)
    )
    if res == 0:
        _logger.error("Failed to terminate thread %s", thread.name)
    elif res > 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def ready_to_receive_subscription_response(config_func):
    """
    A decorator function that checks if a device is ready to receive subscriptions responses before allowing configuration.
    Takes a configuration function as input and returns a wrapper function that performs the subscription check before executing the configuration function.
    """

    def wrapper(*args, **kwargs):
        if kwargs and (ip := kwargs.get("device_ip")):
            _logger.debug(
                "Before config checking if device %s is fully subscribed to GNMI update notifications.",
                kwargs.get("device_ip"),
            )
            if ready_to_receive_subs_resp(ip):
                result = config_func(*args, **kwargs)
                return result
            else:
                _logger.error(
                    "Device %s is not fully subscribed to GNMI update notifications. Configuration can't be done.",
                    ip,
                )
                raise Exception(
                    "Device is not ready to receive GNMI updates. Configuration can't be done."
                )
        else:
            _logger.error(
                "Device ip in args -> %s, kwargs -> %s could not be found.",
                args,
                kwargs,
            )
            return None

    return wrapper
