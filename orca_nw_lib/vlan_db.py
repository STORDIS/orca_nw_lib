from typing import List, Optional

from orca_nw_lib.port_chnl_db import get_port_chnl_of_device_from_db
from .device_db import get_device_db_obj
from .graph_db_models import Device, Vlan
from .interface_db import get_interface_of_device_from_db


def del_vlan_from_db(device_ip, vlan_name: str = None):
    """
    Deletes a VLAN from the database.

    Parameters:
        device_ip (str): The IP address of the device.
        vlan_name (str, optional): The name of the VLAN to be deleted. Defaults to None.

    Returns:
        None
    """
    device: Device = get_device_db_obj(device_ip)
    vlan = device.vlans.get_or_none(name=vlan_name) if device else None
    if vlan:
        vlan.delete()


def get_vlan_obj_from_db(device_ip, vlan_name: str = None):
    """
    Get the VLAN object from the database.

    Parameters:
        device_ip (str): The IP address of the device.
        vlan_name (str, optional): The name of the VLAN. Defaults to None.

    Returns:
        The VLAN object from the database if `vlan_name` is None, otherwise the VLAN object with the specified name.
    """
    device: Device = get_device_db_obj(device_ip)
    return (
        (device.vlans.all()
        if not vlan_name
        else device.vlans.get_or_none(name=vlan_name)) if device else None
    )


def get_vlan_mem_ifcs_from_db(device_ip: str, vlan_name: str) -> Optional[List[str]]:
    """
    Retrieves the member interfaces of a specific VLAN from the device database.

    Args:
        device_ip (str): The IP address of the device.
        vlan_name (str): The name of the VLAN.

    Returns:
        List[str]: A list of member interfaces if the device and VLAN exist in the database,
        otherwise None.
    """

    device: Device = get_device_db_obj(device_ip)
    return (
        v.memberInterfaces.all()
        if device and device.vlans and (v := device.vlans.get_or_none(name=vlan_name))
        else None
    )


def get_vlan_member_port_channels_from_db(device_ip: str, vlan_name: str) -> Optional[List[str]]:
    """
    Retrieves the member port channels of a specific VLAN from the device database.

    Args:
        device_ip (str): The IP address of the device.
        vlan_name (str): The name of the VLAN.

    Returns:
        List[str]: A list of member port channels if the device and VLAN exist in the database,
        otherwise None.
    """

    device: Device = get_device_db_obj(device_ip)
    return (
        v.memberPortChannel.all()
        if device and device.vlans and (v := device.vlans.get_or_none(name=vlan_name))
        else None
    )

def copy_vlan_obj_prop(target_vlan_obj: Vlan, source_vlan_obj: Vlan):
    """
    Copy the properties of one VLAN object to another.

    Args:
        target_vlan_obj (Vlan): The target VLAN object to copy the properties to.
        source_vlan_obj (Vlan): The source VLAN object to copy the properties from.

    Returns:
        None
    """
    target_vlan_obj.vlanid = source_vlan_obj.vlanid
    target_vlan_obj.name = source_vlan_obj.name
    target_vlan_obj.mtu = source_vlan_obj.mtu
    target_vlan_obj.enabled = source_vlan_obj.enabled
    target_vlan_obj.oper_status = source_vlan_obj.oper_status
    target_vlan_obj.autostate = source_vlan_obj.autostate
    target_vlan_obj.ip_address = source_vlan_obj.ip_address
    target_vlan_obj.sag_ip_address = source_vlan_obj.sag_ip_address
    target_vlan_obj.description = source_vlan_obj.description


def insert_vlan_in_db(device: Device, vlans_obj_vs_mem):
    """
    Inserts VLAN information into the database.

    Args:
        device (Device): The device object representing the device.
        vlans_obj_vs_mem (dict): A dictionary containing VLAN objects as keys
        and a list of members as values.

    Returns:
        None
    """
    for vlan, members in vlans_obj_vs_mem.items() or []:
        if v := get_vlan_obj_from_db(device.mgt_ip, vlan.name):
            # update existing vlan if already exists.
            copy_vlan_obj_prop(v, vlan)
            v.save()
            device.vlans.connect(v)
        else:
            # Create a new vlan in database.
            vlan.save()
            device.vlans.connect(vlan)

        saved_vlan = get_vlan_obj_from_db(device.mgt_ip, vlan.name)
        
        ## For updating vlan members in db, lets first disconnect any existing members and recreate membership in DB.
        ## It will cater case when vlan has members are in db but not on device.
        ## Also the case when members has been changed/updated.
        saved_vlan.memberInterfaces.disconnect_all()
        saved_vlan.memberPortChannel.disconnect_all()
        for mem in members or []:
            if "ethernet" in mem.get("ifname").lower():
                intf = get_interface_of_device_from_db(
                            device.mgt_ip, mem.get("ifname")
                        )
                if saved_vlan and intf:
                    mem_rel = saved_vlan.memberInterfaces.connect(intf)
                    mem_rel.tagging_mode = mem.get("tagging_mode")
                    mem_rel.save()
            else:
                ## Its a port channel.
                intf = get_port_chnl_of_device_from_db(
                            device.mgt_ip, mem.get("ifname")
                        )
                if saved_vlan and intf:
                    mem_rel = saved_vlan.memberPortChannel.connect(intf)
                    mem_rel.tagging_mode = mem.get("tagging_mode")
                    mem_rel.save()
    ## Handle the case when some or all vlans has been deleted from device but remained in DB
    ## Remove all vlans which are in DB but not on device.
    for vlan_in_db in get_vlan_obj_from_db(device.mgt_ip) or []:
        if vlan_in_db not in vlans_obj_vs_mem:
            del_vlan_from_db(device.mgt_ip, vlan_in_db.name)


def get_vlan_obj_from_db_using_id(device_ip, vlan_id: int = None):
    """
    Get the VLAN object from the database.

    Parameters:
        device_ip (str): The IP address of the device.
        vlan_id (int, optional): The ID of the VLAN. Defaults to None.

    Returns:
        The VLAN object from the database if `vlan_name` is None, otherwise the VLAN object with the specified name.
    """
    device: Device = get_device_db_obj(device_ip)
    return (
        (device.vlans.all()
        if not vlan_id
        else device.vlans.get_or_none(vlanid=vlan_id)) if device else None
    )