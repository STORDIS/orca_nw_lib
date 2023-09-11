from typing import List
from orca_nw_lib.device_db import get_device_db_obj
import orca_nw_lib.interface_db as orca_interfaces
from orca_nw_lib.graph_db_models import Device, Interface, PortGroup


def copy_portgr_obj_prop(target_obj: PortGroup, src_obj: PortGroup):
    target_obj.port_group_id = src_obj.port_group_id
    target_obj.speed = src_obj.speed
    target_obj.valid_speeds = src_obj.valid_speeds
    target_obj.default_speed = src_obj.default_speed


def get_port_group_from_db(device_ip: str, group_id):
    device: Device = get_device_db_obj(device_ip)
    return device.port_groups.get_or_none(port_group_id=group_id) if device else None


def insert_device_port_groups_in_db(device: Device = None, port_groups: dict = None):
    for pg, mem_intfcs in port_groups.items():
        if p := get_port_group_from_db(device.mgt_ip, pg.port_group_id):
            copy_portgr_obj_prop(p, pg)
            p.save()
            device.port_groups.connect(p)
        else:
            pg.save()
            device.port_groups.connect(pg)

        saved_pg = get_port_group_from_db(device.mgt_ip, pg.port_group_id)

        for if_name in mem_intfcs:
            saved_pg.memberInterfaces.connect(intf) if (
                intf := orca_interfaces.get_interface_of_device_from_db(
                    device.mgt_ip, if_name
                )
            ) and saved_pg else None


def get_port_group_member_from_db(device_ip: str, group_id) -> List[Interface]:
    port_group_obj = get_port_group_from_db(device_ip, group_id)
    return port_group_obj.memberInterfaces.all() if port_group_obj else None


def get_port_group_member_names_from_db(device_ip: str, group_id) -> List[str]:
    intfcs = get_port_group_member_from_db(device_ip, group_id)
    return [intf.name for intf in intfcs or []]


def get_all_port_groups_of_device_from_db(device_ip: str):
    device: Device = get_device_db_obj(device_ip)
    return device.port_groups.all() if device else None


def get_port_group_id_of_device_interface_from_db(device_ip: str, inertface_name: str):
    ## TODO: Following query certainly has scope of performance enhancement.
    for pg in get_all_port_groups_of_device_from_db(device_ip):
        for intf in pg.memberInterfaces.all():
            if intf.name == inertface_name:
                return pg.port_group_id
    return None
