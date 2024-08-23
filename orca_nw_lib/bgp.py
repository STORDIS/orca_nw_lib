from typing import List
from .bgp_db import (
    create_bgp_peer_link_rel,
    get_bgp_global_af_list_from_db,
    get_bgp_global_with_vrf_from_db,
    get_remote_bgp_asn_from_db,
    get_bgp_neighbor_subinterfaces_from_db,
    insert_device_bgp_in_db,
    get_bgp_global_af_from_db, get_bgp_global_af_network_from_db, get_bgp_global_af_aggregate_addr_from_db,
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
    get_bgp_neighbors_from_device, del_bgp_global_af_from_device, config_bgp_global_af_network_on_device,
    get_bgp_global_af_network_from_device, del_bgp_global_af_network_on_device,
    config_bgp_global_af_aggregate_addr_on_device, del_bgp_global_af_aggregate_addr_on_device,
    get_bgp_global_af_aggregate_addr_from_device, get_bgp_details_from_device,
)
from .device_db import get_device_db_obj

from .graph_db_models import BGP, BGP_GLOBAL_AF, BGP_GLOBAL_AF_NETWORK, BGP_GLOBAL_AF_AGGREGATE_ADDR
from .utils import get_logging

_logger = get_logging().getLogger(__name__)


def _create_bgp_graph_objects(device_ip: str) -> dict:
    """
    Creates BGP graph objects based on the given device IP.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        List[BGP]: A list of BGP graph objects created based on the device's BGP configuration.
    """
    bgp_details = get_bgp_details_from_device(device_ip).get("sonic-bgp-global:sonic-bgp-global", {})

    global_list = bgp_details.get("BGP_GLOBALS", {})
    bgp_global_list = {}

    for bgp_config in global_list.get("BGP_GLOBALS_LIST") or []:

        # adding af
        global_af_list = bgp_details.get("BGP_GLOBALS_AF", {}).get("BGP_GLOBALS_AF_LIST", {})
        af_list = []
        bgp_family = {}
        for af in global_af_list:
            af_list.append(
                BGP_GLOBAL_AF(
                    afi_safi=af.get("afi_safi"),
                    vrf_name=af.get("vrf_name"),
                    max_ebgp_paths=int(af.get("max_ebgp_paths")) if af.get("max_ebgp_paths") else None,
                )
            )
        bgp_family["af"] = af_list

        # adding af network
        global_af_network_list = bgp_details.get("BGP_GLOBALS_AF_NETWORK", {}).get("BGP_GLOBALS_AF_NETWORK_LIST", {})
        af_network_list = []
        for af_network in global_af_network_list:
            af_network_list.append(
                BGP_GLOBAL_AF_NETWORK(
                    afi_safi=af_network.get("afi_safi"),
                    vrf_name=af_network.get("vrf_name"),
                    ip_prefix=af_network.get("ip_prefix")
                )
            )
        bgp_family["af_network"] = af_network_list

        # adding af aggregate address
        global_af_aggregate_addr_list = bgp_details.get("BGP_GLOBALS_AF_AGGREGATE_ADDR", {}).get(
            "BGP_GLOBALS_AF_AGGREGATE_ADDR_LIST", {}
        )
        af_aggregate_addr_list = []
        for af_aggregate_addr in global_af_aggregate_addr_list:
            af_aggregate_addr_list.append(
                BGP_GLOBAL_AF_AGGREGATE_ADDR(
                    afi_safi=af_aggregate_addr.get("afi_safi"),
                    vrf_name=af_aggregate_addr.get("vrf_name"),
                    ip_prefix=af_aggregate_addr.get("ip_prefix")
                )
            )
        bgp_family["af_aggregate_addr"] = af_aggregate_addr_list

        bgp_global_list[BGP(
            local_asn=bgp_config.get("local_asn"),
            router_id=bgp_config.get("router_id"),
            vrf_name=bgp_config.get("vrf_name"),
        )] = bgp_family

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


