from typing import List
from orca_nw_lib.common import Speed
from orca_nw_lib.device_db import get_device_db_obj
import orca_nw_lib.interface_db as orca_interfaces
from orca_nw_lib.graph_db_models import Device, Interface, PortGroup


def copy_portgr_obj_prop(target_obj: PortGroup, src_obj: PortGroup):
    """
    Copies the properties of one PortGroup object to another.

    Args:
        target_obj (PortGroup): The target PortGroup object to copy the properties to.
        src_obj (PortGroup): The source PortGroup object to copy the properties from.

    Returns:
        None
    """
    target_obj.port_group_id = src_obj.port_group_id
    target_obj.speed = src_obj.speed
    target_obj.valid_speeds = src_obj.valid_speeds
    target_obj.default_speed = src_obj.default_speed


def get_port_group_from_db(device_ip: str, group_id=None):
    device: Device = get_device_db_obj(device_ip)
    if device:
        return (
            device.port_groups.get_or_none(port_group_id=group_id)
            if group_id
            else device.port_groups.all()
        )


def get_all_port_group_ids_from_db(device_ip: str):
    device: Device = get_device_db_obj(device_ip)
    if device:
        return [pg.port_group_id for pg in get_port_group_from_db(device_ip) or []]


def insert_device_port_groups_in_db(device: Device = None, port_groups: dict = None):
    """
    Insert device port groups in the database.

    Args:
        device (Device, optional): The device object. Defaults to None.
        port_groups (dict, optional): A dictionary of port groups. Defaults to None.

    Returns:
        None
    """
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
            (
                saved_pg.memberInterfaces.connect(intf)
                if (
                    intf := orca_interfaces.get_interface_of_device_from_db(
                        device.mgt_ip, if_name
                    )
                )
                and saved_pg
                else None
            )


def set_port_group_speed_in_db(device_ip: str, group_id: str, speed: Speed):
    """
    Set the speed of a port group in the database.

    Args:
        device_ip (str): The IP address of the device.
        group_id (str): The ID of the port group.
        speed (int): The speed of the port group.

    Returns:
        None
    """
    port_group_obj = get_port_group_from_db(device_ip, group_id)
    if port_group_obj:
        port_group_obj.speed = str(speed)
        port_group_obj.save()


def get_port_group_member_from_db(device_ip: str, group_id) -> List[Interface]:
    """
    Get the port group member interfaces from the database.

    Args:
        device_ip (str): The IP address of the device.
        group_id: The ID of the port group.

    Returns:
        List[Interface]: A list of member interfaces of the port group.
            Returns None if the port group does not exist.
    """
    port_group_obj = get_port_group_from_db(device_ip, group_id)
    return port_group_obj.memberInterfaces.all() if port_group_obj else None


def get_port_group_member_names_from_db(device_ip: str, group_id) -> List[str]:
    """
    Retrieve the names of the port group members from the database.

    Args:
        device_ip (str): The IP address of the device.
        group_id: The ID of the port group.

    Returns:
        List[str]: A list containing the names of the port group members from the database.
    """
    intfcs = get_port_group_member_from_db(device_ip, group_id)
    return [intf.name for intf in intfcs or []]


def get_port_group_of_if_from_db(device_ip: str, interface_name: str) -> PortGroup:
    """
    Retrieve the port group object of an interface from the database.

    Args:
        device_ip (str): The IP address of the device.
        interface_name: The name of the interface.

    Returns:
        PortGroup: The port group object of the interface.
    """

    ## TODO: Following query certainly has scope of performance enhancement.
    ## retrieve the port group object via relation.
    for pg in get_port_group_from_db(device_ip) or []:
        for intf in pg.memberInterfaces.all():
            if intf.name == interface_name:
                return pg
    return None


def get_port_group_id_of_device_interface_from_db(device_ip: str, inertface_name: str):
    return (
        pg.port_group_id
        if (pg := get_port_group_of_if_from_db(device_ip, inertface_name))
        else None
    )
