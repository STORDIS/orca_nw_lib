import json
from typing import Dict, List

from prometheus_client import CollectorRegistry, Gauge, Counter, Info
from orca_nw_lib.gnmi_pb2 import SubscribeResponse
from orca_nw_lib.graph_db_models import Device
from orca_nw_lib.promdb_utils import write_to_prometheus
from .gnmi_util import get_logging
_logger = get_logging().getLogger(__name__)


registry = CollectorRegistry()


# Create a counter metric for Subscribed Interface counters
out_multicast_pkts = Counter('out_multicast_pkts', 'Sonic Interface ethernets counters: outgoing multicast packets', labelnames=["device_ip", "ether_name"], registry=registry)
in_bits_per_second = Counter('in_bits_per_second', 'Sonic Interface ethernets counters: incoming bits per second', labelnames=["device_ip", "ether_name"], registry=registry)
in_broadcast_pkts = Counter('in_broadcast_pkts', 'Sonic Interface ethernets counters: incoming broadcast packets', labelnames=["device_ip", "ether_name"], registry=registry)
in_errors = Counter('in_errors', 'Sonic Interface ethernets counters: incoming errors', labelnames=["device_ip", "ether_name"], registry=registry)
in_octets = Counter('in_octets', 'Sonic Interface ethernets counters: incoming octets', labelnames=["device_ip", "ether_name"], registry=registry)
in_unicast_pkts = Counter('in_unicast_pkts', 'Sonic Interface ethernets counters: incoming unicast packets', labelnames=["device_ip", "ether_name"], registry=registry)
out_bits_per_second = Counter('out_bits_per_second', 'Sonic Interface ethernets counters: outgoing bits per second', labelnames=["device_ip", "ether_name"], registry=registry)
out_discards = Counter('out_discards', 'Sonic Interface ethernets counters: outgoing discarded packets', labelnames=["device_ip", "ether_name"], registry=registry)
out_octets_per_second = Counter('out_octets_per_second', 'Sonic Interface ethernets counters: outgoing octets per second', labelnames=["device_ip", "ether_name"], registry=registry)
in_octets_per_second = Counter('in_octets_per_second', 'Sonic Interface ethernets counters: incoming octets per second', labelnames=["device_ip", "ether_name"], registry=registry)
in_pkts = Counter('in_pkts', 'Sonic Interface ethernets counters: recived packets',  labelnames=["device_ip", "ether_name"], registry=registry)
in_pkts_per_second = Counter('in_pkts_per_second', 'Sonic Interface ethernets counters: incoming packets per second', labelnames=["device_ip", "ether_name"], registry=registry)
out_errors = Counter('out_errors', 'Sonic Interface ethernets counters: outgoing errors', labelnames=["device_ip", "ether_name"], registry=registry)
out_pkts = Counter('out_pkts', 'Sonic Interface ethernets counters: outgoing packets', labelnames=["device_ip", "ether_name"], registry=registry)
out_pkts_per_second = Counter('out_pkts_per_second', 'Sonic Interface ethernets counters: outgoing packets per second', labelnames=["device_ip", "ether_name"], registry=registry)
out_utilization = Counter('out_utilization', 'Sonic Interface ethernets counters: outgoing utilization', labelnames=["device_ip", "ether_name"], registry=registry)
last_clear = Counter('last_clear', 'Sonic Interface ethernets counters: last clear time', labelnames=["device_ip", "ether_name"], registry=registry)
out_broadcast_pkts = Counter('out_broadcast_pkts', 'Sonic Interface ethernets counters: outgoing broadcast packets', labelnames=["device_ip", "ether_name"], registry=registry)
out_octets = Counter('out_octets', 'Sonic Interface ethernets counters: outgoing octets', labelnames=["device_ip", "ether_name"], registry=registry)
in_discards = Counter('in_discards', 'Sonic Interface ethernets counters: incoming discarded packets', labelnames=["device_ip", "ether_name"], registry=registry)
in_multicast_pkts = Counter('in_multicast_pkts', 'Sonic Interface ethernets counters: incoming multicast packets', labelnames=["device_ip", "ether_name"], registry=registry)
in_utilization = Counter('in_utilization', 'Sonic Interface ethernets counters: incoming utilization', labelnames=["device_ip", "ether_name"], registry=registry)
out_unicast_pkts = Counter('out_unicast_pkts', 'Sonic Interface ethernets counters: outgoing unicast packets', labelnames=["device_ip", "ether_name"], registry=registry)


# Create Info metric for discoverd interface data.
intfc_registry = CollectorRegistry()
interface_info = Info('interface_info', 'Discoverd Interface information',
                            labelnames=["device_ip", "ether_name"],
                            registry=intfc_registry)

