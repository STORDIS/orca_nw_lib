from typing import List

from .utils import get_logging
from .device import get_device_from_db
from .interface_db import getSubInterfaceFromDB
from .graph_db_models import BGP, Device

_logger = get_logging().getLogger(__name__)

def copy_bgp_object_prop(target_obj: BGP, src_obj: BGP):
    """
    Copies the properties of a source BGP object to a target BGP object.

    Parameters:
        target_obj (BGP): The target BGP object to copy the properties to.
        src_obj (BGP): The source BGP object to copy the properties from.

    Returns:
        None
    """
    target_obj.local_asn = src_obj.local_asn
    target_obj.vrf_name = src_obj.vrf_name
    target_obj.router_id = src_obj.router_id
    target_obj.remote_asn = src_obj.remote_asn
    target_obj.nbr_ips = src_obj.nbr_ips


def get_bgp_from_db(asn: int) -> List[BGP]:
    """
    Retrieves a list of BGP objects from the database that have a matching local AS number.

    Parameters:
        asn (int): The AS number to match against the local AS number of the BGP objects.

    Returns:
        List[BGP]: A list of BGP objects that have a matching local AS number.
    """
    return [
        b
        for device in get_device_from_db()
        for b in device.bgp.all()
        if b.local_asn == asn
    ]


def insert_device_bgp_in_db(device: Device, bgp_global_list: List[BGP]):
    """
    Inserts the given list of BGP objects into the database for the specified device.

    Args:
        device (Device): The device object to insert the BGP objects for.
        bgp_global_list (List[BGP]): A list of BGP objects to be inserted into the database.

    Returns:
        None
    """
    for bgp in bgp_global_list:
        if b := get_bgp_from_db(bgp.local_asn):
            copy_bgp_object_prop(b[0], bgp)
            b[0].save()
            device.bgp.connect(b[0])
        else:
            bgp.save()
            device.bgp.connect(bgp)
            
    ## Handle BGP Global deletion - remove bgp nodes from DB which are not present in device.
    for bgp in device.bgp.all():
        if not bgp_global_list:
            bgp.delete()
        elif not any(bgp.local_asn == bgp_global.local_asn for bgp_global in bgp_global_list):
            bgp.delete()


def connect_bgp_peers():
    """
    Connects BGP peers by iterating through each device from the database and
    for each device, iterates through its BGP configurations. For each BGP
    configuration, it connects to the subinterface specified by the neighbor
    IP address if it exists. Then, it connects to all BGP configurations from
    the database that have a matching remote AS number.

    Returns:
        None
    """
    for device in get_device_from_db():
        for bgp in device.bgp.all() or []:
            ## In case neighbours has been deleted on the device,
            ## To update the DB relationship is to disconnect_all(),
            ## And then to connect again.
            bgp.neighbors.disconnect_all()
            bgp.remote_asn_node.disconnect_all()
            
            for nbr_ip in bgp.nbr_ips:
                bgp.neighbors.connect(si) if (
                    si := getSubInterfaceFromDB(nbr_ip)
                ) else None
            for remote_as in bgp.remote_asn:
                [
                    bgp.remote_asn_node.connect(rem_bgp)
                    for rem_bgp in get_bgp_from_db(remote_as)
                ]


def get_bgp_global_with_vrf_from_db(device_ip, vrf_name:str=None):
    """
    Retrieve the BGP global list of a device from the database.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        List[BGP]: A list of BGP global configurations for the device. If the device is not found, returns None.
    """
    device = get_device_from_db(device_ip)
    if vrf_name:
        return device.bgp.get_or_none(vrf_name=vrf_name) if device else None
    return device.bgp.all() if device else None


def get_bgp_global_with_asn_from_db(device_ip, asn:str=None):
    device = get_device_from_db(device_ip)
    if asn:
        return device.bgp.get_or_none(local_asn=asn) if device else None
    return device.bgp.all() if device else None


def get_bgp_neighbor_from_db(device_ip, asn:str):
    device = get_device_from_db(device_ip)
    bgp = device.bgp.get_or_none(local_asn=asn) if device else None
    return bgp.neighbors.all() if bgp else None


def create_bgp_peer_link_rel():
    _logger.info("Discovering BGP neighbor relations.")
    connect_bgp_peers()
