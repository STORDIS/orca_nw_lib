from time import sleep
from typing import Dict, List
from grpc import RpcError

from .port_chnl_db import (
    get_all_port_chnl_of_device_from_db,
    get_port_chnl_of_device_from_db,
)
from .device_db import get_device_db_obj
from .graph_db_models import PortChannel
from .port_chnl_db import (
    get_port_chnl_members_from_db,
    insert_device_port_chnl_in_db,
)

from .port_chnl_gnmi import (
    add_port_chnl_member_on_device,
    add_port_chnl_on_device,
    del_port_chnl_from_device,
    get_port_chnls_info_from_device,
    remove_port_chnl_member,
    delete_port_channel_member_vlan_from_device,
    delete_all_port_channel_member_vlan_from_device,
    remove_port_channel_ip_from_device,
    add_port_chnl_valn_members_on_device,
    get_port_channel_ip_details_from_device,
)
from .utils import get_logging, format_and_get_trunk_vlans

_logger = get_logging().getLogger(__name__)


def _create_port_chnl_graph_object(device_ip: str) -> Dict[PortChannel, List[str]]:
    """
    Retrieves the information of the port channels from the specified device.

    Args:
        device_ip (str): The IP address of the device.
        port_chnl_name (str, optional): The name of the port channel. Defaults to None.

    Returns:
        Dict[PortChannel, List[str]]: A dictionary mapping PortChannel objects to lists of interface names.
    """
    port_chnl_json = get_port_chnls_info_from_device(device_ip)
    _logger.debug(f"Retrieved port channels info from device {device_ip} {port_chnl_json}")
    port_chnl_obj_list = {}
    if port_chnl_json:
        lag_table_json_list = port_chnl_json.get("sonic-portchannel:LAG_TABLE_LIST", {})
        lag_mem_table_json_list = port_chnl_json.get(
            "sonic-portchannel:LAG_MEMBER_TABLE_LIST", {}
        )
        port_chnl_json_list = port_chnl_json.get("sonic-portchannel:PORTCHANNEL_LIST", {})
        for lag in lag_table_json_list or []:
            ifname_list = []
            for mem in lag_mem_table_json_list or []:
                if lag.get("lagname") == mem.get("name"):
                    ifname_list.append(mem.get("ifname"))
            port_chnl_item = {}
            port_chnl_vlan_member = {}
            for port_chnl in port_chnl_json_list:
                if lag.get("lagname") == port_chnl.get("name"):
                    port_chnl_item = port_chnl
                    if tagged_vlans := port_chnl.get("tagged_vlans"):
                        port_chnl_vlan_member["trunk_vlans"] = format_and_get_trunk_vlans(tagged_vlans)
                    if access_vlan := port_chnl.get("access_vlan"):
                        port_chnl_vlan_member["access_vlan"] = int(access_vlan)
            
            ipv4_addr = None
            try:
                ip_details = get_port_channel_ip_details_from_device(device_ip, lag.get("lagname")).get(
                    "openconfig-if-ip:addresses", {}
                )
                ipv4_addresses = ip_details.get("address", [])
                for ipv4 in ipv4_addresses or []:
                    if (ip := ipv4.get("config", {}).get("ip", "")) and (
                            pfx := ipv4.get("config", {}).get("prefix-length", "")
                    ):
                        ipv4_addr = f"{ip}/{pfx}"
                        break
            except RpcError as e:
                _logger.debug(f"No IP information found for port channel {lag.get('lagname')} on device {device_ip}. Error: {e}")
                
            port_chnl_obj_list[
                PortChannel(
                    active=lag.get("active"),
                    lag_name=lag.get("lagname"),
                    admin_sts=lag.get("admin_status"),
                    mtu=lag.get("mtu"),
                    name=lag.get("name"),
                    fallback_operational=lag.get("fallback_operational"),
                    oper_sts=lag.get("oper_status"),
                    speed=lag.get("speed"),
                    oper_sts_reason=lag.get("reason"),
                    static=port_chnl_item.get("static"),
                    fallback=port_chnl_item.get("fallback"),
                    fast_rate=port_chnl_item.get("fast_rate"),
                    min_links=port_chnl_item.get("min_links"),
                    description=port_chnl_item.get("description"),
                    graceful_shutdown_mode=port_chnl_item.get("graceful_shutdown_mode"),
                    ip_address=ipv4_addr,
                    vlan_members=port_chnl_vlan_member,
                )
            ] = ifname_list
    return port_chnl_obj_list


