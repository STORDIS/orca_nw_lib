from typing import List

from .utils import get_logging
from .device_db import get_device_db_obj
from .interface_db import get_sub_interface_from_db
from .graph_db_models import (
    BGP,
    BGP_GLOBAL_AF,
    Device,
    BGP_GLOBAL_AF_NETWORK,
    BGP_GLOBAL_AF_AGGREGATE_ADDR,
    BGP_NEIGHBOR,
    BGP_NEIGHBOR_AF
)

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


def get_bgp_global_af_list_from_db(device_ip: str, asn: int) -> List[BGP_GLOBAL_AF]:
    """
    Retrieves a list of BGP_GLOBAL_AF objects from the database for a specific device.

    Args:
        device_ip (str): The IP address of the device.
        asn (int): The AS number of the BGP_GLOBAL_AF objects to retrieve.

    Returns:
        List[BGP_GLOBAL_AF] or None: A list of BGP_GLOBAL_AF objects if the device exists in the database,
        otherwise None.
    """
    bgp = get_bgp_global_with_asn_from_db(device_ip, asn)
    return bgp.af.all() if bgp else None


def insert_device_bgp_in_db(device: Device, bgp_global_list: dict):
    """
    Inserts the given list of BGP objects into the database for the specified device.

    Args:
        device (Device): The device object to insert the BGP objects for.
        bgp_global_list (dict): BGP objects to be inserted into the database.

    Returns:
        None
    """
    for bgp, family in bgp_global_list.items():
        if b := get_bgp_global_with_asn_from_db(device.mgt_ip, bgp.local_asn):
            copy_bgp_object_prop(b, bgp)
            b.save()
            device.bgp.connect(b)
        else:
            bgp.save()
            device.bgp.connect(bgp)

        saved_bgp = get_bgp_global_with_asn_from_db(device.mgt_ip, bgp.local_asn)

        # saving bgp global af
        saved_bgp.af.disconnect_all()
        for af in saved_bgp.af.all():
            af.delete()
        af_list = family.get("af")
        for af in af_list:
            af.save()
            saved_bgp.af.connect(af) if saved_bgp else None

        # saving bgp global network
        saved_bgp.af_network.disconnect_all()
        for af_network in saved_bgp.af_network.all():
            af_network.delete()
        af_network_list = family.get("af_network")
        for af_network in af_network_list:
            af_network.save()
            saved_bgp.af_network.connect(af_network) if saved_bgp else None

        # saving bgp global aggregate addr
        saved_bgp.af_aggregate_addr.disconnect_all()
        for af_aggregate_addr in saved_bgp.af_aggregate_addr.all():
            af_aggregate_addr.delete()
        af_aggregate_addr_list = family.get("af_aggregate_addr")
        for af_aggregate_addr in af_aggregate_addr_list:
            af_aggregate_addr.save()
            saved_bgp.af_aggregate_addr.connect(af_aggregate_addr) if saved_bgp else None

    ## Handle BGP Global deletion - remove bgp nodes from DB which are not present in device.
    for bgp in device.bgp.all():
        if not bgp_global_list:
            bgp.delete()
        elif not any(
                bgp.local_asn == bgp_global.local_asn for bgp_global in bgp_global_list
        ):
            bgp.delete()


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


def get_bgp_global_with_asn_from_db(device_ip, asn: int = None):
    """
    Get the BGP global configuration for a device based on its IP address and optional ASN.

    Parameters:
        device_ip (str): The IP address of the device.
        asn (int, optional): The ASN (Autonomous System Number) to filter the BGP global configuration. Default is None.

    Returns:
        - If `asn` is provided, returns the BGP global configuration for the device with the specified ASN. Returns None if the device doesn't exist.
        - If `asn` is not provided, returns all BGP global configurations for the device. Returns None if the device doesn't exist.
    """
    device = get_device_db_obj(device_ip)
    if asn:
        return device.bgp.get_or_none(local_asn=asn) if device else None
    return device.bgp.all() if device else None


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


