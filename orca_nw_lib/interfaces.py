import datetime
from typing import List

import pytz

from orca_nw_lib.common import Speed, getSpeedStrFromOCStr
from orca_nw_lib.device import getAllDevicesFromDB, getDeviceFromDB
from orca_nw_lib.gnmi_pb2 import Path, PathElem
from orca_nw_lib.gnmi_util import (
    create_gnmi_update,
    create_req_for_update,
    get_gnmi_del_req,
    send_gnmi_get,
    send_gnmi_set,
)
from orca_nw_lib.graph_db_models import Device, Interface, SubInterface
import orca_nw_lib.portgroup as pg
from orca_nw_lib.utils import get_logging


_logger = get_logging().getLogger(__name__)


def createInterfaceGraphObjects(device_ip: str) -> List[Interface]:
    interfaces_json = get_all_interfaces_from_device(device_ip)
    intfc_graph_obj_list = {}
    for intfc in interfaces_json.get("openconfig-interfaces:interface") or []:
        intfc_state = intfc.get("state", {})
        intfc_counters = intfc_state.get("counters", {})
        type = intfc.get("config").get("type")

        if (
            "ether" or "loopback" in type.lower()
        ) and "PortChannel" not in intfc_state.get("name"):
            # Port channels are separately discovered so skip them in interface discovery
            interface = Interface(
                name=intfc_state.get("name"),
                enabled=intfc_state.get("enabled"),
                mtu=intfc_state.get("mtu"),
                fec=intfc.get("openconfig-if-ethernet:ethernet", {})
                .get("config", {})
                .get("openconfig-if-ethernet-ext2:port-fec"),
                speed=getSpeedStrFromOCStr(s)
                if (
                    s := intfc.get("openconfig-if-ethernet:ethernet", {})
                    .get("config", {})
                    .get("port-speed")
                )
                else None,
                oper_sts=intfc_state.get("oper-status"),
                admin_sts=intfc_state.get("admin-status"),
                description=intfc_state.get("description"),
                last_chng=(
                    (lambda utc_date: f"{str(utc_date)} {utc_date.tzinfo}")(
                        datetime.datetime.utcfromtimestamp(int(last_chng)).replace(
                            tzinfo=pytz.utc
                        )
                        if (last_chng := 1688989316)
                        else 0
                    )
                ),
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
            for sub_intfc in intfc.get("subinterfaces", {}).get("subinterface", {}):
                sub_intf_obj = SubInterface()
                for addr in (
                    sub_intfc.get("openconfig-if-ip:ipv4", {})
                    .get("addresses", {})
                    .get("address")
                    or []
                ):
                    if addr.get("ip"):
                        sub_intf_obj.ip_address = addr.get("ip")
                    sub_intf_obj_list.append(sub_intf_obj)

            intfc_graph_obj_list[interface] = sub_intf_obj_list
        elif "lag" in type.lower():
            # its a port channel
            pass
        else:
            _logger.error(f"Unknown Interface type {type}")

    return intfc_graph_obj_list


def getAllInterfacesOfDeviceFromDB(device_ip: str):
    device = getDeviceFromDB(device_ip)
    return device.interfaces.all() if device else None


def getInterfaceOfDeviceFromDB(device_ip: str, interface_name: str) -> Interface:
    device = getDeviceFromDB(device_ip)
    return (
        getDeviceFromDB(device_ip).interfaces.get_or_none(name=interface_name)
        if device
        else None
    )


def getSubInterfaceOfDeviceFromDB(device_ip: str, sub_if_ip: str) -> SubInterface:
    for intf in getAllInterfacesOfDeviceFromDB(device_ip) or []:
        if si := intf.subInterfaces.get_or_none(ip_address=sub_if_ip):
            return si


def getSubInterfaceFromDB(sub_if_ip: str) -> SubInterface:
    devices = getAllDevicesFromDB()
    for device in devices:
        if si := getSubInterfaceOfDeviceFromDB(device.mgt_ip, sub_if_ip):
            return si


def getInterfacesDetailsFromDB(device_ip: str, intfc_name=None):
    op_dict = []

    if intfc_name:
        intfc = getInterfaceOfDeviceFromDB(device_ip, intfc_name)
        if intfc:
            op_dict.append(intfc.__properties__)
    else:
        interfaces = getAllInterfacesOfDeviceFromDB(device_ip)
        for intfc in interfaces or []:
            op_dict.append(intfc.__properties__)
    return op_dict


def get_possible_speeds():
    return [str(e) for e in Speed]


def get_interface_base_path():
    return Path(
        target="openconfig",
        elem=[
            PathElem(
                name="openconfig-interfaces:interfaces",
            )
        ],
    )


def get_interface_path(intfc_name: str):
    path = get_interface_base_path()
    path.elem.append(PathElem(name="interface", key={"name": intfc_name}))
    return path


def get_sub_interface_base_path(intfc_name: str):
    path = get_interface_path(intfc_name)
    path.elem.append(PathElem(name="subinterfaces"))
    return path


def get_sub_interface_path(intfc_name: str):
    path = get_sub_interface_base_path(intfc_name)
    path.elem.append(PathElem(name="subinterface"))
    return path


def get_sub_interface_index_path(intfc_name: str, index: int):
    path = get_sub_interface_base_path(intfc_name)
    path.elem.append(PathElem(name="subinterface", key={"index": str(index)}))
    return path


def get_all_interfaces_path():
    path = get_interface_base_path()
    path.elem.append(PathElem(name="interface"))
    return path


def get_intfc_config_path(intfc_name: str):
    path = get_interface_path(intfc_name)
    path.elem.append(PathElem(name="config"))
    return path


def get_intfc_speed_path(intfc_name: str):
    path = get_interface_path(intfc_name)
    path.elem.append(PathElem(name="openconfig-if-ethernet:ethernet"))
    path.elem.append(PathElem(name="config"))
    path.elem.append(PathElem(name="port-speed"))
    return path


def get_intfc_enabled_path(intfc_name: str):
    path = get_intfc_config_path(intfc_name)
    path.elem.append(PathElem(name="enabled"))
    return path


def set_interface_config_on_device(
    device_ip: str,
    interface_name: str,
    enable: bool = None,
    mtu: int = None,
    loopback: bool = None,
    description: str = None,
    speed: Speed = None,
    ip: str = None,
    ip_prefix_len: int = 0,
    index: int = 0,
):
    updates = []

    if enable is not None:
        updates.append(
            create_gnmi_update(
                get_intfc_enabled_path(interface_name),
                {"openconfig-interfaces:enabled": enable},
            )
        )

    if mtu is not None:
        base_config_path = get_intfc_config_path(interface_name)
        base_config_path.elem.append(PathElem(name="mtu"))
        updates.append(
            create_gnmi_update(
                base_config_path,
                {"openconfig-interfaces:mtu": mtu},
            )
        )

    if loopback is not None:
        base_config_path = get_intfc_config_path(interface_name)
        base_config_path.elem.append(PathElem(name="loopback-mode"))
        updates.append(
            create_gnmi_update(
                base_config_path,
                {"openconfig-interfaces:loopback-mode": loopback},
            )
        )

    if description is not None:
        base_config_path = get_intfc_config_path(interface_name)
        base_config_path.elem.append(PathElem(name="description"))
        updates.append(
            create_gnmi_update(
                base_config_path,
                {"openconfig-interfaces:description": description},
            )
        )

    if speed is not None:
        # if switch supports port groups then configure speed on port-group otherwise directly on interface
        if pg.getAllPortGroupsOfDeviceFromDB(
            device_ip
        ) and pg.getPortGroupIDOfDeviceInterfaceFromDB(device_ip, interface_name):
            pg_id = pg.getPortGroupIDOfDeviceInterfaceFromDB(device_ip, interface_name)
            updates.append(
                create_gnmi_update(
                    pg._get_port_group_speed_path(pg_id),
                    {"openconfig-port-group:speed": speed.get_oc_val()},
                )
            )

        else:
            updates.append(
                create_gnmi_update(
                    get_intfc_speed_path(interface_name),
                    {"port-speed": speed.get_oc_val()},
                )
            )

    if ip is not None:
        ip_payload = {
            "openconfig-interfaces:subinterface": [
                {
                    "config": {"index": index},
                    "index": index,
                    "openconfig-if-ip:ipv4": {
                        "addresses": {
                            "address": [
                                {
                                    "ip": ip,
                                    "config": {
                                        "prefix-length": ip_prefix_len,
                                        "secondary": False,
                                    },
                                }
                            ]
                        }
                    },
                }
            ]
        }
        updates.append(
            create_gnmi_update(
                get_sub_interface_path(interface_name),
                ip_payload,
            )
        )

    if updates:
        return send_gnmi_set(
            create_req_for_update(updates),
            device_ip,
        )
    else:
        return None


def get_all_interfaces_from_device(device_ip: str):
    return send_gnmi_get(device_ip=device_ip, path=[get_all_interfaces_path()])


def get_interface_from_device(device_ip: str, intfc_name: str):
    return send_gnmi_get(device_ip=device_ip, path=[get_interface_path(intfc_name)])


def get_interface_config_from_device(device_ip: str, intfc_name: str):
    return send_gnmi_get(device_ip=device_ip, path=[get_intfc_config_path(intfc_name)])


def get_interface_speed_from_device(device_ip: str, intfc_name: str):
    return send_gnmi_get(device_ip=device_ip, path=[get_intfc_speed_path(intfc_name)])


def get_interface_status_from_device(device_ip: str, intfc_name: str):
    return send_gnmi_get(device_ip=device_ip, path=[get_intfc_enabled_path(intfc_name)])


def get_subinterface_from_device(device_ip: str, intfc_name: str):
    return send_gnmi_get(device_ip=device_ip, path=[get_sub_interface_path(intfc_name)])


def insert_device_interfaces_in_db(device: Device, interfaces: dict):
    for intfc, sub_intfc in interfaces.items():
        intfc.save()
        device.interfaces.connect(intfc)
        for sub_i in sub_intfc:
            sub_i.save()
            intfc.subInterfaces.connect(sub_i)


def getAllInterfacesNameOfDeviceFromDB(device_ip: str):
    intfcs = getAllInterfacesOfDeviceFromDB(device_ip)
    return [intfc.name for intfc in intfcs] if intfcs else None


def set_interface_config_in_db(
    device_ip: str, if_name: str, enable: bool = None, mtu=None, speed: Speed = None
):
    interface = getInterfaceOfDeviceFromDB(device_ip, if_name)
    if interface:
        if enable is not None:
            interface.enabled = enable
        if mtu is not None:
            interface.mtu = mtu
        if speed is not None:
            interface.speed = str(speed)
    interface.save()


def del_subinterface_of_interface_from_device(device_ip: str, if_name: str, index: int):
    return send_gnmi_set(
        get_gnmi_del_req(get_sub_interface_index_path(if_name, index)), device_ip
    )


def del_all_subinterfaces_of_interface_from_device(device_ip: str, if_name: str):
    return send_gnmi_set(get_gnmi_del_req(get_sub_interface_path(if_name)), device_ip)

def del_all_subinterfaces_of_all_interfaces_from_device(device_ip: str):
    for ether in getAllInterfacesNameOfDeviceFromDB(device_ip):
        del_all_subinterfaces_of_interface_from_device(device_ip, ether)

def get_all_subinterfaces_of_interface_from_device(device_ip: str, if_name: str):
    return send_gnmi_get(device_ip=device_ip, path=[get_sub_interface_path(if_name)])


def get_subinterface_from_device(device_ip: str, if_name: str, index: int):
    return send_gnmi_get(
        device_ip=device_ip, path=[get_sub_interface_index_path(if_name, index)]
    )