def discover_port_chnl(device_ip: str = None):
    _logger.info("Port Channel Discovery Started.")
    devices = [get_device_db_obj(device_ip)] if device_ip else get_device_db_obj()
    for device in devices:
        _logger.info(f"Discovering Port Channels of device {device}.")
        try:
            insert_device_port_chnl_in_db(
                device, _create_port_chnl_graph_object(device.mgt_ip)
            )
        except Exception as e:
            _logger.error(
                f"Couldn't discover Port Channel on device {device_ip}, Reason: {e}"
            )
            raise


def get_port_chnl(device_ip: str, port_chnl_name: str = None):
    """
    Retrieves the port channel information for a given device IP.

    Args:
        device_ip (str): The IP address of the device.
        port_chnl_name (str, optional): The name of the port channel. Defaults to None.

    Returns:
        Union[List[Dict[str, Any]], Dict[str, Any], None]: If `port_chnl_name` is provided, 
        returns the properties of the specified port channel if it exists, otherwise returns None. 
        If `port_chnl_name` is not provided, returns a list of properties of all port channels associated with the device IP. 
        If there are no port channels associated with the device IP, returns an empty list.
    """
    if port_chnl_name:
        return (
            port_chnl.__properties__
            if (port_chnl := get_port_chnl_of_device_from_db(device_ip, port_chnl_name))
            else None
        )
    return [
        chnl.__properties__
        for chnl in get_all_port_chnl_of_device_from_db(device_ip) or []
    ]


def add_port_chnl(
        device_ip: str, chnl_name: str, admin_status: str = None, mtu: int = None,
        static: bool = None, fallback: bool = None, fast_rate: bool = None,
        min_links: int = None, description: str = None, graceful_shutdown_mode: str = None,
        ip_addr_with_prefix: str = None,
):
    """
    Adds a port channel to a device,
    and triggers the discovery of the port channel on the device to keep database up to date.

    Args:
        device_ip (str): The IP address of the device.
        chnl_name (str): The name of the port channel.
        admin_status (str, optional): The administrative status of the port channel. Defaults to None.
        mtu (int, optional): The maximum transmission unit (MTU) of the port channel. Defaults to None.
        static (bool, optional): Whether the port channel is static or not. Defaults to None.
        fallback (bool, optional): Whether the port channel is a fallback port channel. Defaults to None.
        fast_rate (bool, optional): Whether the port channel uses fast rate. Defaults to None.
        min_links (int, optional): The minimum number of links in the port channel. Defaults to  None.
        description (str, optional): The description of the port channel. Defaults to None.
        graceful_shutdown_mode (bool, optional): Whether the port channel is in graceful shutdown mode.Defaults to None.
        ip_addr_with_prefix (str, optional): The IP address and prefix of the port channel. Defaults to None.
    Returns:
        None
    """

    try:
        add_port_chnl_on_device(
            device_ip=device_ip, chnl_name=chnl_name, admin_status=admin_status, mtu=mtu,
            static=static, fallback=fallback, fast_rate=fast_rate, min_links=min_links,
            description=description, graceful_shutdown_mode=graceful_shutdown_mode,
            ip_addr_with_prefix=ip_addr_with_prefix,
        )
    except Exception as e:
        _logger.error(
            f"Port Channel {chnl_name} addition failed on device {device_ip}, Reason: {e}"
        )
        raise
    finally:
        discover_port_chnl(device_ip)


def del_port_chnl(device_ip: str, chnl_name: str = None):
    """
    Deletes a port channel from a device,
    and triggers the discovery of the port channel on the device to keep database up to date.

    Args:
        device_ip (str): The IP address of the device.
        chnl_name (str, optional): The name of the port channel to delete. Defaults to None.

    Returns:
        None
    """
    port_chnl = get_port_chnl(device_ip, chnl_name)
    port_chnl_list = port_chnl if isinstance(port_chnl, list) else [port_chnl]
    try:
        for chnl in [item for item in port_chnl_list if item is not None] or []:
            if chnl.get("lag_name"):
                del_port_chnl_from_device(device_ip, chnl.get("lag_name"))
    except Exception as e:
        _logger.error(
            f"Port Channel deletion failed on device {device_ip}, Reason: {e}"
        )
        raise
    finally:
        discover_port_chnl(device_ip)


def add_port_chnl_mem(device_ip: str, chnl_name: str, ifnames: list[str]):
    """
    Adds channel members to a port channel on the specified device,
    and triggers the discovery of the port channel on the device to keep database up to date.

    Parameters:
        device_ip (str): The IP address of the device.
        chnl_name (str): The name of the port channel.
        ifnames (list[str]): A list of interface names to be added as members to the port channel.

    Returns:
        None
    """

    try:
        add_port_chnl_member_on_device(device_ip, chnl_name, ifnames)
    except Exception as e:
        _logger.error(
            f"Port Channel {chnl_name} members {ifnames} addition failed on device {device_ip}, Reason: {e}"
        )
        raise
    finally:
        discover_port_chnl(device_ip)


