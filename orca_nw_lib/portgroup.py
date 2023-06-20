from enum import Enum, auto
import json
from typing import List

from .gnmi_pb2 import Path, PathElem
from .gnmi_util import (
    create_req_for_update,
    send_gnmi_set,
    create_gnmi_update,
    send_gnmi_get,
)
from .graph_db_models import Interface, PortChannel, PortGroup, SubInterface
from .graph_db_utils import getAllInterfacesOfDevice, getInterfaceOfDevice
from .utils import get_logging

_logger = get_logging().getLogger(__name__)


def createPortGroupGraphObjects(device_ip: str):
    port_groups_json = get_port_groups(device_ip)
    port_group_graph_objs = {}
    for port_group in port_groups_json.get("openconfig-port-group:port-group") or []:
        port_group_state = port_group.get("state", {})
        default_speed = port_group_state.get("default-speed")
        member_if_start = port_group_state.get("member-if-start")
        member_if_end = port_group_state.get("member-if-end")
        valid_speeds = port_group_state.get("valid-speeds")
        speed = port_group_state.get("speed")
        id = port_group_state.get("id")

        mem_infcs = []
        for eth_num in range(
            int(member_if_start.replace("Ethernet", "")),
            int(member_if_end.replace("Ethernet", "")) + 1,
        ):
            mem_infcs.append(f"Ethernet{eth_num}")

        port_group_graph_objs[
            PortGroup(
                port_group_id=id,
                speed=speed,
                valid_speeds=valid_speeds,
                default_speed=default_speed,
            )
        ] = mem_infcs

    return port_group_graph_objs


def getInterfacesDetailsFromGraph(device_ip: str, intfc_name=None):
    op_dict = []

    if intfc_name:
        intfc = getInterfaceOfDevice(device_ip, intfc_name)
        if intfc:
            op_dict.append(intfc.__properties__)
    else:
        interfaces = getAllInterfacesOfDevice(device_ip)
        for intfc in interfaces or []:
            op_dict.append(intfc.__properties__)
    return op_dict


def get_port_groups_base_path():
    return Path(
        target="openconfig",
        origin="openconfig-port-group",
        elem=[
            PathElem(
                name="port-groups",
            ),
        ],
    )


def get_port_groups_path():
    path = get_port_groups_base_path()
    path.elem.append(
        PathElem(
            name="port-group",
        )
    )
    return path


def get_port_group_path(id: int):
    path = get_port_groups_base_path()
    path.elem.append(PathElem(name="port-group", key={"port-group": id}))
    return path


def get_port_groups(device_ip: str):
    return send_gnmi_get(device_ip=device_ip, path=[get_port_groups_path()])


def get_port_group(device_ip: str, id: int):
    return send_gnmi_get(device_ip=device_ip, path=[get_port_group_path(id)])
