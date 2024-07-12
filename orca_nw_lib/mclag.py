from typing import Any, Dict, List, Union

from orca_nw_lib.utils import get_logging
from .common import MclagFastConvergence

from .device_db import get_device_db_obj
from .mclag_db import (
    create_mclag_peer_link_rel_in_db,
    get_mclag_gw_mac_of_device_from_db,
    get_mclag_of_device_from_db,
    insert_device_mclag_gw_macs_in_db,
    insert_device_mclag_in_db,
)


from .mclag_gnmi import (
    config_mclag_domain_on_device,
    config_mclag_gateway_mac_on_device,
    config_mclag_member_on_device,
    del_mclag_from_device,
    del_mclag_gateway_mac_from_device,
    del_mclag_member_on_device,
    get_mclag_config_from_device,
    get_mclag_gateway_mac_from_device,
    get_mclag_domain_fast_convergence_from_device,
    remove_mclag_domain_fast_convergence_on_device,
    add_mclag_domain_fast_convergence_on_device,
)
from .graph_db_models import MCLAG_GW_MAC, MCLAG

_logger = get_logging().getLogger(__name__)


def _create_mclag_graph_objects(device_ip: str) -> dict:
    """
    Generates a dictionary of MCLAG objects
    and their associated interfaces based on the provided device IP.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        dict: A dictionary containing MCLAG objects as keys
        and a list of associated interfaces as values.
    """
    mclags_obj_list = {}
    mclag_config = get_mclag_config_from_device(device_ip)
    mclag = mclag_config.get("openconfig-mclag:mclag", {})
    mclag_domains_dict_list = mclag.get("mclag-domains", {}).get("mclag-domain")
    mclag_intfc_list = mclag.get("interfaces", {}).get("interface")

    for mclag_domain in mclag_domains_dict_list or []:
        domain_id = mclag_domain.get("config").get("domain-id")
        mclag_device_details = get_mclag_domain_fast_convergence_from_device(
            device_ip=device_ip, domain_id=domain_id
        )
        fast_convergence = None
        for mclag_item in (
            mclag_device_details.get("sonic-mclag:MCLAG_DOMAIN_LIST") or []
        ):
            if mclag_item.get("domain_id") == domain_id:
                fast_convergence = mclag_item.get("fast_convergence")
        mclag_obj = MCLAG(
            domain_id=domain_id,
            keepalive_interval=mclag_domain.get("config").get("keepalive-interval"),
            mclag_sys_mac=mclag_domain.get("config").get("mclag-system-mac"),
            peer_addr=mclag_domain.get("config").get("peer-address"),
            peer_link=mclag_domain.get("config").get("peer-link"),
            session_timeout=mclag_domain.get("config").get("session-timeout"),
            source_address=mclag_domain.get("config").get("source-address"),
            delay_restore=mclag_domain.get("config").get("delay-restore"),
            oper_status=mclag_domain.get("state").get("oper-status"),
            role=mclag_domain.get("state").get("role"),
            system_mac=mclag_domain.get("state").get("system-mac"),
            session_vrf=mclag_domain.get("config").get("session-vrf"),
            fast_convergence=fast_convergence,
        )
        intfc_list = [
            mclag_intfc["name"]
            for mclag_intfc in mclag_intfc_list or []
            if mclag_obj.domain_id == mclag_intfc["config"]["mclag-domain-id"]
        ]

        mclags_obj_list[mclag_obj] = intfc_list

    return mclags_obj_list


def _create_mclag_gw_mac_obj(device_ip: str) -> List[MCLAG_GW_MAC]:
    """
    Creates a list of MCLAG_GW_MAC objects based on the given device IP.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        List[MCLAG_GW_MAC]: A list of MCLAG_GW_MAC objects.

    Raises:
        None.

    Example Usage:
        create_mclag_gw_mac_obj("192.168.0.1")
    """
    mclag_gw_objs = []
    resp = get_mclag_gateway_mac_from_device(device_ip)

    oc_macs = resp.get("openconfig-mclag:mclag-gateway-macs", {})

    for mac_data in oc_macs.get("mclag-gateway-mac", []):
        gw_mac = mac_data.get("gateway-mac")
        mclag_gw_objs.append(MCLAG_GW_MAC(gateway_mac=gw_mac))

    return mclag_gw_objs


def discover_mclag(device_ip: str = None):
    """
    Discover MCLAG for a given device.

    Args:
        device_ip (str, optional): The IP address of the device. Defaults to None.

    Returns:
        None

    """

    _logger.info("MCLAG Discovery Started.")
    devices = [get_device_db_obj(device_ip)] if device_ip else get_device_db_obj()
    for device in devices:
        try:
            _logger.info(f"Discovering MCLAG on device {device}.")
            insert_device_mclag_in_db(
                device, _create_mclag_graph_objects(device.mgt_ip)
            )
        except Exception as e:
            _logger.error(f"MCLAG Discovery Failed on device {device_ip}, Reason: {e}")
            raise
    create_mclag_peer_link_rel_in_db()


