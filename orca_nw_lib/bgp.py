from typing import List
from .bgp_db import (
    create_bgp_peer_link_rel,
    get_bgp_global_af_list_from_db,
    get_bgp_global_with_vrf_from_db,
    get_remote_bgp_asn_from_db,
    get_bgp_neighbor_subinterfaces_from_db,
    insert_bgp_global_af_list_in_db,
    insert_device_bgp_in_db,
)
from .bgp_gnmi import (
    config_bgp_global_af_on_device,
    config_bgp_global_on_device,
    config_bgp_neighbor_af_on_device,
    config_bgp_neighbors_on_device,
    del_all_bgp_global_af_from_device,
    del_all_bgp_neighbors_from_device,
    del_all_neighbor_af_from_device,
    del_bgp_global_from_device,
    get_bgp_global_af_list_from_device,
    get_bgp_global_list_from_device,
    get_bgp_neighbors_from_device,
)
from .device_db import get_device_db_obj

from .graph_db_models import BGP, BGP_GLOBAL_AF
from .utils import get_logging

_logger = get_logging().getLogger(__name__)


def _create_bgp_graph_objects(device_ip: str) -> List[BGP]:
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
        bgp_global_list.append(bgp)

    bgp_nbrs = get_bgp_neighbors_from_device(device_ip).get(
        "sonic-bgp-neighbor:sonic-bgp-neighbor", {}
    )
    bgp_nbr_list = bgp_nbrs.get("BGP_NEIGHBOR", {}).get("BGP_NEIGHBOR_LIST", [])
    bgp_nbr_af_list = bgp_nbrs.get("BGP_NEIGHBOR_AF", {}).get(
        "BGP_NEIGHBOR_AF_LIST", []
    )

    for nbr in bgp_nbr_list:
        afi_safi = []
        for af in bgp_nbr_af_list:
            if nbr.get("neighbor") == af.get("neighbor"):
                afi_safi.append({af.get("afi_safi"): af.get("admin_status")})
        nbr["afi_safi"] = afi_safi

    for bgp in bgp_global_list:
        nbr_details_list = []
        for nbr in bgp_nbr_list:
            if nbr.get("vrf_name") == bgp.vrf_name:
                nbr_details_list.append(nbr)
        bgp.neighbor_prop = nbr_details_list
    return bgp_global_list


def _create_bgp_global_af_graph_objects(device_ip: str) -> List[BGP_GLOBAL_AF]:
    global_af_list = get_bgp_global_af_list_from_device(device_ip).get(
        "sonic-bgp-global:BGP_GLOBALS_AF_LIST"
    )

    return [
        BGP_GLOBAL_AF(
            afi_safi=global_af.get("afi_safi"), vrf_name=global_af.get("vrf_name")
        )
        for global_af in global_af_list or []
    ]


def get_bgp_global(device_ip, vrf_name: str = None):
    """
    Retrieves the BGP global configuration for a given device IP and VRF name.

    Args:
        device_ip (str): The IP address of the device.
        vrf_name (str, optional): The name of the VRF. Defaults to None.

    Returns:
        list or dict: If `vrf_name` is provided, returns the BGP global configuration
        as a dictionary if it exists in the database, otherwise returns `None`.
        If `vrf_name` is not provided, returns a list of dictionaries, each
        representing the BGP global configuration for a VRF associated with the
        device.
    """

    if vrf_name:
        return (
            bgp_global.__properties__
            if (bgp_global := get_bgp_global_with_vrf_from_db(device_ip, vrf_name))
            else None
        )
    return [
        bgp_global.__properties__
        for bgp_global in get_bgp_global_with_vrf_from_db(device_ip)
    ]


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
    try:
        config_bgp_global_on_device(device_ip, local_asn, router_id, vrf_name)
    except Exception as e:
        _logger.error(
            f"Failed to configure BGP with ASN {local_asn} on device {device_ip}, Reason: {e}."
        )
        raise
    finally:
        discover_bgp()


def del_bgp_global(device_ip: str, vrf_name: str) -> None:
    """
    Delete BGP global configuration for the specified device IP and VRF.

    Args:
        device_ip (str): The IP address of the device.
        vrf_name (str): The name of the VRF.

    Returns:
        None: This function does not return anything.

    Notes:
        This function first attempts to delete the BGP global configuration for the specified device IP and VRF.
        If an error occurs, it logs the error message and re-raises the exception.
        Finally, it calls the `discover_bgp` function to ensure the BGP configuration is updated.

    """
    try:
        del_bgp_global_from_device(device_ip, vrf_name)
    except Exception as e:
        _logger.error(
            f"Failed to delete BGP with VRF {vrf_name} on device {device_ip}, Reason: {e}."
        )
        raise
    finally:
        discover_bgp()


def get_bgp_neighbors_subinterfaces(device_ip: str, asn: int) -> List[dict]:
    """
    Retrieves the BGP neighbors' subinterfaces from the database for a given device IP and ASN.

    Args:
        device_ip (str): The IP address of the device.
        asn (int): The Autonomous System Number (ASN).

    Returns:
        List[dict]: A list of dictionaries representing the BGP neighbors' subinterfaces. Each dictionary contains the properties of a subinterface.
    """
    op_dict: List[dict] = []
    nbrs = get_bgp_neighbor_subinterfaces_from_db(device_ip, asn)

    if not nbrs:
        return op_dict

    for nbr in nbrs:
        op_dict.append(nbr.__properties__)
    return op_dict


