from time import sleep
from typing import Dict, List
from grpc import RpcError
from orca_nw_lib.common import IFMode

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
    get_port_channel_vlan_members_from_device,
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
        for port_chnl in port_chnl_json_list:
            ifname_list = []

            # Getting port channel member details
            for mem in lag_mem_table_json_list:
                if port_chnl.get("name") == mem.get("name"):
                    ifname_list.append(mem.get("ifname"))

            #  Getting port channel vlan member details
            port_chnl_vlan_member = {}
            port_chnl_vlan_member_from_device = get_port_channel_vlan_members_from_device(
                device_ip, port_chnl.get("name")
            )
            port_chnl_vlan_member_details = port_chnl_vlan_member_from_device.get(
                "openconfig-vlan:config", {}
            )
            if port_chnl_vlan_member_details:
                if_mode = port_chnl_vlan_member_details.get("interface-mode")
                port_chnl_vlan_member["if_mode"] = if_mode
                if if_mode == str(IFMode.TRUNK):
                    port_chnl_vlan_member["vlan_ids"] = format_and_get_trunk_vlans(
                        port_chnl_vlan_member_details.get("trunk-vlans", [])
                    )
                if if_mode == str(IFMode.ACCESS):
                    port_chnl_vlan_member["vlan_ids"] = [port_chnl_vlan_member_details.get("access-vlan")]

            # Getting port channel IP details
            ipv4_addr = None
            try:
                ip_details = get_port_channel_ip_details_from_device(device_ip, port_chnl.get("name")).get(
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
                _logger.debug(
                    f"No IP information found for port channel {port_chnl.get('name')} on device {device_ip}. Error: {e}")

            port_chnl_obj = PortChannel(
                lag_name=port_chnl.get("name"),
                admin_sts=port_chnl.get("admin_status"),
                mtu=port_chnl.get("mtu"),
                static=port_chnl.get("static"),
                fallback=port_chnl.get("fallback"),
                fast_rate=port_chnl.get("fast_rate"),
                min_links=port_chnl.get("min_links"),
                description=port_chnl.get("description"),
                graceful_shutdown_mode=port_chnl.get("graceful_shutdown_mode"),
                ip_address=ipv4_addr,
                vlan_members=port_chnl_vlan_member,
            )

            # adding lag table details
            for lag in lag_table_json_list:
                if port_chnl.get("name") == lag.get("lagname"):
                    port_chnl_obj.active = lag.get("active")
                    port_chnl_obj.admin_sts = lag.get("admin_status")
                    port_chnl_obj.mtu = lag.get("mtu")
                    port_chnl_obj.name = lag.get("name")
                    port_chnl_obj.fallback_operational = lag.get("fallback_operational")
                    port_chnl_obj.oper_sts = lag.get("oper_status")
                    port_chnl_obj.speed = lag.get("speed")
                    port_chnl_obj.oper_sts_reason = lag.get("reason")
            port_chnl_obj_list[port_chnl_obj] = ifname_list
    return port_chnl_obj_list


def discover_port_chnl(device_ip: str = None):
    """
    Discovers the port channels of a device and inserts them into the database.

    Args:
        device_ip (str, optional): The IP address of the device. Defaults to None.

    Returns:
        None
    """
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
        sleep(2)  ##While updating port channel members(esp. more than one),
        ## it takes time for the port channel members to reflect on the device's mgmt. framework.
        ## Hence, waiting for 1 second before triggering the discovery.
        ## Otherwise during discovery not all port channel members are available to read.
        ## Better would be to implement gNMI subscription for portchannels.
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


def add_port_chnl_vlan_members(device_ip: str, chnl_name: str, if_mode: IFMode, vlan_ids: list[int]):
    """
    Adds VLAN members to a port channel on a device.

    Parameters:
        device_ip (str): The IP address of the device.
        chnl_name (str): The name of the port channel.
        if_mode (IFMode): The interface mode of the port channel.
        vlan_ids (list[int]): A list of VLAN IDs to be added to the port channel. Defaults to None.
    Returns:
        None
    """
    try:
        add_port_chnl_valn_members_on_device(
            device_ip=device_ip, chnl_name=chnl_name, if_mode=if_mode, vlan_ids=vlan_ids
        )
    except Exception as e:
        _logger.error(
            f"Port Channel {chnl_name} VLAN members addition failed on device {device_ip}, Reason: {e}"
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


def remove_port_channel_vlan_member(device_ip: str, chnl_name: str, if_mode: IFMode, vlan_ids: list[int]):
    """
    Removes VLAN members from a port channel on a device.

    Args:
        device_ip (str): The IP address of the device.
        chnl_name (str): The name of the port channel.
        if_mode (IFMode): The interface mode to set, either ACCESS or TRUNK.
        vlan_ids (list[int]): The VLAN IDs to be deleted from the port channel.

    Returns:
        None
    """
    try:
        delete_port_channel_member_vlan_from_device(device_ip, chnl_name, if_mode, vlan_ids)
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
