from grpc._channel import _InactiveRpcError
from orca_nw_lib.graph_db_models import Vlan
from orca_nw_lib.vlan_gnmi import get_vlan_details_from_device

from .common import VlanTagMode

from .device_db import get_device_db_obj
from .vlan_db import (
    get_vlan_obj_from_db,
    get_vlan_mem_ifcs_from_db,
    insert_vlan_in_db,
)
from .vlan_gnmi import (
    add_vlan_mem_interface_on_device,
    config_vlan_on_device,
    config_vlan_tagging_mode_on_device,
    del_vlan_from_device,
    del_vlan_mem_interface_on_device,
)
from .utils import get_logging
from .graph_db_models import Vlan

_logger = get_logging().getLogger(__name__)


def _create_vlan_db_obj(device_ip: str, vlan_name: str = None):
    """
    Retrieves VLAN information from a device.

    Args:
        device_ip (str): The IP address of the device.
        vlan_name (str, optional): The name of the VLAN to retrieve information for.
                                   Defaults to None.

    Returns:
        dict: A dictionary mapping Vlan objects to a list of VLAN member information.
              Each Vlan object contains information such as VLAN ID, name, MTU,
              administrative status, operational status, and autostate.
              {<vlan_db_obj>: {'ifname': 'Ethernet64', 'name': 'Vlan1', 'tagging_mode': 'tagged'}}
    """

    vlan_details = get_vlan_details_from_device(device_ip, vlan_name)
    vlans = []
    for vlan in vlan_details.get("sonic-vlan:VLAN_LIST") or []:
        vlans.append(
            Vlan(
                vlanid=vlan.get("vlanid"),
                name=vlan.get("name"),
            )
        )

    for vlan in vlan_details.get("sonic-vlan:VLAN_TABLE_LIST") or []:
        for v in vlans:
            if v.name == vlan.get("name"):
                v.mtu = vlan.get("mtu")
                v.admin_status = vlan.get("admin_status")
                v.oper_status = vlan.get("oper_status")
                v.autostate = vlan.get("autostate")

    vlans_obj_vs_mem = {}
    for v in vlans:
        members = []
        for item in vlan_details.get("sonic-vlan:VLAN_MEMBER_LIST") or []:
            if v.name == item.get("name"):
                members.append(item)
        vlans_obj_vs_mem[v] = members

    return vlans_obj_vs_mem


def _getJson(device_ip: str, v: Vlan):
    temp = v.__properties__
    temp["members"] = [
        mem.name for mem in get_vlan_mem_ifcs_from_db(device_ip, temp.get("name")) or []
    ]
    return temp


def get_vlan(device_ip, vlan_name: str = None):
    """
    Get VLAN information for a given device.

    Parameters:
        device_ip (str): The IP address of the device.
        vlan_name (str, optional): The name of the VLAN. Defaults to None.

    Returns:
        list: A list of JSON objects representing the VLAN information.
    """
    vlans = get_vlan_obj_from_db(device_ip, vlan_name)
    if vlans is None:
        return None

    if isinstance(vlans, list):
        return [_getJson(device_ip, v) for v in vlans]

    return _getJson(device_ip, vlans)


def del_vlan(device_ip, vlan_name):
    """
    Deletes a VLAN from a device.

    Args:
        device_ip (str): The IP address of the device.
        vlan_name (str): The name of the VLAN to be deleted.

    Raises:
        _InactiveRpcError: If the VLAN deletion fails.

    Returns:
        None
    """

    try:
        del_vlan_from_device(device_ip, vlan_name)
    except _InactiveRpcError as err:
        _logger.error(
            f"VLAN deletion failed on device {device_ip}, Reason: {err.details()}"
        )
        raise
    finally:
        discover_vlan(device_ip)


def config_vlan(
    device_ip: str, vlan_name: str, vlan_id: int, mem_ifs: dict[str:VlanTagMode] = None
):
    """
    Configures a VLAN on a network device.

    Args:
        device_ip (str): The IP address of the device.
        vlan_name (str): The name of the VLAN.
        vlan_id (int): The ID of the VLAN.
        mem_ifs (dict[str:VlanTagMode], optional): A dictionary mapping interface names to VLAN tag modes.

    Raises:
        _InactiveRpcError: If VLAN configuration fails.

    Returns:
        None
    """
    try:
        config_vlan_on_device(device_ip, vlan_name, vlan_id, mem_ifs)
    except _InactiveRpcError as err:
        _logger.error(
            f"VLAN configuration failed on device {device_ip}, Reason: {err.details()}"
        )
        raise
    finally:
        discover_vlan(device_ip)