def config_bgp_global_af(device_ip: str, afi_safi: str, vrf_name: str = "default", max_ebgp_paths: int = None):
    """
    Configures the BGP global address family (AF) on a device.

    Args:
        device_ip (str): The IP address of the device.
        afi_safi (str): The AF and SAFI (Address Family and Subsequent Address Family Identifier) to configure.
        vrf_name (str, optional): The name of the VRF (Virtual Routing and Forwarding) instance. Defaults to "default".
        max_ebgp_paths (int, optional): The maximum number of EBGP paths. Defaults to None.

    Returns:
        None
    """
    try:
        config_bgp_global_af_on_device(device_ip, afi_safi, vrf_name, max_ebgp_paths)
    except Exception as e:
        _logger.error(
            f"Failed to configure AF {afi_safi} on BGP on device {device_ip}, Reason: {e}."
        )
        raise
    finally:
        discover_bgp(device_ip=device_ip)


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
        discover_bgp()


def del_bgp_global_af(device_ip: str, vrf_name: str, afi_safi: str = None):
    """
    Deletes all BGP global AF from all devices.

    Args:
        device_ip (str): The IP address of the device.
        vrf_name (str): The name of the VRF (Virtual Routing and Forwarding) instance.
        afi_safi (str, optional): The address family identifier. Defaults to None.
    Returns:
        None
    """
    try:
        del_bgp_global_af_from_device(device_ip, vrf_name, afi_safi)
    except Exception as e:
        _logger.error(
            f"Failed to delete AF from BGP on device {device_ip}, Reason: {e}."
        )
        raise
    finally:
        discover_bgp(device_ip=device_ip)


def get_bgp_global_af(device_ip, asn: int, afi_safi: str = None):
    """
    Retrieve a list of BGP global AF dictionaries for a given device IP.

    Args:
        device_ip (str): The IP address of the device.
        asn (int): The autonomous system number.
        afi_safi (str, optional): The address family identifier. Defaults to None.

    Returns:
        list or dict: A list of dictionaries representing the BGP global AF properties.
    """
    bgp_af = get_bgp_global_af_from_db(device_ip, asn, afi_safi)
    if isinstance(bgp_af, list):
        return [i.__properties__ for i in bgp_af] if bgp_af else None
    else:
        return bgp_af.__properties__ if bgp_af else None


def config_bgp_global_af_network(device_ip: str, afi_safi: str, ip_prefix: str, vrf_name: str = "default"):
    """
    Configures the BGP global address family (AF) network on a device.

    Args:
        device_ip (str): The IP address of the device.
        afi_safi (str): The AF and SAFI (Address Family and Subsequent Address Family Identifier) to configure.
        ip_prefix (str): The IP address and prefix length.
        vrf_name (str, optional): The name of the VRF (Virtual Routing and Forwarding) instance. Defaults to "default".

    Raises:
        Exception: If there is an error while configuring the AF network on the device.

    Returns:
        None
    """
    try:
        config_bgp_global_af_network_on_device(
            device_ip=device_ip, vrf_name=vrf_name, afi_safi=afi_safi, ip_prefix=ip_prefix
        )
    except Exception as e:
        _logger.error(
            f"Failed to configure AF Network {afi_safi} on BGP on device {device_ip}, Reason: {e}."
        )
        raise
    finally:
        discover_bgp(device_ip=device_ip)


def get_bgp_global_af_network(device_ip, asn: int, afi_safi: str = None):
    """
    Retrieves the BGP global address family network configuration from the database for a given device IP, ASN, and AFI/SAFI.

    Args:
        device_ip (str): The IP address of the device.
        asn (int): The Autonomous System Number (ASN) of the BGP.
        afi_safi (str, optional): The address family identifier (AFI) and sub-address family identifier (SAFI)
            combination. Defaults to None.

    Returns:
        list[dict] or dict or None: A list of dictionaries representing the BGP global address family network
        configuration, or a single dictionary if afi_safi is specified, or None if no configuration is found.
    """
    bgp_af_network = get_bgp_global_af_network_from_db(device_ip, asn, afi_safi)
    if isinstance(bgp_af_network, list):
        return [i.__properties__ for i in bgp_af_network] if bgp_af_network else None
    else:
        return bgp_af_network.__properties__ if bgp_af_network else None


