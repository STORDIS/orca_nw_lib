from orca_nw_lib.vlan_gnmi import get_vlan_details_from_device

from .common import IFMode, VlanAutoState

from .device_db import get_device_db_obj
from .stp_vlan import discover_stp_vlan
from .vlan_db import (
    get_vlan_member_port_channels_from_db,
    get_vlan_obj_from_db,
    get_vlan_mem_ifcs_from_db,
    insert_vlan_in_db,
)
from .vlan_gnmi import (
    config_vlan_on_device,
    del_vlan_from_device,
    get_vlan_ip_details_from_device,
    remove_anycast_addr_from_vlan_on_device,
    remove_ip_from_vlan_on_device,
    add_vlan_members_on_device,
    delete_vlan_members_on_device,
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
        v_name = vlan.get("name")
        ip_details = get_vlan_ip_details_from_device(device_ip, v_name).get(
            "openconfig-if-ip:ipv4", {}
        )
        ipv4_addresses = ip_details.get("addresses", {}).get("address", [])
        sag_ipv4_addresses = (
            ip_details.get("openconfig-interfaces-ext:sag-ipv4", {})
            .get("config", {})
            .get("static-anycast-gateway", [])
        )

        ipv4_addr = None
        for ipv4 in ipv4_addresses or []:
            if (ip := ipv4.get("config", {}).get("ip", "")) and (
                pfx := ipv4.get("config", {}).get("prefix-length", "")
            ):
                ipv4_addr = f"{ip}/{pfx}"
                break

        vlans.append(
            Vlan(
                vlanid=vlan.get("vlanid"),
                name=v_name,
                ip_address=ipv4_addr,
                sag_ip_address=sag_ipv4_addresses if sag_ipv4_addresses else None,
                autostate=vlan.get("autostate", str(VlanAutoState.disable)),
            )
        )

    for vlan in vlan_details.get("sonic-vlan:VLAN_TABLE_LIST") or []:
        for v in vlans or []:
            if v.name == vlan.get("name"):
                v.mtu = vlan.get("mtu")
                v.enabled = True if vlan.get("admin_status") == "up" else False
                v.oper_status = vlan.get("oper_status")
                v.autostate = vlan.get("autostate")
                v.description = vlan.get("description")

    vlans_obj_vs_mem = {}
    for v in vlans or []:
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


def del_vlan(device_ip, vlan_name: str):
    """
    Deletes a VLAN from a device.

    Args:
        device_ip (str): The IP address of the device.
        vlan_name (str): The name of the VLAN to be deleted.

    Returns:
        None
    """

    try:
        del_vlan_from_device(device_ip, vlan_name)
    except Exception as e:
        _logger.error(f"VLAN deletion failed on device {device_ip}, Reason: {e}")
        raise
    finally:
        discover_vlan(device_ip)
        discover_stp_vlan(device_ip)


def remove_ip_from_vlan(device_ip: str, vlan_name: str):
    """
    Removes an IP address from a VLAN on a specific device.

    Args:
        device_ip (str): The IP address of the device.
        vlan_name (str): The name of the VLAN.

    Raises:
        Exception: If there is an error while removing the IP address from the VLAN on the device.

    Returns:
        None
    """

    try:
        remove_ip_from_vlan_on_device(device_ip, vlan_name)
    except Exception as e:
        _logger.error(f"VLAN IP removal failed on device {device_ip}, Reason: {e}")
        raise
    finally:
        discover_vlan(device_ip)


def remove_anycast_ip_from_vlan(device_ip: str, vlan_name: str, anycast_ip: str):
    """
    Removes an anycast IP address from a VLAN on a specific device.

    Args:
        device_ip (str): The IP address of the device.
        vlan_name (str): The name of the VLAN.
        anycast_ip (str, optional): The anycast IP address to be removed from the VLAN. Defaults to None.

    Raises:
        Exception: If there is an error while removing the anycast IP address from the VLAN on the device.

    Returns:
        None
    """

    try:
        remove_anycast_addr_from_vlan_on_device(device_ip, vlan_name, anycast_ip)
    except Exception as e:
        _logger.error(
            f"VLAN Anycast IP removal failed on device {device_ip}, Reason: {e}"
        )
        raise
    finally:
        discover_vlan(device_ip)


def config_vlan(device_ip: str, vlan_name: str, **kwargs):
    """
    Configures a VLAN on a device.

    Args:
        device_ip (str): The IP address of the device.
        vlan_name (str): The name of the VLAN.
        **kwargs: Additional keyword arguments to be passed to the `config_vlan_on_device` function.

    Raises:
        Exception: If there is an error while configuring the VLAN on the device.

    Returns:
        None
    """
    try:
        config_vlan_on_device(device_ip=device_ip, vlan_name=vlan_name, **kwargs)
    except Exception as e:
        _logger.error(f"VLAN configuration failed on device {device_ip}, Reason: {e}")
        raise
    finally:
        discover_vlan(device_ip)


def add_vlan_mem(device_ip: str, vlan_name: str, mem_ifs: dict[str:IFMode]):
    """
    Adds VLAN members to a device.

    Args:
        device_ip (str): The IP address of the device.
        vlan_name (str): The name of the VLAN.
        mem_ifs (dict[str:IFMode]): A dictionary mapping interface names to their IFMode.

    Raises:
        Exception: If there is an error while adding VLAN members to the device.

    Returns:
        None
    """

    try:
        add_vlan_members_on_device(device_ip, vlan_name, mem_ifs)
    except Exception as e:
        _logger.error(f"VLAN member addition failed on device {device_ip}, Reason: {e}")
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
    mem_intf_vs_tagging_mode = {}

    member_ethernet = get_vlan_mem_ifcs_from_db(device_ip, vlan_name)
    for mem in member_ethernet or []:
        mem_rel = get_vlan_obj_from_db(
            device_ip, vlan_name
        ).memberInterfaces.relationship(mem)
        mem_intf_vs_tagging_mode[mem.name] = (
            IFMode.TRUNK if mem_rel.tagging_mode == "tagged" else IFMode.ACCESS
        )

    member_port_channel = get_vlan_member_port_channels_from_db(device_ip, vlan_name)
    for mem in member_port_channel or []:
        mem_rel = get_vlan_obj_from_db(
            device_ip, vlan_name
        ).memberPortChannel.relationship(mem)
        mem_intf_vs_tagging_mode[mem.lag_name] = (
            IFMode.TRUNK if mem_rel.tagging_mode == "tagged" else IFMode.ACCESS
        )

    return mem_intf_vs_tagging_mode


def del_vlan_mem(device_ip: str, vlan_name: str, if_name: str):
    """
    Deletes a VLAN member from a device.

    Args:
        device_ip (str): The IP address of the device.
        vlan_name (int): The ID of the VLAN.
        if_name (str): The name of the interface to be removed from the VLAN.
        if_mode (IFMode): The mode of the interface to be removed from the VLAN.

    Returns:
        None
    """

    try:
        delete_vlan_members_on_device(device_ip, vlan_name, if_name)
    except Exception as e:
        _logger.error(f"VLAN member deletion failed on device {device_ip}, Reason: {e}")
        raise
    finally:
        discover_vlan(device_ip)


def discover_vlan(device_ip: str = None):
    """
    Discovers VLANs on a network device.

    Args:
        device_ip (str, optional): The IP address of the device. Defaults to None.
        vlan_name (str, optional): The name of the VLAN. Defaults to None.

    Returns:
        None
    """

    _logger.info("Discovering VLAN.")
    devices = [get_device_db_obj(device_ip)] if device_ip else get_device_db_obj()
    for device in devices or []:
        try:
            _logger.info(f"Discovering VLAN on device {device}.")
            insert_vlan_in_db(device, _create_vlan_db_obj(device.mgt_ip))
        except Exception as e:
            _logger.error(f"VLAN Discovery Failed on device {device_ip}, Reason: {e}")
            raise