def add_vlan_mem(device_ip: str, vlan_name: str, mem_ifs: dict[str:VlanTagMode]):
    """
    Adds the specified VLAN as a member on the given device.

    Args:
        device_ip (str): The IP address of the device.
        vlan_name (str): The name of the VLAN.
        mem_ifs (dict[str:VlanTagMode]): A dictionary mapping interface names to VLAN tag modes.

    Raises:
        _InactiveRpcError: If the VLAN member addition fails on the device.

    Returns:
        None
    """
    try:
        add_vlan_mem_interface_on_device(device_ip, vlan_name, mem_ifs)
    except _InactiveRpcError as err:
        _logger.error(
            f"VLAN member addition failed on device {device_ip}, Reason: {err.details()}"
        )
        raise
    finally:
        discover_vlan(device_ip)


def get_vlan_members(device_ip, vlan_name: str):
    """
    Retrieves the members of a VLAN on a specific device.

    Args:
        device_ip (str): The IP address of the device.
        vlan_name (str): The name of the VLAN.

    Returns:
        dict: A dictionary mapping member interface names to their corresponding tagging mode.
    """
    members = get_vlan_mem_ifcs_from_db(device_ip, vlan_name)
    mem_intf_vs_tagging_mode = {}
    for mem in members or []:
        mem_rel = get_vlan_obj_from_db(
            device_ip, vlan_name
        ).memberInterfaces.relationship(mem)
        mem_intf_vs_tagging_mode[mem.name] = mem_rel.tagging_mode
    return mem_intf_vs_tagging_mode


def config_vlan_mem_tagging(
    device_ip: str, vlan_name: str, if_name: str, tagging_mode: VlanTagMode
):
    """
    Configures VLAN member tagging on a network device.

    Args:
        device_ip (str): The IP address of the network device.
        vlan_name (str): The name of the VLAN.
        if_name (str): The name of the interface.
        tagging_mode (VlanTagMode): The tagging mode to be configured.

    Raises:
        _InactiveRpcError: If the VLAN member tagging configuration fails.

    Returns:
        None
    """
    try:
        config_vlan_tagging_mode_on_device(device_ip, vlan_name, if_name, tagging_mode)
    except _InactiveRpcError as err:
        _logger.error(
            f"VLAN member tagging configuration failed on device {device_ip}, Reason: {err.details()}"
        )
        raise
    finally:
        discover_vlan(device_ip)


def del_vlan_mem(device_ip: str, vlan_name: str, if_name: str = None):
    """
    Deletes a VLAN member from a device.

    Args:
        device_ip (str): The IP address of the device.
        vlan_name (str): The name of the VLAN.
        if_name (str, optional): The name of the interface. Defaults to None.

    Raises:
        _InactiveRpcError: If the VLAN member deletion fails.

    Returns:
        None
    """
    try:
        del_vlan_mem_interface_on_device(device_ip, vlan_name, if_name)
    except _InactiveRpcError as err:
        _logger.error(
            f"VLAN member deletion failed on device {device_ip}, Reason: {err.details()}"
        )
        raise
    finally:
        discover_vlan(device_ip)


def discover_vlan(device_ip: str = None, vlan_name: str = None):
    """
    Discovers VLANs on a network device.

    Args:
        device_ip (str, optional): The IP address of the device. Defaults to None.
        vlan_name (str, optional): The name of the VLAN. Defaults to None.

    Raises:
        _InactiveRpcError: If the VLAN discovery fails.

    Returns:
        None
    """

    _logger.info("Discovering VLAN.")
    devices = [get_device_db_obj(device_ip)] if device_ip else get_device_db_obj()
    for device in devices:
        try:
            _logger.info(f"Discovering VLAN on device {device}.")
            insert_vlan_in_db(device, _create_vlan_db_obj(device.mgt_ip, vlan_name))
        except _InactiveRpcError as err:
            _logger.error(
                f"VLAN Discovery Failed on device {device_ip}, Reason: {err.details()}"
            )
            raise