def get_neighbour_bgp(device_ip: str, asn: int) -> List[dict]:
    """
    Retrieves the neighbor BGP information for a given device IP and ASN.

    Args:
        device_ip (str): The IP address of the device.
        asn (int): The Autonomous System Number.

    Returns:
        List[dict]: A list of dictionaries containing the neighbor BGP information.

    Raises:
        None.
    """
    op_dict: List[dict] = []
    nbrs = get_remote_bgp_asn_from_db(device_ip, asn)

    if not nbrs:
        return op_dict

    for nbr in nbrs:
        op_dict.append(nbr.__properties__)
    return op_dict


def config_bgp_neighbors(
    device_ip: str, remote_asn: int, neighbor_ip: str, remote_vrf: str
):
    """
    Configures BGP neighbors on a device.

    Args:
        device_ip (str): The IP address of the device.
        remote_asn (int): The remote AS number.
        neighbor_ip (str): The IP address of the BGP neighbor.
        remote_vrf (str): The remote VRF name.

    Returns:
        None
    """
    try:
        config_bgp_neighbors_on_device(device_ip, remote_asn, neighbor_ip, remote_vrf)
    except Exception as e:
        _logger.error(
            f"Failed to configure BGP neighbor {neighbor_ip} with ASN {remote_asn} on device {device_ip}, Reason: {e}."
        )
        raise
    finally:
        discover_bgp()


def del_all_bgp_neighbors(device_ip: str):
    """
    Deletes all BGP neighbors from the specified device.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        None
    """
    try:
        del_all_bgp_neighbors_from_device(device_ip)
    except Exception as e:
        _logger.error(
            f"Failed to delete BGP neighbors on device {device_ip}, Reason: {e}."
        )
        raise
    finally:
        discover_bgp()


def discover_bgp(device_ip: str = None):
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
    devices = [get_device_db_obj(device_ip)] if device_ip else get_device_db_obj()
    for device in devices:
        try:
            _logger.info(f"Discovering BGP on device {device}.")
            insert_device_bgp_in_db(device, _create_bgp_graph_objects(device.mgt_ip))
        except Exception as e:
            _logger.error(
                f"BGP Discovery Failed on device {device.mgt_ip}, Reason: {e}"
            )
            raise
    create_bgp_peer_link_rel()


def discover_bgp_af_global(device_ip: str = None):
    """
    Discovers the BGP Global AF List.
    Retrieves the list of devices from the database and for each device,
    discovers BGP and inserts the BGP information into the database.
    Lastly, creates the BGP peer link relationships.

    Parameters:
    None

    Returns:
    None
    """

    _logger.info("Discovering BGP Global AF List.")
    devices = [get_device_db_obj(device_ip)] if device_ip else get_device_db_obj()
    for device in devices:
        try:
            _logger.info(f"Discovering BGP Global AF List on device {device.mgt_ip}.")
            insert_bgp_global_af_list_in_db(
                device, _create_bgp_global_af_graph_objects(device.mgt_ip)
            )
        except Exception as e:
            _logger.error(
                f"BGP Global AF List Discovery Failed on device {device.mgt_ip}, Reason: {e}"
            )
            raise


def config_bgp_neighbor_af(
    device_ip: str,
    afi_safi: str,
    neighbor_ip: str,
    vrf: str,
    admin_status: bool = True,
):
    """
    Configure BGP neighbor address family.

    Args:
        device_ip (str): The IP address of the device.
        afi_safi (str): The address family identifier.
        neighbor_ip (str): The IP address of the BGP neighbor.
        vrf (str): The VRF (Virtual Routing and Forwarding) instance.
        admin_status (bool, optional): The administrative status of the neighbor.
            Defaults to True.

    Returns:
        None
    """

    try:
        config_bgp_neighbor_af_on_device(
            device_ip, afi_safi, neighbor_ip, vrf, admin_status
        )
    except Exception as e:
        _logger.error(
            f"Failed to configure AF {afi_safi} on BGP neighbor {neighbor_ip}, Reason: {e}."
        )
        raise
    finally:
        discover_bgp()


def del_all_bgp_neighbour_af(device_ip: str):
    """
    Deletes all BGP neighbor AF from the specified device.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        None
    """
    try:
        del_all_neighbor_af_from_device(device_ip)
    except Exception as e:
        _logger.error(
            f"Failed to delete AF from BGP neighbor of device {device_ip}, Reason: {e}."
        )
        raise
    finally:
        discover_bgp()


def get_bgp_global_af_list(device_ip: str) -> List[dict]:
    """
    Retrieve a list of BGP global AF dictionaries for a given device IP.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        List[dict]: A list of dictionaries representing the BGP global AF properties.
    """
    return [
        global_af.__properties__
        for global_af in get_bgp_global_af_list_from_db(device_ip)
    ]


def config_bgp_global_af(device_ip: str, afi_safi: str, vrf_name: str = "default"):
    """
    Configures the BGP global address family (AF) on a device.

    Args:
        device_ip (str): The IP address of the device.
        afi_safi (str): The AF and SAFI (Address Family and Subsequent Address Family Identifier) to configure.
        vrf_name (str, optional): The name of the VRF (Virtual Routing and Forwarding) instance. Defaults to "default".

    Returns:
        None
    """
    try:
        config_bgp_global_af_on_device(device_ip, afi_safi, vrf_name)
    except Exception as e:
        _logger.error(
            f"Failed to configure AF {afi_safi} on BGP on device {device_ip}, Reason: {e}."
        )
        raise
    finally:
        discover_bgp_af_global()


def del_bgp_global_af_all(device_ip: str):
    """
    Deletes all BGP global AF from the specified device.

    Parameters:
        device_ip (str): The IP address of the device.

    Returns:
        None
    """
    try:
        del_all_bgp_global_af_from_device(device_ip)
    except Exception as e:
        _logger.error(
            f"Failed to delete AF from BGP on device {device_ip}, Reason: {e}."
        )
        raise
    finally:
        discover_bgp_af_global()
