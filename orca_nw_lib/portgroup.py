from orca_nw_lib.common import getSpeedStrFromOCStr
from orca_nw_lib.device_db import get_device_db_obj
from orca_nw_lib.graph_db_models import PortGroup
from orca_nw_lib.portgroup_gnmi import get_port_group_from_device
from orca_nw_lib.portgroup_db import get_all_port_groups_of_device_from_db, get_port_group_member_from_db, get_port_group_member_names_from_db, insert_device_port_groups_in_db
from orca_nw_lib.utils import get_logging


_logger = get_logging().getLogger(__name__)


def create_port_group_graph_objects(device_ip: str):
    port_groups_json = get_port_group_from_device(device_ip)
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


def get_port_group_members(device_ip: str, group_id):
    op_dict = []
    mem_intfcs = get_port_group_member_from_db(device_ip, group_id)
    if mem_intfcs:
        for mem_if in mem_intfcs or []:
            op_dict.append(mem_if.__properties__)
    return op_dict


def get_port_groups(device_ip: str):
    op_dict = []
    port_groups = get_all_port_groups_of_device_from_db(device_ip)
    if port_groups:
        for pg in port_groups or []:
            temp = pg.__properties__
            temp["mem_intfs"] = get_port_group_member_names_from_db(
                device_ip, pg.port_group_id
            )
            op_dict.append(temp)
    return op_dict


def discover_port_groups():
    _logger.info("Port-groups Discovery Started.")
    for device in get_device_db_obj():
        _logger.info(f"Discovering port-groups of device {device}.")
        insert_device_port_groups_in_db(
            device, create_port_group_graph_objects(device.mgt_ip)
        )
