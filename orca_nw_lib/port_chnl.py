from time import sleep
from typing import List, Optional

from .port_chnl_db import (
    get_all_port_chnl_of_device_from_db,
    get_port_chnl_of_device_from_db,
)
from .device import get_device_from_db
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


def createPortChnlGraphObject(device_ip: str, port_chnl_name: str = None):
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
    Discover the port channel of a device.

    Args:
        device_ip (str): The IP address of the device. If None, all devices will be used.
        port_chnl_name (str): The name of the port channel.
        If None, all port channels will be discovered.

    Returns:
        None
    """
    _logger.info("Port Channel Discovery Started.")
    devices = [get_device_from_db(device_ip)] if device_ip else get_device_from_db()
    for device in devices:
        _logger.info(f"Discovering Port Channels of device {device}.")
        insert_device_port_chnl_in_db(
            device, createPortChnlGraphObject(device.mgt_ip, port_chnl_name)
        )


def get_port_chnl(device_ip: str, port_chnl_name: Optional[str] = None) -> List[dict]:
    """
    Retrieves the port channel information for a specific device.

    Args:
        device_ip (str): The IP address of the device.
        port_chnl_name (Optional[str], optional): The name of the port channel. Defaults to None.

    Returns:
        List[dict]: A list of dictionaries containing the properties of the port channels.

    Raises:
        None

    Examples:
        >>> get_port_chnl("192.168.0.1", "PortChannel1")
        [{'property1': 'value1', 'property2': 'value2'},
        {'property1': 'value3', 'property2': 'value4'}]
    """
    op_dict = []
    if port_chnl_name:
        if port_chnl := get_port_chnl_of_device_from_db(device_ip, port_chnl_name):
            op_dict.append(port_chnl.__properties__)
    else:
        port_chnl = get_all_port_chnl_of_device_from_db(device_ip)
        for chnl in port_chnl or []:
            op_dict.append(chnl.__properties__)
    return op_dict


def add_port_chnl(
    device_ip: str, chnl_name: str, admin_status: str = None, mtu: int = None
):
    """
    Adds a port channel to a device,
    and triggers the discovery of the port channel on the device to keep database up to date.

    Args:
        device_ip (str): The IP address of the device.
        chnl_name (str): The name of the port channel.
        admin_status (str, optional): The administrative status of the port channel.
        Defaults to None.
        mtu (int, optional): The maximum transmission unit (MTU) size of the port channel.
        Defaults to None.

    Returns:
        None
    """
    add_port_chnl_on_device(device_ip, chnl_name, admin_status, mtu)
    discover_port_chnl(device_ip)


def del_port_chnl(device_ip: str, chnl_name: str):
    """
    Deletes a port channel from a device,
    and triggers the discovery of the port channel on the device to keep database up to date.

    Args:
        device_ip (str): The IP address of the device.
        chnl_name (str): The name of the port channel to delete.

    Returns:
        None
    """
    del_port_chnl_from_device(device_ip, chnl_name)
    discover_port_chnl(device_ip)


def add_port_chnl_mem(device_ip: str, chnl_name: str, ifnames: list[str]):
    """
    Adds channel members to a port channel on the specified device,
    and triggers the discovery of the port channel on the device to keep database up to date.

    Args:
        device_ip (str): The IP address of the device.
        chnl_name (str): The name of the channel to add the members to.
        ifnames (list[str]): A list of interface names to add as members.

    Returns:
        None
    """
    add_port_chnl_member(device_ip, chnl_name, ifnames)
    ## Note - A bit strange but despite of being single threaded process,
    ## Need to keep a delay between creating channel members and getting them.
    sleep(1)
    discover_port_chnl(device_ip)


def del_port_chnl_mem(device_ip: str, chnl_name: str, ifname: str):
    remove_port_chnl_member(device_ip, chnl_name, ifname)
    discover_port_chnl(device_ip)


def get_port_chnl_members(device_ip: str, port_chnl_name: str, ifname: str = None):
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
        op_dict = []
        port_chnl_mems = get_port_chnl_members_from_db(device_ip, port_chnl_name)
        for mem in port_chnl_mems or []:
            op_dict.append(mem.__properties__)
        return op_dict
