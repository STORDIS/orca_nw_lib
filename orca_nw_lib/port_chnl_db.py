from typing import List
from .device_db import get_device_db_obj
from .graph_db_models import Device, Interface, PortChannel
from .interface_db import get_interface_of_device_from_db
from .utils import get_logging

_logger = get_logging().getLogger(__name__)

def get_port_chnl_of_device_from_db(device_ip: str, port_chnl_name: str) -> PortChannel:
    """
    Get the port channel of a device from the database.

    Args:
        device_ip (str): The IP address of the device.
        port_chnl_name (str): The name of the port channel.

    Returns:
        PortChannel: The port channel object if found, None otherwise.
    """

    device = get_device_db_obj(device_ip)
    return device.port_chnl.get_or_none(lag_name=port_chnl_name) if device else None


def del_port_chnl_of_device_from_db(device_ip: str, port_chnl_name: str):
    """
    Deletes the specified port channel of a device from the database.

    Parameters:
        device_ip (str): The IP address of the device.
        port_chnl_name (str): The name of the port channel.

    Returns:
        None
    """
    device = get_device_db_obj(device_ip)
    chnl = device.port_chnl.get_or_none(lag_name=port_chnl_name) if device else None
    if chnl:
        chnl.delete()


def get_all_port_chnl_of_device_from_db(device_ip: str) -> List[PortChannel]:
    """
    Retrieve all port channels associated with a device from the database.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        List[PortChannel]: A list of port channel objects associated with the device.
    """
    device = get_device_db_obj(device_ip)
    return device.port_chnl.all() if device else None


def get_port_chnl_members_from_db(
    device_ip: str, port_chnl_name: str, if_name: str = None
) -> Interface | List[Interface]:
    """
    Retrieves the members of a port channel from the database.

    Args:
        device_ip (str): The IP address of the device.
        port_chnl_name (str): The name of the port channel.
        if_name (str, optional): The name of the interface. Defaults to None.

    Returns:
        Union[Interface, List[Interface]]: If `if_name` is provided and
        a matching port channel is found,
        returns the specified interface. If `if_name` is not provided and
        a matching port channel is found,returns a list of all interface members.
        If no matching port channel is found, returns None.
    """

    chnl = get_port_chnl_of_device_from_db(device_ip, port_chnl_name)
    return (
        chnl.members.get_or_none(if_name)
        if if_name and chnl
        else chnl.members.all()
        if chnl
        else None
    )


def copy_port_chnl_prop(target_obj: PortChannel, src_obj: PortChannel):
    """
    Copy the properties of a source PortChannel object to a target PortChannel object.

    Args:
        target_obj (PortChannel): The target PortChannel object to copy the properties to.
        src_obj (PortChannel): The source PortChannel object to copy the properties from.

    Returns:
        None
    """
    target_obj.lag_name = src_obj.lag_name
    target_obj.active = src_obj.active
    target_obj.admin_sts = src_obj.admin_sts
    target_obj.mtu = src_obj.mtu
    target_obj.name = src_obj.name  # name of protocol e.g. lacp
    target_obj.fallback_operational = src_obj.fallback_operational
    target_obj.oper_sts = src_obj.oper_sts
    target_obj.speed = src_obj.speed
    target_obj.oper_sts_reason = src_obj.oper_sts_reason
    target_obj.static = src_obj.static
    target_obj.min_links = src_obj.min_links
    target_obj.fallback = src_obj.fallback
    target_obj.description = src_obj.description
    target_obj.fast_rate = src_obj.fast_rate
    target_obj.graceful_shutdown_mode = src_obj.graceful_shutdown_mode
    target_obj.ip_address = src_obj.ip_address
    target_obj.vlan_members = src_obj.vlan_members


def insert_device_port_chnl_in_db(device: Device, portchnl_to_mem_list):
    """
    Inserts device port channels into the database.

    Args:
        device (Device): The device object.
        portchnl_to_mem_list (dict): A dictionary mapping port channels
        to a list of member interfaces.

    Returns:
        None

    Raises:
        None

    """
    _logger.debug(f"Inserting port channels in the DB for device {device.mgt_ip} {portchnl_to_mem_list}")
    for chnl, mem_list in portchnl_to_mem_list.items() or []:
        if p_chnl := get_port_chnl_of_device_from_db(device.mgt_ip, chnl.lag_name):
            copy_port_chnl_prop(p_chnl, chnl)
            p_chnl.save()
            device.port_chnl.connect(p_chnl)
        else:
            chnl.save()
            device.port_chnl.connect(chnl)
        saved_p_chnl = get_port_chnl_of_device_from_db(device.mgt_ip, chnl.lag_name)
        ## For updating Port channel members in db, lets first disconnect any existing members and recreate membership in DB.
        ## It will cater case when vlan has members are in db but not on device.
        ## Also the case when members has been changed/updated.
        saved_p_chnl.members.disconnect_all()
        for intf_name in mem_list or []:
            _logger.debug(f"retrieving intf from DB {intf_name}")
            intf_obj = get_interface_of_device_from_db(device.mgt_ip, intf_name)
            if saved_p_chnl and intf_obj:
                _logger.debug(f"Found interface {intf_name}")
                saved_p_chnl.members.connect(intf_obj)

    ## Handle the case when some or all port_chnl has been deleted from device but remained in DB
    ## Remove all port_chnl which are in DB but not on device
    for chnl_in_db in get_all_port_chnl_of_device_from_db(device.mgt_ip) or []:
        if chnl_in_db not in portchnl_to_mem_list:
            del_port_chnl_of_device_from_db(device.mgt_ip, chnl_in_db.lag_name)
            
        ## Also disconnect interfaces if not a member of channel
        #chnl_members_on_device = portchnl_to_mem_list.get(chnl_in_db)
        #for mem in chnl_in_db.members.all() or []:
        #    if mem.name not in chnl_members_on_device:
        #        chnl_in_db.members.disconnect(mem)
