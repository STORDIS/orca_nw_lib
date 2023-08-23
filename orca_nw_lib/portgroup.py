from typing import List
from orca_nw_lib.common import Speed, getSpeedStrFromOCStr
from orca_nw_lib.device import getDeviceFromDB
from orca_nw_lib.gnmi_pb2 import Path, PathElem
from orca_nw_lib.gnmi_util import (
    create_gnmi_update,
    create_req_for_update,
    send_gnmi_get,
    send_gnmi_set,
)
from orca_nw_lib.graph_db_models import Device, Interface, PortGroup
import orca_nw_lib.interfaces as orca_interfaces
from orca_nw_lib.utils import get_logging


_logger = get_logging().getLogger(__name__)


def createPortGroupGraphObjects(device_ip: str):
    port_groups_json = get_port_groups(device_ip)
    port_group_graph_objs = {}
    for port_group in port_groups_json.get("openconfig-port-group:port-group") or []:
        port_group_state = port_group.get("state", {})
        default_speed = getSpeedStrFromOCStr(port_group_state.get("default-speed"))
        member_if_start = port_group_state.get("member-if-start")
        member_if_end = port_group_state.get("member-if-end")
        valid_speeds = [
            getSpeedStrFromOCStr(s) for s in port_group_state.get("valid-speeds")
        ]
        speed = getSpeedStrFromOCStr(port_group_state.get("speed"))
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


def _get_port_groups_base_path():
    return Path(
        target="openconfig",
        origin="openconfig-port-group",
        elem=[
            PathElem(
                name="port-groups",
            ),
        ],
    )


def _get_port_groups_path():
    path = _get_port_groups_base_path()
    path.elem.append(
        PathElem(
            name="port-group",
        )
    )
    return path


def _get_port_group_path(id: str):
    path = _get_port_groups_base_path()
    path.elem.append(PathElem(name="port-group", key={"id": str(id)}))
    return path


def _get_port_group_config_path(id: str):
    path = _get_port_group_path(id)
    path.elem.append(PathElem(name="config"))
    return path


def _get_port_group_speed_path(id: str):
    path = _get_port_group_config_path(id)
    path.elem.append(PathElem(name="speed"))
    return path


def get_port_groups(device_ip: str):
    return send_gnmi_get(device_ip=device_ip, path=[_get_port_groups_path()])


def get_port_group(device_ip: str, id: int):
    return send_gnmi_get(device_ip=device_ip, path=[_get_port_group_path(id)])


def get_port_group_speed(device_ip: str, id: int):
    return send_gnmi_get(device_ip=device_ip, path=[_get_port_group_speed_path(id)])


def set_port_group_speed(device_ip: str, id: int, speed: Speed):
    return send_gnmi_set(
        create_req_for_update(
            [
                create_gnmi_update(
                    _get_port_group_speed_path(id),
                    {"openconfig-port-group:speed": speed.get_oc_val()},
                )
            ]
        ),
        device_ip,
    )


def getAllPortGroupsOfDeviceFromDB(device_ip: str):
    device: Device = getDeviceFromDB(device_ip)
    return device.port_groups.all() if device else None


def getPortGroupIDOfDeviceInterfaceFromDB(device_ip: str, inertface_name: str):
    ## TODO: Following query certainly has scope of performance enhancement.
    for pg in getAllPortGroupsOfDeviceFromDB(device_ip):
        for intf in pg.memberInterfaces.all():
            if intf.name == inertface_name:
                return pg.port_group_id
    return None


def getPortGroupFromDB(device_ip: str, group_id):
    device: Device = getDeviceFromDB(device_ip)
    return device.port_groups.get_or_none(port_group_id=group_id) if device else None


def getPortGroupMemIFFromDB(device_ip: str, group_id) -> List[Interface]:
    port_group_obj = getPortGroupFromDB(device_ip, group_id)
    return port_group_obj.memberInterfaces.all() if port_group_obj else None


def getPortGroupMemIFNamesFromDB(device_ip: str, group_id) -> List[str]:
    intfcs = getPortGroupMemIFFromDB(device_ip, group_id)
    return [intf.name for intf in intfcs or []]


def copy_portgr_obj_prop(target_obj: PortGroup, src_obj: PortGroup):
    target_obj.port_group_id = src_obj.port_group_id
    target_obj.speed = src_obj.speed
    target_obj.valid_speeds = src_obj.valid_speeds
    target_obj.default_speed = src_obj.default_speed


def insert_device_port_groups_in_db(device: Device = None, port_groups: dict = None):
    for pg, mem_intfcs in port_groups.items():
        if p := getPortGroupFromDB(device.mgt_ip, pg.port_group_id):
            copy_portgr_obj_prop(p, pg)
            p.save()
            device.port_groups.connect(p)
        else:
            pg.save()
            device.port_groups.connect(pg)

        saved_pg = getPortGroupFromDB(device.mgt_ip, pg.port_group_id)
        
        for if_name in mem_intfcs:
            saved_pg.memberInterfaces.connect(intf) if (
                intf := orca_interfaces.getInterfaceOfDeviceFromDB(
                    device.mgt_ip, if_name
                )
            ) and saved_pg else None


def getJsonOfPortGroupMemIfFromDB(device_ip: str, group_id):
    op_dict = []
    mem_intfcs = getPortGroupMemIFFromDB(device_ip, group_id)
    if mem_intfcs:
        for mem_if in mem_intfcs or []:
            op_dict.append(mem_if.__properties__)
    return op_dict


def getJsonOfAllPortGroupsOfDeviceFromDB(device_ip: str):
    op_dict = []
    port_groups = getAllPortGroupsOfDeviceFromDB(device_ip)
    if port_groups:
        for pg in port_groups or []:
            temp = pg.__properties__
            temp["mem_intfs"] = getPortGroupMemIFNamesFromDB(
                device_ip, pg.port_group_id
            )
            op_dict.append(temp)
    return op_dict