def get_bgp_global_af_from_db(device_ip: str, asn: int, afi_safi: str = None) -> list[BGP_GLOBAL_AF] | BGP_GLOBAL_AF:
    """
    Retrieves the BGP global address family configuration from the database for a given device IP, ASN, and AFI/SAFI.

    Args:
        device_ip (str): The IP address of the device.
        asn (int): The Autonomous System Number (ASN) of the BGP.
        afi_safi (str, optional): The address family identifier (AFI) and sub-address family identifier (SAFI)
            combination. Defaults to None.

    Returns:
        list[BGP_GLOBAL_AF] | BGP_GLOBAL_AF: A list of BGP_GLOBAL_AF objects if afi_safi is provided and found,
        a single BGP_GLOBAL_AF object if afi_safi is provided and not found, or None if afi_safi is not provided
        and no BGP_GLOBAL_AF objects are found.
    """
    bgp = get_bgp_global_with_asn_from_db(device_ip, asn)
    if afi_safi:
        return bgp.af.get_or_none(afi_safi=afi_safi) if bgp else None
    return bgp.af.all() if bgp else None


def get_bgp_global_af_network_from_db(
        device_ip: str, asn: int, afi_safi: str = None
) -> list[BGP_GLOBAL_AF_NETWORK] | BGP_GLOBAL_AF_NETWORK:
    """
    Retrieves the BGP global address family network configuration from the database for a given device IP, ASN, and AFI/SAFI.

    Args:
        device_ip (str): The IP address of the device.
        asn (int): The Autonomous System Number (ASN) of the BGP.
        afi_safi (str, optional): The address family identifier (AFI) and sub-address family identifier (SAFI)
            combination. Defaults to None.
    """
    bgp = get_bgp_global_with_asn_from_db(device_ip, asn)
    if afi_safi:
        return bgp.af_network.get_or_none(afi_safi=afi_safi) if bgp else None
    return bgp.af_network.all() if bgp else None


def get_bgp_global_af_aggregate_addr_from_db(
        device_ip: str, asn: int, afi_safi: str = None
) -> list[BGP_GLOBAL_AF_AGGREGATE_ADDR] | BGP_GLOBAL_AF_AGGREGATE_ADDR:
    """
    Retrieves the BGP global address family aggregate address configuration from the database for a given device IP, ASN, and AFI/SAFI.

    Args:
        device_ip (str): The IP address of the device.
        asn (int): The Autonomous System Number (ASN) of the BGP.
        afi_safi (str, optional): The address family identifier (AFI) and sub-address family identifier (SAFI)
            combination. Defaults to None.
    """
    bgp = get_bgp_global_with_asn_from_db(device_ip, asn)
    if afi_safi:
        return bgp.af_aggregate_addr.get_or_none(afi_safi=afi_safi) if bgp else None
    return bgp.af_aggregate_addr.all() if bgp else None


def copy_bgp_neighbor_object_prop(src_obj: BGP_NEIGHBOR, target_obj: BGP_NEIGHBOR):
    """
    Copies the properties of a source BGP_NEIGHBOR object to a target BGP_NEIGHBOR object.

    Parameters:
        target_obj (BGP_NEIGHBOR): The target BGP_NEIGHBOR object to copy the properties to.
        src_obj (BGP_NEIGHBOR): The source BGP_NEIGHBOR object to copy the properties from.

    Returns:
        None
    """
    target_obj.local_asn = src_obj.local_asn
    target_obj.vrf_name = src_obj.vrf_name
    target_obj.neighbor_ip = src_obj.neighbor_ip
    target_obj.remote_asn = src_obj.remote_asn


def insert_device_bgp_neighbors_in_db(device: Device, bgp_neighbor_list: dict):
    """
    Inserts the BGP neighbors in the database.

    Args:
        device (Device): The device object.
        bgp_neighbor_list (dict): A list of BGP_NEIGHBOR objects.

    Returns:
        None
    """
    for bgp_neighbor, family in bgp_neighbor_list.items():
        if bgp_neighbor_from_db := get_bgp_neighbor_from_db(
                device_ip=device.mgt_ip, neighbor_ip=bgp_neighbor.neighbor_ip
        ):
            copy_bgp_neighbor_object_prop(bgp_neighbor_from_db, bgp_neighbor)
            bgp_neighbor_from_db.save()
            device.bgp_neighbor.connect(bgp_neighbor_from_db)
        else:
            bgp_neighbor.save()
            device.bgp_neighbor.connect(bgp_neighbor)

        saved_bgp_neighbor = get_bgp_neighbor_from_db(device.mgt_ip, bgp_neighbor.neighbor_ip)
        for af in saved_bgp_neighbor.af.all():
            af.delete()
        nbr_af_list = family.get("neighbor_af")
        for af in nbr_af_list:
            af.save()
            saved_bgp_neighbor.af.connect(af) if saved_bgp_neighbor else None

    saved_bgp_neighbors = get_bgp_neighbor_from_db(device.mgt_ip)
    for i in saved_bgp_neighbors:
        if i.neighbor_ip:
            neighbor_sub = get_sub_interface_from_db(i.neighbor_ip)
            i.neighbor_rel.disconnect_all()
            if neighbor_sub:
                i.neighbor_rel.connect(neighbor_sub)

    for i in saved_bgp_neighbors:
        if i not in bgp_neighbor_list:
            i.delete()


