from threading import Thread
from typing import List
from datetime import datetime

from orca_nw_lib.gnmi_sub import get_running_thread_names, get_subscription_path_for_monitoring, gnmi_unsubscribe, subscribe_to_path, device_sync_responses
from orca_nw_lib.influxdb_utils import create_point, write_to_influx
from orca_nw_lib.utils import get_logging
from .gnmi_pb2 import (
    Encoding,
    SubscribeRequest,
    SubscribeResponse,
    Subscription,
    SubscriptionList,
)
from orca_nw_lib.gnmi_util import getGrpcStubs
from orca_nw_lib.interface_gnmi import get_interface_base_path

from typing import List
from .gnmi_pb2 import SubscribeResponse, Subscription
from .gnmi_util import get_logging

_logger = get_logging().getLogger(__name__)


def inster_intfc_counters_influxdb(device_ip: str, resp: SubscribeResponse):
    """
    Sends the subscription interface counters metrics received from a device to the InfluxDB.
    
    Args:
        device_ip (str): The IP address of the device
        resp (SubscribeResponse): The subscription response containing metrics

    Returns: 
        None
    """
    ether = ""
    point = create_point("interface_metrics")
    for ele in resp.update.prefix.elem:
       if ele.name == "interface":
           ether = ele.key.get("name")
           point.tag("interface", ether)
           break
    if not ether:
        _logger.debug("Ethernet interface not found in gNMI subscription response from %s",device_ip,)
        return
    
    # Print each update
    for u in resp.update.update:
        for ele in u.path.elem:
            key = ele.name
            value = float(u.val.uint_val)
            point.field(key, value)
    point.time(datetime.utcnow())
    write_to_influx(point=point)
    

# Modifed handle_update function to use the new influxdb function:
def handle_update_influxdb(device_ip: str, subscriptions: List[Subscription]):
    device_gnmi_stub = getGrpcStubs(device_ip)
    subscriptionlist = SubscriptionList(
            subscription=subscriptions,
            mode=SubscriptionList.Mode.Value("STREAM"),
            encoding=Encoding.Value("JSON_IETF"),
        )
    sub_req = SubscribeRequest(subscribe=subscriptionlist)
    for resp in device_gnmi_stub.Subscribe(subscribe_to_path(sub_req)):
        try:
            if not resp.sync_response:
                for ele in resp.update.prefix.elem:
                    if ele.name == get_interface_base_path().elem[0].name:
                        _logger.debug("gNMI subscription interface counters received from %s -> %s",device_ip, resp,)
                        thread = Thread(
                            target=inster_intfc_counters_influxdb,
                            args=(device_ip, resp),
                            # daemon=True,
                        )
                        thread.start()
            
            elif resp.sync_response:
                _logger.info("gNMI subscription sync response received from %s -> %s", device_ip, resp,)
                device_sync_responses[device_ip] = resp.sync_response
                _logger.debug("Subscription sync response status for devices %s",device_sync_responses,)
                   
            else:
                device_sync_responses[device_ip] = resp.sync_response
                
        except Exception as e:
            _logger.error(f"Error processing subscription response: {e}")







def gnmi_subscribe_interface_counters(device_ip: str, force_resubscribe: bool = False):
    """
    Subscribe to GNMI for the given device IP.

    Args:
        device_ip (str): The IP address of the device.
        force_resubscribe (bool, optional): Whether to force resubscription even if already subscribed. Defaults to False.

    Returns:
        bool: True if subscription is successful, False otherwise.
    """

    thread_name = f"subscription_thread_influxdb_{device_ip}"
    if force_resubscribe:
        _logger.info("The force subscription is true, first removing the existing subscription if any.")
        gnmi_unsubscribe(device_ip)

    if thread_name in get_running_thread_names() and not force_resubscribe:
        _logger.debug("Already subscribed for %s", device_ip)
        _logger.debug("Currently running threads %s", get_running_thread_names())
        return True
    else:
        ## add get_subscription_path_for_monitoring to subscritions
        subscriptions = get_subscription_path_for_monitoring(device_ip)
        if not subscriptions:
            _logger.warn(
                "No subscription paths created for %s, Check if device with its components and config is discovered in DB or rediscover device.",device_ip,)
            return False
        _logger.info("Subscribing for %s", device_ip)
        thread = Thread(
            name=thread_name,
            target=handle_update_influxdb,
            args=(device_ip, subscriptions),
            # daemon=True,
        )
        thread.start()
        _logger.debug("Currently running threads for InfluxDB %s", get_running_thread_names())
        if thread_name in get_running_thread_names():
            _logger.debug("Subscribed for %s gnmi notifications from thread %s.",device_ip,thread_name,)
            return True
        _logger.error("Failed to subscribe for %s gnmi notifications.", device_ip)
        return False
    

