import json
import logging
from typing import List
from orca_backend.gnmi_pb2 import Path, PathElem
from orca_backend.gnmi_util import send_gnmi_set, get_gnmi_update_req, send_gnmi_get
from orca_backend.graph_db_models import Interface, PortChannel
from orca_backend.graph_db_utils import getAllInterfacesOfDevice
_logger=logging.getLogger(__name__)

def createInterfaceGraphObjects(device_ip: str) -> List[Interface]:
    interfaces_json = get_all_interfaces(device_ip)
    intfc_graph_obj_list = []
    for intfc in interfaces_json.get('openconfig-interfaces:interface'):
        intfc_state = intfc.get('state')
        intfc_counters = intfc_state.get('counters')
        type=intfc.get('config').get('type')
        name=intfc.get('config').get('name')
        if 'ether' in type.lower():
            intfc_graph_obj_list.append(Interface(name=intfc_state.get('name'),
                                                enabled=intfc_state.get(
                                                    'enabled'),
                                                mtu=intfc_state.get('mtu'),
                                                fec=intfc.get('openconfig-if-ethernet:ethernet').get(
                                                    'config').get('openconfig-if-ethernet-ext2:port-fec'),
                                                speed=intfc.get(
                                                    'openconfig-if-ethernet:ethernet').get('config').get('port-speed'),
                                                oper_sts=intfc_state.get(
                                                    'oper-status'),
                                                admin_sts=intfc_state.get(
                                                    'admin-status'),
                                                description=intfc_state.get(
                                                    'description'),
                                                last_chng=intfc_state.get(
                                                    'last-change'),
                                                mac_addr=intfc_state.get(
                                                    'mac-address'),
                                                in_bits_per_second=intfc_counters.get(
                                                    'in-bits-per-second'),
                                                in_broadcast_pkts=intfc_counters.get(
                                                    'in-broadcast-pkts'),
                                                in_discards=intfc_counters.get(
                                                    'in-discards'),
                                                in_errors=intfc_counters.get(
                                                    'in-errors'),
                                                in_multicast_pkts=intfc_counters.get(
                                                    'in-multicast-pkts'),
                                                in_octets=intfc_counters.get(
                                                    'in-octets'),
                                                in_octets_per_second=intfc_counters.get(
                                                    'in-octets-per-second'),
                                                in_pkts=intfc_counters.get(
                                                    'in-pkts'),
                                                in_pkts_per_second=intfc_counters.get(
                                                    'in-pkts-per-second'),
                                                in_unicast_pkts=intfc_counters.get(
                                                    'in-unicast-pkts'),
                                                in_utilization=intfc_counters.get(
                                                    'in-utilization'),
                                                last_clear=intfc_counters.get(
                                                    'last-clear'),
                                                out_bits_per_second=intfc_counters.get(
                                                    'out-bits-per-second'),
                                                out_broadcast_pkts=intfc_counters.get(
                                                    'out-broadcast-pkts'),
                                                out_discards=intfc_counters.get(
                                                    'out-discards'),
                                                out_errors=intfc_counters.get(
                                                    'out-errors'),
                                                out_multicast_pkts=intfc_counters.get(
                                                    'out-multicast-pkts'),
                                                out_octets=intfc_counters.get(
                                                    'out-octets'),
                                                out_octets_per_second=intfc_counters.get(
                                                    'out-octets-per-second'),
                                                out_pkts=intfc_counters.get(
                                                    'out-pkts'),
                                                out_pkts_per_second=intfc_counters.get(
                                                    'out-pkts-per-second'),
                                                out_unicast_pkts=intfc_counters.get(
                                                    'out-unicast-pkts'),
                                                out_utilization=intfc_counters.get(
                                                    'out-utilization')
                                                ))
        elif 'lag' in type.lower():
            #its a poert channel
            pass
        else:
            _logger.error(f'Unknown Interface type {type}')

    return intfc_graph_obj_list


def getInterfacesDetailsFromGraph(device_ip:str):
    interfaces=getAllInterfacesOfDevice(device_ip)
    op_dict = []
    for intfc in interfaces or []:
        op_dict.append(intfc.__properties__)
    return op_dict


def enable_interface(device_ip: str, interface_name: str, enable: bool):
    path_intf_status_path = Path(target='openconfig',
                                 origin='openconfig-interfaces',
                                 elem=[PathElem(name="interfaces", ),
                                       PathElem(name="interface", key={
                                                "name": interface_name}),
                                       PathElem(name="config"),
                                       PathElem(name="enabled"),
                                       ])
    return send_gnmi_set(get_gnmi_update_req(path_intf_status_path,
                                             {"openconfig-interfaces:enabled": enable}), device_ip)


def get_all_interfaces(device_ip: str):
    path_intf = Path(target='openconfig',
                     origin='openconfig-interfaces',
                     elem=[PathElem(name="interfaces", ),
                           PathElem(name="interface",)
                           ])
    return send_gnmi_get(device_ip=device_ip, path=[path_intf])