def get_bgp_neighbor_from_db(device_ip: str, neighbor_ip: str = None) -> BGP_NEIGHBOR | list[BGP_NEIGHBOR]:
    """
    Get the BGP neighbor from the database.

    Args:
        device_ip (str): The IP address of the device.
        neighbor_ip (str, optional): The IP address of the neighbor. Defaults to None.

    Returns:
        BGP_NEIGHBOR: The BGP neighbor if found, None otherwise.
    """
    device = get_device_db_obj(device_ip)
    if neighbor_ip:
        return device.bgp_neighbor.get_or_none(neighbor_ip=neighbor_ip) if device else None
    return device.bgp_neighbor.all() if device_ip else None


def get_bgp_neighbor_af_from_db(device_ip: str, neighbor_ip: str, afi_safi: str = None) -> list[BGP_NEIGHBOR_AF] | BGP_NEIGHBOR_AF:
    """
    Get the BGP neighbor address family from the database.

    Args:
        device_ip (str): The IP address of the device.
        neighbor_ip (str): The IP address of the neighbor.
        afi_safi (str, optional): The address family identifier (AFI) and sub-address family identifier (SAFI)
            combination. Defaults to None.

    Returns:
        list: A list of BGP neighbor address families if found, None otherwise.
    """
    bgp_neighbor = get_bgp_neighbor_from_db(device_ip, neighbor_ip)
    if afi_safi:
        return bgp_neighbor.af.get_or_none(afi_safi=afi_safi) if bgp_neighbor else None
    return bgp_neighbor.af.all() if bgp_neighbor else None


def get_bgp_neighbor_subinterfaces_from_db(device_ip, neighbor_ip: str):
    """
    Get the BGP neighbor subinterfaces from the database.

    Args:
        device_ip (str): The IP address of the device.
        neighbor_ip (str): The IP address of the neighbor.
    """
    bgp_nbr = get_bgp_neighbor_from_db(device_ip, neighbor_ip)
    return bgp_nbr.neighbor_rel.all() if bgp_nbr else None


def get_bgp_neighbor_local_bgp_from_db(device_ip, neighbor_ip: str, asn: int = None):
    """
    Get the BGP neighbor BGP global from the database.

    Args:
        device_ip (str): The IP address of the device.
        neighbor_ip (str): The IP address of the neighbor.
        asn (int, optional): The ASN of the BGP. Defaults to None.
    """
    bgp_nbr = get_bgp_neighbor_from_db(device_ip, neighbor_ip)
    if asn:
        return bgp_nbr.local_asn_rel.get_or_none(local_asn=asn) if bgp_nbr else None
    return bgp_nbr.local_asn_rel.all() if bgp_nbr else None


def get_bgp_neighbor_remote_bgp_from_db(device_ip, neighbor_ip: str, asn: int = None):
    """
    Get the BGP neighbor BGP global from the database.

    Args:
        device_ip (str): The IP address of the device.
        neighbor_ip (str): The IP address of the neighbor.
        asn (int, optional): The ASN of the BGP. Defaults to None.
    """
    bgp_nbr = get_bgp_neighbor_from_db(device_ip, neighbor_ip)
    if asn:
        return bgp_nbr.remote_asn_rel.get_or_none(local_asn=asn) if bgp_nbr else None
    return bgp_nbr.remote_asn_rel.all() if bgp_nbr else None


def connect_bgp_neighbor_to_bgp_global():
    devices = get_device_db_obj()
    bgp_neighbors = []
    bgp_globals = []
    for device in devices:
        for bgp_neighbor in device.bgp_neighbor.all():
            bgp_neighbors.append(bgp_neighbor)
        for bgp_global in device.bgp.all():
            bgp_globals.append(bgp_global)
    for bgp_neighbor in bgp_neighbors:
        bgp_neighbor.local_asn_rel.disconnect_all()
        bgp_neighbor.remote_asn_rel.disconnect_all()
        for bgp_global in bgp_globals:
            if bgp_global.local_asn == bgp_neighbor.remote_asn:
                bgp_neighbor.remote_asn_rel.connect(bgp_global)
            if bgp_global.local_asn == bgp_neighbor.local_asn:
                bgp_neighbor.local_asn_rel.connect(bgp_global)