def del_bgp_global_af_network(device_ip: str, afi_safi: str, ip_prefix: str, vrf_name: str = "default"):
    """
    Deletes the BGP global address family network configuration from a device.

    Args:
        device_ip (str): The IP address of the device.
        afi_safi (str): The address family identifier and sub-address family identifier combination.
        ip_prefix (str): The IP address and prefix length.
        vrf_name (str, optional): The name of the VRF instance. Defaults to "default".

    Raises:
        Exception: If there is an error while deleting the AF network on the device.

    Returns:
        None
    """
    try:
        del_bgp_global_af_network_on_device(
            device_ip=device_ip,
            vrf_name=vrf_name,
            afi_safi=afi_safi,
            ip_prefix=ip_prefix
        )
    except Exception as e:
        _logger.error(
            f"Failed to delete AF Network {afi_safi} on BGP on device {device_ip}, Reason: {e}."
        )
        raise
    finally:
        discover_bgp(device_ip=device_ip)


def config_bgp_global_af_aggregate_addr(device_ip: str, afi_safi: str, ip_prefix: str, vrf_name: str = "default"):
    """
    Configures the BGP global address family (AF) aggregate address on a device.

    Args:
        device_ip (str): The IP address of the device.
        afi_safi (str): The AF and SAFI (Address Family and Subsequent Address Family Identifier) to configure.
        ip_prefix (str): The IP address and prefix length.
        vrf_name (str, optional): The name of the VRF (Virtual Routing and Forwarding) instance. Defaults to "default".

    Raises:
        Exception: If there is an error while configuring the AF network on the device.

    Returns:
        None
    """
    try:
        config_bgp_global_af_aggregate_addr_on_device(
            device_ip=device_ip, vrf_name=vrf_name, afi_safi=afi_safi, ip_prefix=ip_prefix
        )
    except Exception as e:
        _logger.error(
            f"Failed to configure AF Aggregate Address {afi_safi} on BGP on device {device_ip}, Reason: {e}."
        )
        raise
    finally:
        discover_bgp(device_ip=device_ip)


def get_bgp_global_af_aggregate_addr(device_ip, asn: int, afi_safi: str = None):
    """
    Retrieves the BGP global address family aggregate address configuration from the database for a given device IP, ASN, and AFI/SAFI.

    Args:
        device_ip (str): The IP address of the device.
        asn (int): The Autonomous System Number (ASN) of the BGP.
        afi_safi (str, optional): The address family identifier (AFI) and sub-address family identifier (SAFI)
            combination. Defaults to None.

    Returns:
        list[dict] | dict | None: A list of dictionaries representing the BGP global address family aggregate address network
        configuration, or a single dictionary if afi_safi is specified, or None if no configuration is found.
    """
    bgp_af_aggregate_addr = get_bgp_global_af_aggregate_addr_from_db(device_ip, asn, afi_safi)
    if isinstance(bgp_af_aggregate_addr, list):
        return [i.__properties__ for i in bgp_af_aggregate_addr] if bgp_af_aggregate_addr else None
    else:
        return bgp_af_aggregate_addr.__properties__ if bgp_af_aggregate_addr else None


def del_bgp_global_af_aggregate_addr(device_ip: str, afi_safi: str, ip_prefix: str, vrf_name: str = "default"):
    """
    Deletes the BGP global address family (AF) aggregate address configuration on a device.

    Args:
        device_ip (str): The IP address of the device.
        afi_safi (str): The AF and SAFI (Address Family and Subsequent Address Family Identifier) to delete.
        ip_prefix (str): The IP address and prefix length.
        vrf_name (str, optional): The name of the VRF (Virtual Routing and Forwarding) in which the AF is configured. Defaults to "default".

    Raises:
        Exception: If there is an error while deleting the AF network on the device.

    Returns:
        None
    """
    try:
        del_bgp_global_af_aggregate_addr_on_device(
            device_ip=device_ip,
            vrf_name=vrf_name,
            afi_safi=afi_safi,
            ip_prefix=ip_prefix
        )
    except Exception as e:
        _logger.error(
            f"Failed to delete AF Aggregate Address {afi_safi} on BGP on device {device_ip}, Reason: {e}."
        )
        raise
    finally:
        discover_bgp(device_ip=device_ip)
