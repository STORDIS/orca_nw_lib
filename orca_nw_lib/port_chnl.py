from time import sleep
from typing import Any, Dict, List, Optional, Union
from grpc._channel import _InactiveRpcError


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
    add_port_chnl_member,
    add_port_chnl_on_device,
    del_port_chnl_from_device,
    get_port_chnls_info_from_device,
    remove_port_chnl_member,
)
from .utils import get_logging

_logger = get_logging().getLogger(__name__)


def _create_port_chnl_graph_object(
    device_ip: str, port_chnl_name: str = None
) -> Dict[PortChannel, List[str]]:
    """
    Retrieves the information of the port channels from the specified device.

    Args:
        device_ip (str): The IP address of the device.
        port_chnl_name (str, optional): The name of the port channel. Defaults to None.

    Returns:
        Dict[PortChannel, List[str]]: A dictionary mapping PortChannel objects to lists of interface names.
    """
    port_chnl_json = get_port_chnls_info_from_device(device_ip, port_chnl_name)
    port_chnl_obj_list = {}
    if port_chnl_json:
        lag_table_json_list = port_chnl_json.get("sonic-portchannel:LAG_TABLE_LIST", {})
        lag_mem_table_json_list = port_chnl_json.get(
            "sonic-portchannel:LAG_MEMBER_TABLE_LIST", {}
        )
        for lag in lag_table_json_list or []:
            ifname_list = []
            for mem in lag_mem_table_json_list or []:
                if lag.get("lagname") == mem.get("name"):
                    ifname_list.append(mem.get("ifname"))
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
                )
            ] = ifname_list

    return port_chnl_obj_list


def discover_port_chnl(device_ip: str = None, port_chnl_name: str = None):
    """
    Discover port channels of a device and insert them into the database.

    Args:
        device_ip (str, optional): The IP address of the device. Defaults to None.
        port_chnl_name (str, optional): The name of the port channel. Defaults to None.

    Returns:
        None

    Raises:
        _InactiveRpcError: If the port channel discovery fails on the specified device.

    """

    _logger.info("Port Channel Discovery Started.")
    devices = [get_device_db_obj(device_ip)] if device_ip else get_device_db_obj()
    for device in devices:
        try:
            _logger.info(f"Discovering Port Channels of device {device}.")
            insert_device_port_chnl_in_db(
                device, _create_port_chnl_graph_object(device.mgt_ip, port_chnl_name)
            )
        except _InactiveRpcError as err:
            _logger.error(
                f"Port Channel Discovery Failed on device {device_ip}, Reason: {err.details()}"
            )
            raise


def get_port_chnl(
    device_ip: str, port_chnl_name: Optional[str] = None
) -> Union[List[Dict[str, Any]], Dict[str, Any], None]:
    """
    Retrieves the port channel information for a given device.

    Args:
        device_ip (str): The IP address of the device.
        port_chnl_name (Optional[str], optional): The name of the port channel. Defaults to None.

    Returns:
        Union[List[Dict[str, Any]], Dict[str, Any], None]: If `port_chnl_name` is provided,
        returns the properties of the specified port channel as a dictionary.
        If `port_chnl_name` is not provided, returns a list of dictionaries containing
        the properties of all port channels associated with the device.
        If no port channels are found, returns an empty list.
        If the device or port channel is not found, returns None.
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
    device_ip: str, chnl_name: str, admin_status: str = None, mtu: int = None
):
    """
    Adds a port channel to a device,
    and triggers the discovery of the port channel on the device to keep database up to date.

    Args:
        device_ip (str): The IP address of the device.
        chnl_name (str): The name of the port channel.
        admin_status (str, optional): The administrative status of the port channel. Defaults to None.
        mtu (int, optional): The maximum transmission unit (MTU) of the port channel. Defaults to None.

    Raises:
        _InactiveRpcError: If the addition of the port channel fails.

    Returns:
        None
    """

    try:
        add_port_chnl_on_device(device_ip, chnl_name, admin_status, mtu)
    except _InactiveRpcError as err:
        _logger.error(
            f"Port Channel {chnl_name} addition failed on device {device_ip}, Reason: {err.details()}"
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

    Raises:
        _InactiveRpcError: If the deletion of the port channel fails.

    Returns:
        None
    """

    try:
        del_port_chnl_from_device(device_ip, chnl_name)
    except _InactiveRpcError as err:
        _logger.error(
            f"Port Channel {chnl_name} deletion failed on device {device_ip}, Reason: {err.details()}"
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

    Raises:
        _InactiveRpcError: If the addition of port channel members fails.

    Returns:
        None
    """

    try:
        add_port_chnl_member(device_ip, chnl_name, ifnames)
    except _InactiveRpcError as err:
        _logger.error(
            f"Port Channel {chnl_name} members {ifnames} addition failed on device {device_ip}, Reason: {err.details()}"
        )
        raise
    finally:
        ## Note - A bit strange but despite of being single threaded process,
        ## Need to keep a delay between creating channel members and getting them.
        sleep(1)
        discover_port_chnl(device_ip)


def del_port_chnl_mem(device_ip: str, chnl_name: str, ifname: str):
    """
    Deletes a member from a port channel on a given device.

    Args:
        device_ip (str): The IP address of the device.
        chnl_name (str): The name of the port channel.
        ifname (str): The name of the interface to be removed from the port channel.

    Raises:
        _InactiveRpcError: If the deletion of the member fails.

    Returns:
        None
    """
    try:
        remove_port_chnl_member(device_ip, chnl_name, ifname)
    except _InactiveRpcError as err:
        _logger.error(
            f"Port Channel {chnl_name} member {ifname} deletion failed on device {device_ip}, Reason: {err.details()}"
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
