from ast import Dict
from typing import List
from .bgp_db import (
    create_bgp_peer_link_rel,
    get_bgp_global_with_vrf_from_db,
    get_bgp_neighbor_from_db,
    insert_device_bgp_in_db,
)
from .bgp_gnmi import (
    config_bgp_global_on_device,
    config_bgp_neighbors_on_device,
    del_all_bgp_neighbors_from_device,
    del_bgp_global_from_device,
    get_bgp_global_list_from_device,
    get_bgp_neighbor_from_device,
)
from .device import get_device_from_db

from .graph_db_models import BGP
from .utils import get_logging

_logger = get_logging().getLogger(__name__)


def create_bgp_graph_objects(device_ip: str) -> List[BGP]:
    """
    Creates BGP graph objects based on the given device IP.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        List[BGP]: A list of BGP graph objects created based on the device's BGP configuration.
    """

    global_list = get_bgp_global_list_from_device(device_ip)
    bgp_global_list = []

    for bgp_config in global_list.get("sonic-bgp-global:BGP_GLOBALS_LIST") or []:
        bgp = BGP(
            local_asn=bgp_config.get("local_asn"),
            router_id=bgp_config.get("router_id"),
            vrf_name=bgp_config.get("vrf_name"),
        )

        remote_asn_list = []
        nbr_ips = []
        nbr_list = get_bgp_neighbor_from_device(device_ip)

        for nbr in nbr_list.get("sonic-bgp-neighbor:BGP_NEIGHBOR_LIST") or []:
            if bgp.vrf_name == nbr.get("vrf_name"):
                remote_asn_list.append(nbr.get("asn"))
                nbr_ips.append(nbr.get("neighbor"))

        bgp.remote_asn = remote_asn_list
        bgp.nbr_ips = nbr_ips
        bgp_global_list.append(bgp)

    return bgp_global_list


def get_bgp_global(device_ip, vrf_name: str = None):
    """
    Retrieves the BGP global configuration for a given device IP and VRF name.

    Args:
        device_ip (str): The IP address of the device.
        vrf_name (str, optional): The name of the VRF. Defaults to None.

    Returns:
        List[Dict[str, str]]: A list of dictionaries representing the BGP global configuration.
            Each dictionary contains the properties of a BGP global configuration.

    Raises:
        None

    """
    op_dict: List[Dict[str, str]] = []
    bgp_global = get_bgp_global_with_vrf_from_db(device_ip, vrf_name)

    if not bgp_global:
        return None

    try:
        for bgp in bgp_global:
            op_dict.append(bgp.__properties__)
    except TypeError:
        op_dict.append(bgp_global.__properties__)
    return op_dict


def config_bgp_global(
    device_ip: str, local_asn: int, router_id: str, vrf_name: str = "default"
) -> None:
    """
    Configures the BGP global settings on the specified device,
    and rediscovers the BGP global configuration.

    Note:
        This function does not check if the BGP global configuration already exists.
        If the BGP global configuration already exists, this function will overwrite it.

    Args:
        device_ip (str): The IP address of the device.
        local_asn (int): The local autonomous system number.
        router_id (str): The router ID.
        vrf_name (str, optional): The name of the VRF (Virtual Routing and Forwarding) instance. Defaults to "default".

    Returns:
        None: This function does not return anything.
    """
    config_bgp_global_on_device(device_ip, local_asn, router_id, vrf_name)
    discover_bgp()


def del_bgp_global(device_ip: str, vrf_name: str) -> None:
    del_bgp_global_from_device(device_ip, vrf_name)
    discover_bgp()


def get_bgp_neighbors(device_ip: str, asn: int) -> List[dict]:
    op_dict: List[dict] = []
    nbrs = get_bgp_neighbor_from_db(device_ip, asn)

    if not nbrs:
        return op_dict

    for nbr in nbrs:
        op_dict.append(nbr.__properties__)
    return op_dict


def config_bgp_neighbors(
    device_ip: str, remote_asn: int, neighbor_ip: str, remote_vrf: str
):
    config_bgp_neighbors_on_device(device_ip, remote_asn, neighbor_ip, remote_vrf)
    discover_bgp()


def del_all_bgp_neighbors(device_ip: str):
    del_all_bgp_neighbors_from_device(device_ip)
    discover_bgp()


def discover_bgp():
    """
    Discovers the BGP Global List.
    Retrieves the list of devices from the database and for each device,
    discovers BGP and inserts the BGP information into the database.
    Lastly, creates the BGP peer link relationships.

    Parameters:
    None

    Returns:
    None
    """
    _logger.info("Discovering BGP Global List.")
    for device in get_device_from_db():
        _logger.info(f"Discovering BGP on device {device}.")
        insert_device_bgp_in_db(device, create_bgp_graph_objects(device.mgt_ip))
    create_bgp_peer_link_rel()