def del_port_chnl_mem(device_ip: str, chnl_name: str, ifname: str):
    """
    Deletes a member from a port channel on a given device.

    Args:
        device_ip (str): The IP address of the device.
        chnl_name (str): The name of the port channel.
        ifname (str): The name of the interface to be removed from the port channel.

    Returns:
        None
    """
    try:
        remove_port_chnl_member(device_ip, chnl_name, ifname)
    except Exception as e:
        _logger.error(
            f"Port Channel {chnl_name} member {ifname} deletion failed on device {device_ip}, Reason: {e}"
        )
        raise
    finally:
        discover_port_chnl(device_ip)


def get_port_chnl_members(device_ip: str, port_chnl_name: str, ifname: str = None):
    """
    Retrieves the members of a port channel on a device.

    Args:
        device_ip (str): The IP address of the device.
        port_chnl_name (str): The name of the port channel.
        ifname (str, optional): The name of the interface. Defaults to None.

    Returns:
        Union[List[Dict[str, Any]], None]: A list of dictionaries representing the properties of each member of the port channel. Returns None if no members are found.
    """
    if ifname:
        return (
            port_chnl_mem.__properties__
            if (
                port_chnl_mem := get_port_chnl_members_from_db(
                    device_ip, port_chnl_name, ifname
                )
            )
            else None
        )
    else:
        return [
            mem.__properties__
            for mem in get_port_chnl_members_from_db(device_ip, port_chnl_name) or []
        ]


def add_port_chnl_vlan_members(device_ip: str, chnl_name: str, trunk_vlans: list[int] = None, access_vlan: int = None):
    """
    Adds VLAN members to a port channel on a device.

    Parameters:
        device_ip (str): The IP address of the device.
        chnl_name (str): The name of the port channel.
        trunk_vlans (list[int], optional): The list of VLAN IDs to be added as trunk VLANs. Defaults to None.
        access_vlan (int, optional): The VLAN ID to be added as access VLAN. Defaults to None.

    Returns:
        None
    """
    try:
        add_port_chnl_valn_members_on_device(
            device_ip=device_ip, chnl_name=chnl_name, trunk_vlans=trunk_vlans, access_vlan=access_vlan
        )
    except Exception as e:
        _logger.error(
            f"Port Channel {chnl_name}  vlan members {trunk_vlans} and {access_vlan} addition failed on device {device_ip}, Reason: {e}"
        )
        raise
    finally:
        discover_port_chnl(device_ip)


def remove_port_chnl_ip(device_ip: str, chnl_name: str, ip_address: str = None):
    """
    Removes an IP address from a port channel on a device.

    Args:
        device_ip (str): The IP address of the device.
        chnl_name (str): The name of the port channel.
        ip_address (str, optional): The IP address to be removed. Defaults to None.

    Returns:
        None
    """
    try:
        remove_port_channel_ip_from_device(device_ip, chnl_name, ip_address)
    except Exception as e:
        _logger.error(f"Port Channel IP removal failed on device {device_ip}, Reason: {e}")
        raise
    finally:
        discover_port_chnl(device_ip)


def remove_port_channel_vlan_member(device_ip: str, chnl_name: str, access_vlan: int = None,
                                    trunk_vlans: list[int] = None):
    """
    Removes VLAN members from a port channel on a device.

    Args:
        device_ip (str): The IP address of the device.
        chnl_name (str): The name of the port channel.
        access_vlan (int): The VLAN ID to be removed as access VLAN.
        trunk_vlans (list[int], optional): The list of VLAN IDs to be removed as trunk VLANs. Defaults to None.

    Returns:
        None
    """
    try:
        delete_port_channel_member_vlan_from_device(device_ip, chnl_name, access_vlan, trunk_vlans)
    except Exception as e:
        _logger.error(f"Port Channel Vlan members removal failed on device {device_ip}, Reason: {e}")
        raise
    finally:
        discover_port_chnl(device_ip)


def remove_all_port_channel_vlan_member(device_ip: str, chnl_name: str):
    """
    Removes all VLAN members from a port channel on a device.

    Args:
        device_ip (str): The IP address of the device.
        chnl_name (str): The name of the port channel.

    Returns:
        None
    """
    try:
        delete_all_port_channel_member_vlan_from_device(device_ip, chnl_name)
    except Exception as e:
        _logger.error(f"Port Channel Vlan members removal failed on device {device_ip}, Reason: {e}")
        raise
    finally:
        discover_port_chnl(device_ip)
