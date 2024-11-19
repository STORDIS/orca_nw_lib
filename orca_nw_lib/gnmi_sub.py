import time
from threading import Thread
import threading
from typing import List
from .common import PortFec, Speed
from .device_db import get_all_devices_ip_from_db, update_device_status
from .device_gnmi import get_device_state_url
from .gnmi_pb2 import (
    Encoding,
    SubscribeRequest,
    SubscribeResponse,
    Subscription,
    SubscriptionList,
    SubscriptionMode,
)
from orca_nw_lib.gnmi_util import get_logging, send_gnmi_subscribe, getGrpcStubs

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
from .stp_db import set_stp_config_in_db
from .stp_port_db import set_stp_port_config_in_db, delete_stp_port_member_from_db
from .stp_port_gnmi import get_stp_port_path

_logger = get_logging().getLogger(__name__)

gnmi_subscriptions = {}


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
    autoneg = None
    adv_speeds = None
    link_training = None
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
            if ele.name == "auto-negotiate":
                autoneg = u.val.bool_val
            if ele.name == "advertised-speed":
                adv_speeds = u.val.string_val
            if ele.name == "standalone-link-training":
                link_training = u.val.bool_val
    _logger.debug(
        "updating interface config in DB, device_ip: %s, ether: %s, enable: %s, mtu: %s, speed: %s, description: %s, autoneg: %s, adv_speeds : %s, link_training: %s .",
        device_ip,
        ether,
        enable,
        mtu,
        speed,
        description,
        autoneg,
        adv_speeds,
        link_training,
    )
    set_interface_config_in_db(
        device_ip=device_ip,
        if_name=ether,
        enable=enable,
        mtu=mtu,
        speed=speed,
        description=description,
        fec=fec,
        autoneg=autoneg,
        adv_speeds=adv_speeds,
        link_training=link_training,
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


def handle_stp_config(device_ip: str, resp: SubscribeResponse):
    enabled_protocol = None
    bpdu_filter = None
    loop_guard = None
    disabled_vlans = None
    rootguard_timeout = (None,)
    portfast = (None,)
    hello_time = (None,)
    max_age = (None,)
    forwarding_delay = (None,)
    bridge_priority = None
    for u in resp.update.update:
        for ele in u.path.elem:
            if ele.name == "enabled-protocol":
                enabled_protocol = u.val.string_val
            if ele.name == "bpdu-filter":
                bpdu_filter = u.val.bool_val
            if ele.name == "loop-guard":
                loop_guard = u.val.bool_val
            if ele.name == "disabled-vlans":
                disabled_vlans = u.val.string_val
            if ele.name == "rootguard-timeout":
                rootguard_timeout = u.val.uint_val
            if ele.name == "portfast":
                portfast = u.val.bool_val
            if ele.name == "hello-time":
                hello_time = u.val.uint_val
            if ele.name == "max-age":
                max_age = u.val.uint_val
            if ele.name == "forwarding-delay":
                forwarding_delay = u.val.uint_val
            if ele.name == "bridge-priority":
                bridge_priority = u.val.uint_val
    _logger.debug(
        "Updating STP config on DB for device: %s, enabled_protocol: %s, bpdu_filter: %s, loop_guard: %s, disabled_vlans: %s, rootguard_timeout: %s, portfast: %s, hello_time: %s, max_age: %s, forwarding_delay: %s, bridge_priority: %s",
        device_ip,
        enabled_protocol,
        bpdu_filter,
        loop_guard,
        disabled_vlans,
        rootguard_timeout,
        portfast,
        hello_time,
        max_age,
        forwarding_delay,
        bridge_priority,
    )
    set_stp_config_in_db(
        device_ip=device_ip,
        enabled_protocol=enabled_protocol,
        bpdu_filter=bpdu_filter,
        loop_guard=loop_guard,
        disabled_vlans=disabled_vlans,
        rootguard_timeout=rootguard_timeout,
        portfast=portfast,
        hello_time=hello_time,
        max_age=max_age,
        forwarding_delay=forwarding_delay,
        bridge_priority=bridge_priority,
    )


def handle_stp_port_config(device_ip: str, resp: SubscribeResponse):
    bpdu_guard = None
    bpdu_filter = None
    bpdu_guard_port_shutdown = None
    link_type = None
    guard = None
    edge_port = None
    if_name = None
    portfast = None
    stp_enabled = None
    uplink_fast = None
    cost = None
    port_priority = None
    for del_item in resp.update.delete:
        for ele in del_item.elem:
            if ele.name == "interface":
                if_name = ele.key.get("name")
                return delete_stp_port_member_from_db(
                    device_ip=device_ip, if_name=if_name
                )

    for u in resp.update.update:
        for ele in u.path.elem:
            if ele.name == "bpdu-guard":
                bpdu_guard = u.val.bool_val
            if ele.name == "bpdu-filter":
                bpdu_filter = u.val.bool_val
            if ele.name == "bpdu-guard-port-shutdown":
                bpdu_guard_port_shutdown = u.val.bool_val
            if ele.name == "link-type":
                link_type = u.val.string_val
            if ele.name == "guard":
                guard = u.val.string_val
            if ele.name == "edge-port":
                edge_port = u.val.string_val
            if ele.name == "name":
                if_name = u.val.string_val
            if ele.name == "portfast":
                portfast = u.val.bool_val
            if ele.name == "spanning-tree-enable":
                stp_enabled = u.val.bool_val
            if ele.name == "uplink-fast":
                uplink_fast = u.val.bool_val
            if ele.name == "cost":
                cost = u.val.uint_val
            if ele.name == "port-priority":
                port_priority = u.val.uint_val
    _logger.debug(
        f"Updating stp port {if_name} on db for {device_ip} with config bpdu_guard: {bpdu_guard}, bpdu_filter: {bpdu_filter}, bpdu_guard_port_shutdown: {bpdu_guard_port_shutdown}, link_type: {link_type}, guard: {guard}, edge_port: {edge_port}, portfast: {portfast}, stp_enabled: {stp_enabled}, uplink_fast: {uplink_fast}, cost: {cost}, port_priority: {bpdu_guard}."
    )
    return set_stp_port_config_in_db(
        device_ip=device_ip,
        if_name=if_name,
        bpdu_guard=bpdu_guard,
        bpdu_filter=bpdu_filter,
        bpdu_guard_port_shutdown=bpdu_guard_port_shutdown,
        link_type=link_type,
        guard=guard,
        edge_port=edge_port,
        portfast=portfast,
        stp_enabled=stp_enabled,
        uplink_fast=uplink_fast,
        cost=cost,
        port_priority=port_priority,
    )


def handle_device_state(device_ip: str, resp: SubscribeResponse):
    for u in resp.update.update:
        resource = None
        status = None
        for ele in u.path.elem:
            if ele.name == "resource":
                resource = u.val.string_val
            if ele.name == "text":
                status = u.val.string_val
        if resource == "system_status":
            update_device_status(device_ip, status)


def handle_update(device_ip: str, subscriptions: List[Subscription]):
    # device_gnmi_stub = getGrpcStubs(device_ip)
    subscriptionlist = SubscriptionList(
        subscription=subscriptions,
        mode=SubscriptionList.Mode.Value("STREAM"),
        encoding=Encoding.Value("PROTO"),
        updates_only=True,
    )

    sub_req = SubscribeRequest(subscribe=subscriptionlist)
    subscription = send_gnmi_subscribe(
        device_ip=device_ip, subscribe_request=subscribe_to_path(sub_req)
    )
    global gnmi_subscriptions
    gnmi_subscriptions[device_ip] = subscription
    for resp in subscription:
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
                    # if ele.name == get_stp_global_config_path().elem[0].name:
                    #     _logger.debug(
                    #         "gNMI subscription stp config update received from %s -> %s",
                    #         device_ip,
                    #         resp,
                    #     )
                    #     handle_stp_config(device_ip, resp)
                    if ele.name == get_stp_port_path().elem[0].name:
                        _logger.debug(
                            "gNMI subscription stp config update received from %s -> %s",
                            device_ip,
                            resp,
                        )
                        handle_stp_port_config(device_ip, resp)
                    if ele.name == get_device_state_url().elem[0].name:
                        _logger.debug(
                            "gNMI subscription device state update received from %s -> %s",
                            device_ip,
                            resp,
                        )
                        handle_device_state(device_ip, resp)
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


"""
dictionary to store the sync response received from the device.
    Key: device_ip
    Value: sync_response received status (True/False)
"""
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


def gnmi_subscribe(device_ip: str, force_resubscribe: bool = False):
    """
    Subscribe to GNMI for the given device IP.

    Args:
        device_ip (str): The IP address of the device.
        force_resubscribe (bool, optional): Whether to force resubscription even if already subscribed. Defaults to False.

    Returns:
        bool: True if subscription is successful, False otherwise.
    """

    thread_name = get_subscription_thread_name(device_ip)
    if force_resubscribe:
        _logger.info(
            "The force subscription is true, first removing the existing subscription if any."
        )
        gnmi_unsubscribe(device_ip)

    if thread_name in get_running_thread_names() and not force_resubscribe:
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

    # ON_CHANGE subscription mode is not supported for stp global config,  only SAMPLE subscription mode is supported.
    # re discovery of stp global config is being done for every config change on stp global config via ORCA.

    # subscriptions.append(
    #     Subscription(
    #         path=get_stp_global_config_path(),
    #         mode=SubscriptionMode.ON_CHANGE,
    #     )
    # )

    subscriptions.append(
        Subscription(path=get_stp_port_path(), mode=SubscriptionMode.ON_CHANGE)
    )

    subscriptions.append(
        Subscription(
            path=get_device_state_url(),
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


def gnmi_unsubscribe(device_ip: str, retries: int = 5, timeout: int = 1) -> None:
    """
    Unsubscribes from the GNMI device with the specified IP address.

    Args:
        device_ip (str): The IP address of the GNMI device.
        retries (int, optional): The number of retries. Defaults to 5.
        timeout (int, optional): The timeout between retries. Defaults to 1.

    Returns:
        None
    """
    sync_response = device_sync_responses.pop(device_ip, None)
    if sync_response is not None:
        _logger.debug(
            f"Removed device {device_ip} with sync_response {sync_response} from device_sync_responses dictionary."
        )
    else:
        _logger.debug(
            f"Device {device_ip} not found in device_sync_responses dictionary."
        )

    global gnmi_subscriptions
    subscription = gnmi_subscriptions.get(device_ip)
    if subscription:
        try:
            _logger.info("Removing subscription for %s", device_ip)
            subscription.cancel()
        except Exception as e:
            _logger.debug("Failed to remove subscription for %s: %s", device_ip, e)
            raise

    thread_name = get_subscription_thread_name(device_ip)
    while retries > 0:
        _logger.info("Checking if subscription removed for %s", device_ip)
        if thread_name in get_running_thread_names():
            _logger.error("Subscription not removed for %s", device_ip)
        else:
            _logger.info("Removed subscription for %s", device_ip)
            break
        time.sleep(timeout)
        retries -= 1
    _logger.debug("Currently running threads %s", get_running_thread_names())


def close_gnmi_channel(device_ip: str, retries: int = 5, timeout: int = 1) -> None:
    """
    Closes the GNMI channel for the given device IP.

    Args:
        device_ip (str): The IP address of the device.
        retries (int, optional): The number of retries. Defaults to 5.
        timeout (int, optional): The timeout in seconds. Defaults to 1.

    Returns:
        None
    """
    # currently this function is not used.
    # we are keeping it for future use. i.e., when remove device from db, we need to close the channel.

    # close gnmi channel
    device_gnmi_stub = getGrpcStubs(device_ip)
    try:
        device_gnmi_stub.channel.close()
        _logger.info("Closed channel for %s", device_ip)
    except Exception as e:
        _logger.debug("Failed to close channel for %s: %s", device_ip, e)
        raise

    # remove gnmi stub from global stubs
    from orca_nw_lib.gnmi_util import remove_stub
    remove_stub(device_ip)

    thread_name = get_subscription_thread_name(device_ip)
    while retries > 0:
        _logger.info("checking if channel closed for %s", device_ip)
        if thread_name in get_running_thread_names():
            _logger.error("Failed to close channel thread for %s", device_ip)
        else:
            _logger.info("Closed channel thread for %s", device_ip)
            break
        time.sleep(timeout)
        retries -= 1
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


def check_gnmi_subscription_and_apply_config(config_func):
    """
    Decorator to check if the device is fully subscribed to GNMI updates before executing the decorated function.

    Args:
        config_func: The function to be decorated.

    Returns:
        The decorated function.

    Raises:
        Exception: If the device is not fully subscribed to GNMI updates.
    """

    def wrapper(*args, **kwargs):
        if kwargs and (ip := kwargs.get("device_ip")):
            _logger.debug(
                "Before config checking if device %s is fully subscribed to GNMI update notifications.",
                kwargs.get("device_ip"),
            )
            if gnmi_subscribe(ip) and sync_response_received(
                    ip
            ):  ## Check if the snyc response has been received for the given device also attempt to subscribe to gNMI,
                # gNMI subscription will occur in case not already Subscribed.
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