def handle_interface_counters_promdb(device_ip: str, resp: SubscribeResponse):
    try:
        """
        Sends the subscription interface counters metrics received from a device to the prometheus pushgateway.

        Args:
            device_ip (str): The IP address of the device
            resp (SubscribeResponse): The subscription response containing metrics

        Returns: 
            None
        """
        ether = ""    
        for ele in resp.update.prefix.elem:
           if ele.name == "interface":
            ether = ele.key.get("name")
            break
        if not ether:
            _logger.debug("Ethernet interface not found in gNMI subscription response from %s", device_ip,)
            return

        # Push the interface counters to prometheus pushgateway
        for u in resp.update.update:
            for ele in u.path.elem:
                # assign values to variables [if key then var = value] key --> (ele.name), value --> int(u.val.uint_val)
                if ele.name == "out-multicast-pkts":
                    out_multicast_pkts.labels(device_ip=device_ip, ether_name=ether).inc(int(u.val.uint_val))
                if ele.name == "in-bits-per-second":
                    in_bits_per_second.labels(device_ip=device_ip, ether_name=ether).inc(int(u.val.uint_val))
                if ele.name == "in-broadcast-pkts":
                    in_broadcast_pkts.labels(device_ip=device_ip, ether_name=ether).inc(int(u.val.uint_val))
                if ele.name == "in-errors":
                    in_errors.labels(device_ip=device_ip, ether_name=ether).inc(int(u.val.uint_val))
                if ele.name == "in-octets":
                    in_octets.labels(device_ip=device_ip, ether_name=ether).inc(int(u.val.uint_val))
                if ele.name == "in-unicast-pkts":
                    in_unicast_pkts.labels(device_ip=device_ip, ether_name=ether).inc(int(u.val.uint_val))
                if ele.name == "out-bits-per-second":
                    out_bits_per_second.labels(device_ip=device_ip, ether_name=ether).inc(int(u.val.uint_val))
                if ele.name == "out-discards":
                    out_discards.labels(device_ip=device_ip, ether_name=ether).inc(int(u.val.uint_val))
                if ele.name == "out-octets-per-second":
                    out_octets_per_second.labels(device_ip=device_ip, ether_name=ether).inc(int(u.val.uint_val))
                if ele.name == "in-octets-per-second":
                    in_octets_per_second.labels(device_ip=device_ip, ether_name=ether).inc(int(u.val.uint_val))
                if ele.name == "in-pkts":
                    in_pkts.labels(device_ip=device_ip, ether_name=ether).inc(int(u.val.uint_val))
                if ele.name == "in-pkts-per-second":
                    in_pkts_per_second.labels(device_ip=device_ip, ether_name=ether).inc(int(u.val.uint_val))
                if ele.name == "out-errors":
                    out_errors.labels(device_ip=device_ip, ether_name=ether).inc(int(u.val.uint_val))
                if ele.name == "out-pkts":
                    out_pkts.labels(device_ip=device_ip, ether_name=ether).inc(int(u.val.uint_val))
                if ele.name == "out-pkts-per-second":
                    out_pkts_per_second.labels(device_ip=device_ip, ether_name=ether).inc(int(u.val.uint_val))
                if ele.name == "out-utilization":
                    out_utilization.labels(device_ip=device_ip, ether_name=ether).inc(int(u.val.uint_val))
                if ele.name == "last-clear":
                    last_clear.labels(device_ip=device_ip, ether_name=ether).inc(int(u.val.uint_val))
                if ele.name == "out-broadcast-pkts":
                    out_broadcast_pkts.labels(device_ip=device_ip, ether_name=ether).inc(int(u.val.uint_val))
                if ele.name == "out-octets":
                    out_octets.labels(device_ip=device_ip, ether_name=ether).inc(int(u.val.uint_val))
                if ele.name == "in-discards":
                    in_discards.labels(device_ip=device_ip, ether_name=ether).inc(int(u.val.uint_val))
                if ele.name == "in-multicast-pkts":
                    in_multicast_pkts.labels(device_ip=device_ip, ether_name=ether).inc(int(u.val.uint_val))
                if ele.name == "in-utilization":
                    in_utilization.labels(device_ip=device_ip, ether_name=ether).inc(int(u.val.uint_val))
                if ele.name == "out-unicast-pkts":
                    out_unicast_pkts.labels(device_ip=device_ip, ether_name=ether).inc(int(u.val.uint_val))

        write_to_prometheus(registry=registry)
    except Exception as e:
        _logger.error(f"Error insterting in prometheus: {e}")
 
 
# Function to insert discoverd interface info to prometheus
def insert_device_interface_in_prometheus(device: Device, interfaces: dict):
    """
    Retrieves discovered interface data and inserts into prometheus DB.
   
    Args:
        device (Device): Object of type Device.
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
            interface_info.labels(device_ip=device.mgt_ip, ether_name=intfc.name).info({
                "interface_name": intfc.name,
                "enabled": str(intfc.enabled),
                "mtu": str(intfc.mtu),
                "speed": intfc.speed if intfc.speed else "N/A",
                "fec": intfc.fec if intfc.fec else "N/A",
                "oper_status": intfc.oper_sts,
                "admin_status": intfc.admin_sts,
                "description": intfc.description if intfc.description else "N/A",
                "mac_address": intfc.mac_addr if intfc.mac_addr else "N/A",
                "alias": intfc.alias if intfc.alias else "N/A",
                "lanes": intfc.lanes,
                "valid_speeds": str(intfc.valid_speeds),
                "breakout_supported": str(intfc.breakout_supported),
                "breakout_mode": str(intfc.breakout_mode)
            })
        write_to_prometheus(registry=intfc_registry)
    except Exception as e:
        _logger.error(f"Error inserting in prometheus: {e}")