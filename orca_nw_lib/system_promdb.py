
from prometheus_client import CollectorRegistry, Gauge, Info

from orca_nw_lib.promdb_utils import write_to_prometheus
from .gnmi_pb2 import SubscribeResponse
from .gnmi_util import get_logging

_logger = get_logging().getLogger(__name__)

system_registry = CollectorRegistry()
system_info_sub = Info('system_info_sub', 'System info from subscription',
                       labelnames=["device_ip", "sys_metric"],
                        registry=system_registry)

system_info_events = Info('system_info_events', 'System Events info from subscription',
                        labelnames=["device_ip", "event_id"],
                        registry=system_registry)



def handle_system_promdb(device_ip: str, resp: SubscribeResponse):
    """
    Sends the subscription system metrics received from a device to the Prometheus.
    
    Args:
        device_ip (str): The IP address of the device
        resp (SubscribeResponse): The subscription response containing metrics

    Returns: 
        None
    """
    sys_dict = {}
    sys_event_dict = {"id": "", "resource": "", "severity": "", "text": "", "time_created": "", "type_id": ""}
    sys_metric = ""
    event_id = ""

    for ele in resp.update.prefix.elem:
        if ele.name == "dns":
           sys_metric = "dns"
           break
        if ele.name == "memory":
           sys_metric = 'memory'
           break
        if ele.name == "event":
            sys_metric = 'event'
            event_id = ele.key.get('id')
            break

    if not sys_metric:
        _logger.debug("System Info not found in gNMI subscription response from %s",device_ip,)
        return


    for u in resp.update.update:
        for ele in u.path.elem:

            # System dns
            if ele.name == "address" and sys_metric == 'dns':
                sys_dict["address"] = u.val.string_val
            if ele.name == "address-type" and sys_metric == 'dns':
                sys_dict["address_type"] = u.val.string_val
            
            # System memory
            if ele.name == "buff-cache" and sys_metric == 'memory':
                sys_dict["buff_cache"] = str(u.val.uint_val)
            if ele.name == "physical" and sys_metric == 'memory':
                sys_dict["physical"]= str(u.val.uint_val)
            if ele.name == "reserved" and sys_metric == 'memory':
                sys_dict["reserved"]= str(u.val.uint_val) 
            if ele.name == "unused" and sys_metric == 'memory':
                sys_dict["unused"]= str(u.val.uint_val)

            # System event
            if ele.name == "id" and sys_metric == 'event':
                sys_event_dict["id"] = u.val.string_val
            if ele.name == "resource" and sys_metric == 'event':
                sys_event_dict["resource"] = u.val.string_val
            if ele.name == "severity" and sys_metric == 'event':
                sys_event_dict["severity"] = u.val.string_val
            if ele.name == "text" and sys_metric == 'event':
                sys_event_dict["text"]= u.val.string_val
            if ele.name == "time-created" and sys_metric == 'event': 
                sys_event_dict["time_created"]= str(u.val.uint_val)
            if ele.name == "type-id" and sys_metric == 'event':
                sys_event_dict["type_id"]= u.val.string_val


    if sys_metric == "dns" or sys_metric == "memory":
        system_info_sub.labels(device_ip=device_ip,sys_metric=sys_metric).info(sys_dict)
    elif sys_metric == "event":
        system_info_events.labels(device_ip=device_ip, event_id=event_id).info(sys_event_dict)
    write_to_prometheus(registry=system_registry)
    _logger.debug("gNMI subscription system received from %s ",device_ip)
    




system_info = Info('system_info_get', 'System info from GET', labelnames=["device_ip", "sys_metric"], registry=system_registry)
peer_delay = Gauge('system_info_get_peer_delay', 'System peer dealy', labelnames=["device_ip", "sys_metric"], registry=system_registry)
peer_jitter = Gauge('system_info_get_peer_jitter', 'System peer jitter', labelnames=["device_ip", "sys_metric"], registry=system_registry)
peer_offset = Gauge('system_info_get_peer_offset', 'System peer offset', labelnames=["device_ip", "sys_metric"], registry=system_registry)

# GET function that inserts the system uptime and NTP into inflixdb
def insert_system_in_prometheus(device_ip: str, system_data: dict):
    """
    Retrieves system uptime data and NTP inserts into prometheus pushgateway.
    
    Args:
        device_ip (Device): Object of type Device.
        system_infra (dict): Dictionary pf key value pairs.
    """
    if not device_ip:
        _logger.error("Device ip is required.")
        return
    
    if not system_data:
        _logger.error("System dictionary is required.")
        return

    try:
        system_info.labels(device_ip=device_ip, sys_metric="ntp").info({
                "reboot_cause": system_data.get("reboot_cause"),
                "show_user_list": ",".join(system_data.get("show_user_list", [])),
                # ("uptime", system_data.get("uptime"), # Returns "6 days, 12 hours, 37 minutes"
                "days": str(system_data.get("uptime").split(", ")[0].split(" ")[0]),
                "hours": str(system_data.get("uptime").split(", ")[1].split(" ")[0]),
                "minutes": str(system_data.get("uptime").split(", ")[2].split(" ")[0]),
                "server_address": system_data.get('server_address'),
                "now": str(system_data.get('now')),
                # "peer_delay": system_data.get('peer_delay'),
                # "peer_jitter": system_data.get('peer_jitter'),
                # "peer_offset": system_data.get('peer_offset'),
                "peer_type": system_data.get('peer_type'),
                "poll_interval": str(system_data.get('poll_interval')),
                "reach": str(system_data.get('reach')),
                "sel_mode": system_data.get('sel_mode') if system_data.get('sel_mode') else "N/A",
                "stratum": str(system_data.get('stratum')),
            })
        peer_delay.labels(device_ip=device_ip, sys_metric="ntp").set(float(system_data.get('peer_delay')))
        peer_jitter.labels(device_ip=device_ip, sys_metric="ntp").set(float(system_data.get('peer_jitter')))
        peer_offset.labels(device_ip=device_ip, sys_metric="ntp").set(float(system_data.get('peer_offset')))
            
        write_to_prometheus(registry=system_registry)
        _logger.debug("System Info pushed to prometheus %s ",device_ip)
    except Exception as e:
        _logger.error(f"Error instering in influxdb: {e}")