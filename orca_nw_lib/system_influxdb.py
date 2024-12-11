import datetime

from orca_nw_lib.influxdb_utils import create_point, write_to_influx
from .gnmi_pb2 import SubscribeResponse
from .gnmi_util import get_logging


_logger = get_logging().getLogger(__name__)


def handle_system_influxdb(device_ip: str, resp: SubscribeResponse):
    """
    Sends the subscription system metrics received from a device to the InfluxDB.
    
    Args:
        device_ip (str): The IP address of the device
        resp (SubscribeResponse): The subscription response containing metrics

    Returns: 
        None
    """

    sys_metric = ""
    sys_metric_event_id = ""
    point = create_point("system_info_sub")
    device_pnt = point.tag("device_ip", device_ip)
    for ele in resp.update.prefix.elem:
        if ele.name == "dns":
           sys_metric = "dns"
           sys_metric_pnt = device_pnt.tag("system_metric", sys_metric)
           break
        if ele.name == "memory":
           sys_metric = 'memory'
           sys_metric_pnt = device_pnt.tag("system_metric", sys_metric)
           break
        if ele.name == "event":
            sys_metric = 'event'
            sys_metric_pnt = device_pnt.tag("system_metric", sys_metric)
            event_id = ele.key.get('id')
            sys_metric_event_id = sys_metric_pnt.tag("id", event_id)
            break

    if not sys_metric:
        _logger.debug("System Info not found in gNMI subscription response from %s",device_ip,)
        return

    for u in resp.update.update:
        for ele in u.path.elem:

            # System dns
            if ele.name == "address" and sys_metric == 'dns': 
                sys_metric_pnt.field(ele.name, u.val.string_val)
            if ele.name == "address-type" and sys_metric == 'dns': 
                sys_metric_pnt.field(ele.name, u.val.string_val)
            
            # System memory
            if ele.name == "reserved" and sys_metric == 'memory': 
                sys_metric_pnt.field(ele.name, int(u.val.uint_val))
            if ele.name == "buff-cache" and sys_metric == 'memory':
                sys_metric_pnt.field(ele.name, int(u.val.uint_val))
            if ele.name == "physical" and sys_metric == 'memory':
                sys_metric_pnt.field(ele.name, int(u.val.uint_val))
            if ele.name == "reserved" and sys_metric == 'memory':
                sys_metric_pnt.field(ele.name, int(u.val.uint_val))
            if ele.name == "unused" and sys_metric == 'memory':
                sys_metric_pnt.field(ele.name, int(u.val.uint_val))

            # System event
            if ele.name == "id" and sys_metric == 'event': 
                sys_metric_event_id.field(ele.name, u.val.string_val)
            if ele.name == "resource" and sys_metric == 'event':
                sys_metric_event_id.field(ele.name, u.val.string_val)
            if ele.name == "severity" and sys_metric == 'event':
                sys_metric_event_id.field(ele.name, u.val.string_val)
            if ele.name == "text" and sys_metric == 'event':
                sys_metric_event_id.field(ele.name, u.val.string_val)
            if ele.name == "time-created" and sys_metric == 'event': 
                sys_metric_event_id.field(ele.name, u.val.uint_val)
            if ele.name == "type-id" and sys_metric == 'event':
                sys_metric_event_id.field(ele.name, u.val.string_val)

    point.time(datetime.datetime.now(datetime.timezone.utc))
    write_to_influx(point=point)
    _logger.debug("gNMI subscription system received from %s ",device_ip)
    


# GET function that inserts the system uptime into inflixdb
def insert_system_in_influxdb(device_ip: str, system_info: dict):
    """
    Retrieves system uptime and NTP data and inserts into influx DB.
    
    Args:
        device_ip (str): Device ip of the system.
        system_infra (dict): Dictionary pf key value pairs.
    """

    if not device_ip:
        _logger.error("Device ip is required.")
        return
    
    if not system_info:
        _logger.error("System dictionary is required.")
        return

    
    try:
        point = create_point("system_info") 
        device_ip_pnt = point.tag("device_ip", device_ip)
        device_ip_pnt.field("reboot_cause", system_info.get("reboot_cause"))
        device_ip_pnt.field("show_user_list", ",".join(system_info.get("show_user_list", []))) 
        # device_ip_pnt.field("days", system_info.get("uptime"))  # Returns "6 days, 12 hours, 37 minutes"
        device_ip_pnt.field("days", system_info.get("uptime").split(", ")[0].split(" ")[0])
        device_ip_pnt.field("hours", system_info.get("uptime").split(", ")[1].split(" ")[0])
        device_ip_pnt.field("minutes", system_info.get("uptime").split(", ")[2].split(" ")[0])
        device_ip_pnt.field("server_address", system_info.get('server_address'))
        device_ip_pnt.field("now", system_info.get('now'))
        device_ip_pnt.field("peer_delay", system_info.get('peer_delay'))
        device_ip_pnt.field("peer_jitter", system_info.get('peer_jitter'))
        device_ip_pnt.field("peer_offset", system_info.get('peer_offset'))
        device_ip_pnt.field("peer_type", system_info.get('peer_type'))
        device_ip_pnt.field("poll_interval", system_info.get('poll_interval'))
        device_ip_pnt.field("reach", system_info.get('reach'))
        device_ip_pnt.field("sel_mode", system_info.get('sel_mode'))
        device_ip_pnt.field("stratum", system_info.get('stratum'))
            
        write_to_influx(point=point)
        _logger.debug("system info inserted to influxdb %s ",device_ip)
    except Exception as e:
        _logger.error(f"Error instering in influxdb: {e}")