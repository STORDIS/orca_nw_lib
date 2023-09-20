from typing import List

from .utils import get_logging
from .device_db import get_device_db_obj
from .interface_db import get_sub_interface_from_db
from .graph_db_models import BGP, BGP_GLOBAL_AF, Device

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
    target_obj.neighbor_prop = src_obj.neighbor_prop


def copy_bgp_global_af_object_prop(target_obj: BGP_GLOBAL_AF, src_obj: BGP_GLOBAL_AF):
    """
    Copy the properties of the source BGP_GLOBAL_AF object to the target BGP_GLOBAL_AF object.

    Args:
        target_obj (BGP_GLOBAL_AF): The target BGP_GLOBAL_AF object to copy the properties to.
        src_obj (BGP_GLOBAL_AF): The source BGP_GLOBAL_AF object to copy the properties from.

    Returns:
        None
    """
    target_obj.afi_safi = src_obj.afi_safi
    target_obj.vrf_name = src_obj.vrf_name


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
        for device in get_device_db_obj()
        for b in device.bgp.all()
        if b.local_asn == asn
    ]


def get_bgp_global_af_list_from_db(device_ip: str) -> List[BGP_GLOBAL_AF]:
    """
    Retrieves a list of BGP_GLOBAL_AF objects from the database for a specific device.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        List[BGP_GLOBAL_AF] or None: A list of BGP_GLOBAL_AF objects if the device exists in the database,
        otherwise None.
    """
    device = get_device_db_obj(device_ip)
    return device.bgp_global_af.all() if device else None


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
        elif not any(
            bgp.local_asn == bgp_global.local_asn for bgp_global in bgp_global_list
        ):
            bgp.delete()


def insert_bgp_global_af_list_in_db(
    device: Device, bgp_global_af_list: List[BGP_GLOBAL_AF]
):
    """
    Insert a list of BGP Global AF objects into the database for a given device.

    Args:
        device (Device): The device object representing the device where the BGP Global AF objects will be inserted.
        bgp_global_af_list (List[BGP_GLOBAL_AF]): The list of BGP Global AF objects to be inserted.

    Returns:
        None

    Raises:
        None
    """
    for bgp_global_af in bgp_global_af_list:
        if af_list := get_bgp_global_af_list_from_db(device.mgt_ip):
            for af in af_list:
                if af.vrf_name == bgp_global_af.vrf_name:
                    copy_bgp_global_af_object_prop(af, bgp_global_af)
                    af.save()
                    device.bgp_global_af.connect(af)
        else:
            bgp_global_af.save()
            device.bgp_global_af.connect(bgp_global_af)

    ## Handle BGP Global deletion - remove bgp global af nodes from DB which are not present in device.
    for bgp_global_af in device.bgp_global_af.all():
        if not bgp_global_af_list:
            bgp_global_af.delete()
        elif not any(
            bgp_global_af.afi_safi == af.afi_safi for af in bgp_global_af_list
        ):
            bgp_global_af.delete()


def connect_bgp_neighbours_and_asn():
    """
    Connects BGP peers by iterating through each device from the database and
    for each device, iterates through its BGP configurations. For each BGP
    configuration, it connects to the subinterface specified by the neighbor
    IP address if it exists. Then, it connects to all BGP configurations from
    the database that have a matching remote AS number.

    Returns:
        None
    """
    for device in get_device_db_obj():
        for bgp in device.bgp.all() or []:
            ## In case neighbours has been deleted on the device,
            ## To update the DB relationship is to disconnect_all(),
            ## And then to connect again.
            bgp.neighbor.disconnect_all()
            bgp.remote_asn_node.disconnect_all()

            for prop in bgp.neighbor_prop or []:
                neighbor_rel = (
                    bgp.neighbor.connect(si)
                    if (si := get_sub_interface_from_db(prop.get("neighbor")))
                    else None
                )
                if neighbor_rel:
                    neighbor_rel.vrf_name = prop.get("vrf_name")
                    neighbor_rel.afi_safi = prop.get("afi_safi")
                    neighbor_rel.save()

                for rem_bgp in get_bgp_from_db(prop.get("asn")):
                    bgp.remote_asn_node.connect(rem_bgp)


def get_bgp_global_with_vrf_from_db(device_ip, vrf_name: str = None):
    """
    Retrieve the BGP global list of a device from the database.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        List[BGP]: A list of BGP global configurations for the device. If the device is not found, returns None.
    """
    device = get_device_db_obj(device_ip)
    if vrf_name:
        return device.bgp.get_or_none(vrf_name=vrf_name) if device else None
    return device.bgp.all() if device else None


def get_bgp_global_with_asn_from_db(device_ip, asn: str = None):
    """
    Get the BGP global configuration for a device based on its IP address and optional ASN.

    Parameters:
        device_ip (str): The IP address of the device.
        asn (str, optional): The ASN (Autonomous System Number) to filter the BGP global configuration. Default is None.

    Returns:
        - If `asn` is provided, returns the BGP global configuration for the device with the specified ASN. Returns None if the device doesn't exist.
        - If `asn` is not provided, returns all BGP global configurations for the device. Returns None if the device doesn't exist.
    """
    device = get_device_db_obj(device_ip)
    if asn:
        return device.bgp.get_or_none(local_asn=asn) if device else None
    return device.bgp.all() if device else None


def get_bgp_neighbor_subinterfaces_from_db(device_ip, asn: str):
    """
    Get the BGP neighbor subinterfaces from the database.

    Args:
        device_ip (str): The IP address of the device.
        asn (str): The ASN (Autonomous System Number) of the BGP.

    Returns:
        list: A list of BGP neighbor subinterfaces if found, None otherwise.
    """
    device = get_device_db_obj(device_ip)
    bgp = device.bgp.get_or_none(local_asn=asn) if device else None
    return bgp.neighbor.all() if bgp else None


def get_remote_bgp_asn_from_db(device_ip, asn: str):
    """
    Get the remote BGP ASN nodes from the database for a given device IP and ASN.

    Parameters:
        device_ip (str): The IP address of the device.
        asn (str): The local ASN of the BGP.

    Returns:
        list or None: A list of remote BGP ASN nodes if found, None otherwise.
    """
    device = get_device_db_obj(device_ip)
    bgp = device.bgp.get_or_none(local_asn=asn) if device else None
    return bgp.remote_asn_node.all() if bgp else None


def create_bgp_peer_link_rel():
    """
    Generates the BGP peer link relation.

    This function is responsible for discovering the BGP neighbor relations. It calls the 'connect_bgp_neighbours_and_asn()' function to connect the BGP neighbors and retrieve their Autonomous System Number (ASN).

    Parameters:
        None

    Returns:
        None
    """
    _logger.info("Discovering BGP neighbor relations.")
    connect_bgp_neighbours_and_asn()