def discover_mclag_gw_macs(device_ip: str = None):
    """
    Discover MCLAG gateway MAC addresses for a given device or all devices.

    Args:
        device_ip (str): The IP address of the device to discover MCLAG gateway MAC addresses for.
            If None, MCLAG gateway MAC addresses for all devices will be discovered. Default is None.

    Returns:
        None

    """
    _logger.info("MCLAG GW MAC Discovery Started.")
    devices = [get_device_db_obj(device_ip)] if device_ip else get_device_db_obj()
    for device in devices:
        try:
            _logger.info(f"Discovering MCLAG on device {device}.")
            insert_device_mclag_gw_macs_in_db(
                device, _create_mclag_gw_mac_obj(device.mgt_ip)
            )
        except Exception as e:
            _logger.error(
                f"MCLAG gateway MAC Discovery Failed on device {device_ip}, Reason: {e}"
            )
            raise


def get_mclags(
    device_ip: str, domain_id=None
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Retrieves the MCLAG information for a given device IP and domain ID.

    Args:
        device_ip (str): The IP address of the device.
        domain_id (Optional[int]): The ID of the domain. Defaults to None.

    Returns:
        Union[Dict[str, Any], List[Dict[str, Any]]]: The MCLAG information
        as a dictionary or a list of dictionaries.
    """

    if domain_id:
        mclag = get_mclag_of_device_from_db(device_ip, domain_id)
        return mclag.__properties__ if mclag else None
    else:
        return [
            mclag.__properties__ for mclag in get_mclag_of_device_from_db(device_ip)
        ]


def config_mclag(
    device_ip: int,
    domain_id: int,
    source_addr: str = None,
    peer_addr: str = None,
    peer_link: str = None,
    mclag_sys_mac: str = None,
    keepalive_int: int = 1,
    session_timeout: int = 30,
    delay_restore: int = 300,
    session_vrf: str = None,
    fast_convergence: MclagFastConvergence = None,
):
    """
    Configures MCLAG on the device.

    Args:
        device_ip (str): The IP address of the device.
        domain_id (int): The domain ID for MCLAG.
        source_addr (str): The source address for MCLAG.
        peer_addr (str): The peer address for MCLAG.
        peer_link (str): The peer link for MCLAG.
        mclag_sys_mac (str): The MCLAG system MAC address.
        keepalive_int (int, optional): The keepalive interval. Defaults to None.
        session_timeout (int, optional): The session timeout. Defaults to None.
        delay_restore (int, optional): The delay to restore MCLAG. Defaults to None.
        session_vrf (str, optional): The session VRF. Defaults to None.
        fast_convergence (str, optional): The fast convergence. Defaults to None.

    Returns:
        None

    """
    try:
        config_mclag_domain_on_device(
            device_ip,
            domain_id,
            source_addr,
            peer_addr,
            peer_link,
            mclag_sys_mac,
            keepalive_int,
            session_timeout,
            delay_restore,
            session_vrf,
            fast_convergence,
        )

    except Exception as e:
        _logger.error(
            f" MCLAG configuration failed on device_ip : {device_ip}, Reason: {e}"
        )
        raise
    finally:
        discover_mclag(device_ip)


def del_mclag(device_ip: str):
    """
    Deletes the MCLAG configuration from the specified device.

    Parameters:
        device_ip (str): The IP address of the device.

    Returns:
        None
    """
    try:
        del_mclag_from_device(device_ip)
    except Exception as e:
        _logger.error(f" MCLAG deletion failed on device_ip : {device_ip}, Reason: {e}")
        raise
    finally:
        discover_mclag(device_ip)


def get_mclag_gw_mac(
    device_ip: str, gw_mac: str = None
) -> Union[List[Dict[str, Any]], Dict[str, Any], None]:
    """
    Retrieves the MCLAG gateway MAC address for a given device IP.

    Args:
        device_ip (str): The IP address of the device.
        gw_mac (str, optional): The gateway MAC address. Defaults to None.

    Returns:
        Union[List[Dict[str, Any]], Dict[str, Any], None]:
        - If the `gw_mac` parameter is provided, returns a dictionary representing
          the properties of the MCLAG gateway MAC address. If the MCLAG gateway
          MAC address is not found, returns None.
        - If the `gw_mac` parameter is not provided, returns a list of dictionaries,
          where each dictionary represents the properties of a MCLAG gateway MAC
          address for the specified device IP. If no MCLAG gateway MAC addresses
          are found, returns an empty list.

    """
    if gw_mac:
        mclag_gw_mac = get_mclag_gw_mac_of_device_from_db(device_ip, gw_mac)
        return mclag_gw_mac.__properties__ if mclag_gw_mac else None
    return [
        mac.__properties__
        for mac in get_mclag_gw_mac_of_device_from_db(device_ip) or []
    ]


def config_mclag_gw_mac(device_ip: str, gw_mac: str):
    """
    Configures the MCLAG gateway MAC address for the specified device IP.

    Args:
        device_ip (str): The IP address of the device.
        gw_mac (str): The gateway MAC address.

    Returns:
        None

    """

    try:
        config_mclag_gateway_mac_on_device(device_ip, gw_mac)
    except Exception as e:
        _logger.error(
            f"MCLAG GW MAC {gw_mac} configuration failed on device_ip : {device_ip}, Reason: {e}"
        )
        raise
    finally:
        discover_mclag_gw_macs(device_ip)


def del_mclag_gw_mac(device_ip: str):
    """
    Deletes the MCLAG gateway MAC address from the specified device.

    Args:
        device_ip (str): The IP address of the device from which to delete the MCLAG gateway MAC address.

    Raises:
        Exception: If the deletion of the MCLAG gateway MAC address fails.

    Returns:
        None
    """
    try:
        del_mclag_gateway_mac_from_device(device_ip)
    except Exception as e:
        _logger.error(
            f"MCLAG GW MAC deletion failed on device_ip : {device_ip}, Reason: {e}"
        )
        raise
    finally:
        discover_mclag_gw_macs(device_ip)


def get_mclag_mem_intfs(device_ip: str, mclag_domain_id: int):
    """
    Retrieves the list of MCLAG member interfaces for a given device IP and MCLAG domain ID.

    Args:
        device_ip (str): The IP address of the device.
        mclag_domain_id (int): The ID of the MCLAG domain.

    Returns:
        list: A list of dictionaries, where each dictionary represents the properties of a MCLAG member interface.
              The properties include information such as interface name, status, and configuration details.

    Raises:
        None
    """
    mclag = get_mclag_of_device_from_db(device_ip, mclag_domain_id)

    op_dict = []
    if mclag:
        mem_intfcs = mclag.intfc_members.all()

        for intf in mem_intfcs or []:
            op_dict.append(intf.__properties__)
    return op_dict


def get_mclag_mem_portchnls(device_ip: str, mclag_domain_id: int):
    """
    Retrieves the MCLAG member port channels for a given device IP and MCLAG domain ID.

    Args:
        device_ip (str): The IP address of the device.
        mclag_domain_id (int): The ID of the MCLAG domain.

    Returns:
        list: A list of dictionaries representing the properties of the member port channels.
    """
    mclag = get_mclag_of_device_from_db(device_ip, mclag_domain_id)

    op_dict = []
    if mclag:
        mem_chnl = mclag.portChnl_member.all()

        for chnl in mem_chnl or []:
            op_dict.append(chnl.__properties__)
    return op_dict


def config_mclag_mem_portchnl(
    device_ip: str, mclag_domain_id: int, port_chnl_name: str
):
    """
    Configures an MCLAG member port channel on the specified device.

    Args:
        device_ip (str): The IP address of the device.
        mclag_domain_id (int): The ID of the MCLAG domain.
        port_chnl_name (str): The name of the port channel.

    Returns:
        None
    """
    try:
        config_mclag_member_on_device(device_ip, mclag_domain_id, port_chnl_name)
    except Exception as e:
        _logger.error(
            f"MCLAG member {port_chnl_name} configuration failed on mclag_domain_id : {mclag_domain_id} and device_ip : {device_ip}, Reason: {e} "
        )
        raise
    finally:
        discover_mclag(device_ip)


def del_mclag_member(device_ip: str, mclag_member: str = None):
    """
    Deletes an MCLAG member on the specified device.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        None
    """
    try:
        del_mclag_member_on_device(device_ip, mclag_member)
    except Exception as e:
        _logger.error(
            f"MCLAG member deletion failed on device_ip : {device_ip}, Reason: {e}"
        )
        raise
    finally:
        discover_mclag(device_ip)


def remove_mclag_domain_fast_convergence(device_ip: str, domain_id: int):
    """
    Deletes an MCLAG domain fast convergence on the specified device.

    Args:
        device_ip (str): The IP address of the device.
        domain_id (int): The ID of the MCLAG domain.

    Returns:
        None
    """
    try:
        remove_mclag_domain_fast_convergence_on_device(device_ip, domain_id)
    except Exception as e:
        _logger.error(
            f"MCLAG domain fast convergence deletion failed on domain_id : {domain_id} and device_ip : {device_ip}, Reason: {e} "
        )
        raise
    finally:
        discover_mclag(device_ip)


def add_mclag_domain_fast_convergence(device_ip: str, domain_id: int):
    """
    ADDs an MCLAG domain fast convergence on the specified device.

    Args:
        device_ip (str): The IP address of the device.
        domain_id (int): The ID of the MCLAG domain.

    Returns:
        None
    """
    try:
        add_mclag_domain_fast_convergence_on_device(device_ip, domain_id)
    except Exception as e:
        _logger.error(
            f"MCLAG domain fast convergence deletion failed on domain_id : {domain_id} and device_ip : {device_ip}, Reason: {e} "
        )
        raise
    finally:
        discover_mclag(device_ip)
