from orca_nw_lib.common import Speed
from orca_nw_lib.device import getDeviceFromDB
from orca_nw_lib.gnmi_pb2 import Path, PathElem
from orca_nw_lib.gnmi_util import (
    create_gnmi_update,
    create_req_for_update,
    send_gnmi_get,
    send_gnmi_set,
)
from orca_nw_lib.graph_db_models import Device, PortGroup
import orca_nw_lib.interfaces as orca_interfaces
from orca_nw_lib.utils import get_logging


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
        intfc = orca_interfaces.getInterfaceOfDeviceFromDB(device_ip, intfc_name)
        if intfc:
            op_dict.append(intfc.__properties__)
    else:
        interfaces = orca_interfaces.getAllInterfacesOfDeviceFromDB(device_ip)
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


def get_port_group_path(id: str):
    path = get_port_groups_base_path()
    path.elem.append(PathElem(name="port-group", key={"id": str(id)}))
    return path


def get_port_group_config_path(id: str):
    path = get_port_group_path(id)
    path.elem.append(PathElem(name="config"))
    return path


def get_port_group_speed_path(id: str):
    path = get_port_group_config_path(id)
    path.elem.append(PathElem(name="speed"))
    return path


def get_port_groups(device_ip: str):
    return send_gnmi_get(device_ip=device_ip, path=[get_port_groups_path()])


def get_port_group(device_ip: str, id: int):
    return send_gnmi_get(device_ip=device_ip, path=[get_port_group_path(id)])


def get_port_group_speed(device_ip: str, id: int):
    return send_gnmi_get(device_ip=device_ip, path=[get_port_group_speed_path(id)])


def set_port_group_speed(device_ip: str, id: int, speed: Speed):
    return send_gnmi_set(
        create_req_for_update(
            [
                create_gnmi_update(
                    get_port_group_speed_path(id),
                    {"openconfig-port-group:speed": speed.get_gnmi_val()},
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


def insert_device_port_groups_in_db(device: Device = None, port_groups: dict = None):
    for pg, mem_intfcs in port_groups.items():
        pg.save()
        device.port_groups.connect(pg)
        for if_name in mem_intfcs:
            intf = orca_interfaces.getInterfaceOfDeviceFromDB(device.mgt_ip, if_name)
            if intf:
                pg.memberInterfaces.connect(intf)
