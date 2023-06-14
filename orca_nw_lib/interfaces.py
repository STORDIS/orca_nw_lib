from enum import Enum, auto
import json
import logging
from typing import List

from .gnmi_pb2 import Path, PathElem
from .gnmi_util import create_req_for_update, send_gnmi_set, create_gnmi_update, send_gnmi_get
from .graph_db_models import Interface, PortChannel, SubInterface
from .graph_db_utils import getAllInterfacesOfDevice,getInterfacesOfDevice

_logger = logging.getLogger(__name__)


def createInterfaceGraphObjects(device_ip: str) -> List[Interface]:
    interfaces_json = get_all_interfaces(device_ip)
    intfc_graph_obj_list = {}
    for intfc in interfaces_json.get("openconfig-interfaces:interface"):
        intfc_state = intfc.get("state",{})
        intfc_counters = intfc_state.get("counters",{})
        type = intfc.get("config").get("type")

        if "ether" or "loopback" in type.lower():
            interface = Interface(
                name=intfc_state.get("name"),
                enabled=intfc_state.get("enabled"),
                mtu=intfc_state.get("mtu"),
                fec=intfc.get("openconfig-if-ethernet:ethernet",{})
                .get("config",{})
                .get("openconfig-if-ethernet-ext2:port-fec"),
                speed=intfc.get("openconfig-if-ethernet:ethernet",{})
                .get("config",{})
                .get("port-speed"),
                oper_sts=intfc_state.get("oper-status"),
                admin_sts=intfc_state.get("admin-status"),
                description=intfc_state.get("description"),
                last_chng=intfc_state.get("last-change"),
                mac_addr=intfc_state.get("mac-address"),
                in_bits_per_second=intfc_counters.get("in-bits-per-second"),
                in_broadcast_pkts=intfc_counters.get("in-broadcast-pkts"),
                in_discards=intfc_counters.get("in-discards"),
                in_errors=intfc_counters.get("in-errors"),
                in_multicast_pkts=intfc_counters.get("in-multicast-pkts"),
                in_octets=intfc_counters.get("in-octets"),
                in_octets_per_second=intfc_counters.get("in-octets-per-second"),
                in_pkts=intfc_counters.get("in-pkts"),
                in_pkts_per_second=intfc_counters.get("in-pkts-per-second"),
                in_unicast_pkts=intfc_counters.get("in-unicast-pkts"),
                in_utilization=intfc_counters.get("in-utilization"),
                last_clear=intfc_counters.get("last-clear"),
                out_bits_per_second=intfc_counters.get("out-bits-per-second"),
                out_broadcast_pkts=intfc_counters.get("out-broadcast-pkts"),
                out_discards=intfc_counters.get("out-discards"),
                out_errors=intfc_counters.get("out-errors"),
                out_multicast_pkts=intfc_counters.get("out-multicast-pkts"),
                out_octets=intfc_counters.get("out-octets"),
                out_octets_per_second=intfc_counters.get("out-octets-per-second"),
                out_pkts=intfc_counters.get("out-pkts"),
                out_pkts_per_second=intfc_counters.get("out-pkts-per-second"),
                out_unicast_pkts=intfc_counters.get("out-unicast-pkts"),
                out_utilization=intfc_counters.get("out-utilization"),
            )
            sub_intf_obj_list = []
            for sub_intfc in intfc.get("subinterfaces", {}).get("subinterface",{}):
                sub_intf_obj = SubInterface()
                sub_interface_ip_addresses = []
                for addr in (
                    sub_intfc.get("openconfig-if-ip:ipv4", {})
                    .get("addresses", {})
                    .get("address")
                    or []
                ):
                    if addr.get("ip"):
                        sub_interface_ip_addresses.append(addr.get("ip"))
                if sub_interface_ip_addresses:
                    sub_intf_obj.ip_addresses = sub_interface_ip_addresses
                    sub_intf_obj_list.append(sub_intf_obj)

                # sub_intf_obj.ip_addresses=sub_interface_ip_addresses if sub_intf_obj_list else []

            intfc_graph_obj_list[interface] = (
                sub_intf_obj_list if sub_interface_ip_addresses else []
            )
        elif "lag" in type.lower():
            # its a port channel
            pass
        else:
            _logger.error(f"Unknown Interface type {type}")

    return intfc_graph_obj_list


def getInterfacesDetailsFromGraph(device_ip: str, intfc_name=None):
    op_dict = []
    
    if intfc_name :
        intfc=getInterfacesOfDevice(device_ip, intfc_name)
        if intfc:
            op_dict.append(intfc.__properties__)
    else:
        interfaces = getAllInterfacesOfDevice(device_ip)
        for intfc in interfaces or []:
            op_dict.append(intfc.__properties__)
    return op_dict


