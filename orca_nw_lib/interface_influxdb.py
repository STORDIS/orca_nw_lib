import datetime

from .gnmi_pb2 import SubscribeResponse
from orca_nw_lib.graph_db_models import Device
from orca_nw_lib.influxdb_utils import create_point, write_to_influx
from .gnmi_util import get_logging
from .gnmi_pb2 import SubscribeResponse
from orca_nw_lib.graph_db_models import Device


_logger = get_logging().getLogger(__name__)


def handle_interface_counters_influxdb(device_ip: str, resp: SubscribeResponse):
    """
    Sends the subscription interface counters metrics received from a device to the InfluxDB.
    
    Args:
        device_ip (str): The IP address of the device
        resp (SubscribeResponse): The subscription response containing metrics

    Returns: 
        None
    """
    ether = ""
    point = create_point("interface_counters")
    device_pnt = point.tag("device_ip", device_ip)
    for ele in resp.update.prefix.elem:
       if ele.name == "interface":
            ether = ele.key.get("name")
            ether_pnt = device_pnt.tag("ether_name", ether)
            break
    if not ether:
        _logger.debug("Ethernet interface not found in gNMI subscription response from %s",device_ip,)
        return
    
    # Insert each intfc cntrs update
    for u in resp.update.update:
        for ele in u.path.elem:
            key = ele.name
            value = float(u.val.uint_val)
            ether_pnt.field(key, value)
        point.field("device_ip", device_ip)
    point.time(datetime.datetime.now(datetime.timezone.utc))
    write_to_influx(point=point)
    _logger.debug("gNMI subscription interface counters received from %s ",device_ip)
    

# GET function that inserts the discoverd device interface into inflixdb
def insert_device_interfaces_in_influxdb(device: Device, interfaces: dict):
    """
    Retrieves discovered interface data and inserts into influx DB.
    
    Args:
        device_ip (Device): Object of type Device.
        interfaces (dict): Dictionary pf key value pairs.
    """

    if not device:
        _logger.error("Device object is required.")
        return
    
    if not interfaces:
        _logger.error("Interfaces dictionary is required.")
        return
    
    try:
        for intfc, sub_intfc in interfaces.items():
            point = create_point("discovered_interfaces") \
                .tag("device_ip", device.mgt_ip) \
                .tag("ether_name", intfc.name) \
                .field("interface_name", intfc.name) \
                .field("enabled", intfc.enabled) \
                .field("mtu", intfc.mtu) \
                .field("speed", intfc.speed) \
                .field("fec", intfc.fec) \
                .field("oper_status", intfc.oper_sts) \
                .field("admin_status", intfc.admin_sts) \
                .field("description", intfc.description) \
                .field("mac_address", intfc.mac_addr) \
                .field("alias", intfc.alias) \
                .field("lanes", intfc.lanes) \
                .field("breakout_supported", intfc.breakout_supported) \
                .field("valid_speeds", intfc.valid_speeds) \
                .field("breakout_mode", intfc.breakout_mode)
            

            write_to_influx(point=point)
    except Exception as e:
        _logger.error(f"Error instering in influxdb: {e}")