class Speed(Enum):
    SPEED_1GB = auto()
    SPEED_5GB = auto()
    SPEED_10GB = auto()
    SPEED_25GB = auto()
    SPEED_40GB = auto()
    SPEED_50GB = auto()
    SPEED_100GB = auto()
    def __str__(self):
        return f'openconfig-if-ethernet:{self.name}'

def get_possible_speeds():
    return [str(e) for e in Speed]

def config_interface(device_ip: str, interface_name: str, enable:bool=None,mtu:int=None,loopback:bool=None,description:str=None
                     ,speed:Speed=None):
    updates=[]
    
    if enable is not None:
        updates.append(create_gnmi_update(
         Path(
            target="openconfig",
            origin="openconfig-interfaces",
            elem=[
                PathElem(
                    name="interfaces",
                ),
                PathElem(name="interface", key={"name": interface_name}),
                PathElem(name="config"),
                PathElem(name="enabled"),
            ],
        ),{"openconfig-interfaces:enabled": enable}))
        
    if mtu is not None:
        updates.append(create_gnmi_update(
         Path(
            target="openconfig",
            origin="openconfig-interfaces",
            elem=[
                PathElem(
                    name="interfaces",
                ),
                PathElem(name="interface", key={"name": interface_name}),
                PathElem(name="config"),
                PathElem(name="mtu"),
            ],
        ),{"openconfig-interfaces:mtu": mtu}))
        
    if loopback is not None:
        updates.append(create_gnmi_update(
         Path(
            target="openconfig",
            origin="openconfig-interfaces",
            elem=[
                PathElem(
                    name="interfaces",
                ),
                PathElem(name="interface", key={"name": interface_name}),
                PathElem(name="config"),
                PathElem(name="loopback-mode"),
            ],
        ),{"openconfig-interfaces:loopback-mode": loopback}))
    
    
    if description is not None:
        updates.append(create_gnmi_update(
         Path(
            target="openconfig",
            origin="openconfig-interfaces",
            elem=[
                PathElem(
                    name="interfaces",
                ),
                PathElem(name="interface", key={"name": interface_name}),
                PathElem(name="config"),
                PathElem(name="description"),
            ],
        ),{"openconfig-interfaces:description": description}))
    
    if speed is not None:
        updates.append(create_gnmi_update(
         Path(
            target="openconfig",
            origin="openconfig-interfaces",
            elem=[
                PathElem(
                    name="interfaces",
                ),
                PathElem(name="interface", key={"name": interface_name}),
                PathElem(name="openconfig-if-ethernet:ethernet"),
                #PathElem(name="ethernet"),
                PathElem(name="config"),
                PathElem(name="port-speed"),
            ],
        ),{"openconfig-if-ethernet:port-speed": str(speed)}))
    
    if updates:
        return send_gnmi_set(
            create_req_for_update(updates),
            device_ip,
        )
    else :
        return None


def get_all_interfaces(device_ip: str):
    path_intf = Path(
        target="openconfig",
        origin="openconfig-interfaces",
        elem=[
            PathElem(
                name="interfaces",
            ),
            PathElem(
                name="interface",
            ),
        ],
    )
    return send_gnmi_get(device_ip=device_ip, path=[path_intf])

def get_interface(device_ip: str,intfc_name:str):
    path_intf = Path(
        target="openconfig",
        origin="openconfig-interfaces",
        elem=[
            PathElem(
                name="interfaces",
            ),
            PathElem(name="interface", key={"name": intfc_name}),
        ],
    )
    return send_gnmi_get(device_ip=device_ip, path=[path_intf])

def get_interface_speed(device_ip: str,intfc_name:str):
    path_intf =  Path(
            target="openconfig",
            origin="openconfig-interfaces",
            elem=[
                PathElem(
                    name="interfaces",
                ),
                PathElem(name="interface", key={"name": intfc_name}),
                PathElem(name="openconfig-if-ethernet:ethernet"),
                #PathElem(name="ethernet"),
                PathElem(name="config"),
                PathElem(name="port-speed"),
            ],
        )
    return send_gnmi_get(device_ip=device_ip, path=[path_intf])

def get_interface_status(device_ip: str,intfc_name:str):
    path_intf =   Path(
            target="openconfig",
            origin="openconfig-interfaces",
            elem=[
                PathElem(
                    name="interfaces",
                ),
                PathElem(name="interface", key={"name": intfc_name}),
                PathElem(name="config"),
                PathElem(name="enabled"),
            ],
        )
    return send_gnmi_get(device_ip=device_ip, path=[path_intf])
