from orca_nw_lib.common import IFMode
from orca_nw_lib.portgroup_gnmi import get_port_chnl_mem_base_path
from orca_nw_lib.utils import get_logging, validate_and_get_ip_prefix, format_and_get_trunk_vlans
from .gnmi_pb2 import Path, PathElem
from .gnmi_util import (
    create_gnmi_update,
    create_req_for_update,
    get_gnmi_del_req,
    get_gnmi_path,
    send_gnmi_get,
    send_gnmi_set,
    get_gnmi_del_reqs
)

_logger = get_logging().getLogger(__name__)


def get_port_chnl_root_path() -> Path:
    """
    Get the root path of the port channel configuration in the OpenConfig model.

    Returns:
        A Path object representing the root path of the port channel configuration.
    """
    return Path(
        target="openconfig",
        origin="sonic-portchannel",
        elem=[
            PathElem(name="sonic-portchannel"),
        ],
    )


def get_port_chnl_base_path() -> Path:
    """
    Return the base path for the port channel.

    Returns:
        Path: The base path for the port channel.
    """
    path = get_port_chnl_root_path()
    path.elem.append(PathElem(name="PORTCHANNEL"))
    return path


def get_port_chnl_list_path() -> Path:
    """
    Return the path to the port channel list.

    Returns:
        Path: The path to the port channel list.
    """
    path = get_port_chnl_base_path()
    path.elem.append(PathElem(name="PORTCHANNEL_LIST"))
    return path


def get_port_chnl_path(chnl_name: str = None):
    """
    Retrieves the path for a specific channel or the entire port channel list.

    Args:
        chnl_name (str, optional): The name of the channel. Defaults to None.

    Returns:
        Path: The path object representing the channel or the entire port channel list.
    """
    path = get_port_chnl_base_path()
    if chnl_name:
        path.elem.append(PathElem(name="PORTCHANNEL_LIST", key={"name": chnl_name}))
    else:
        path.elem.append(PathElem(name="PORTCHANNEL_LIST"))
    return path


def get_lag_member_table_list_path() -> Path:
    """
    Returns the path to the list of LAG member tables.

    Returns:
        Path: The path to the list of LAG member tables.
    """

    path = get_port_chnl_root_path()
    path.elem.append(PathElem(name="LAG_MEMBER_TABLE"))
    path.elem.append(PathElem(name="LAG_MEMBER_TABLE_LIST"))
    return path


def get_lag_table_list_path(chnl_name: str = None) -> Path:
    """
    Generates the path to the LAG table list based on the given channel name.

    Parameters:
        chnl_name (str, optional): The name of the channel. Defaults to None.

    Returns:
        Path: The path to the LAG table list.
    """
    path = get_port_chnl_root_path()
    path.elem.append(PathElem(name="LAG_TABLE"))

    if chnl_name:
        path.elem.append(PathElem(name="LAG_TABLE_LIST", key={"lagname": chnl_name}))
    else:
        path.elem.append(PathElem(name="LAG_TABLE_LIST"))

    return path


def del_all_port_chnl(device_ip: str):
    """
    Deletes all port channels on the specified device.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        The result of sending the GNMI delete request to remove all port channels on the device.
    """
    return send_gnmi_set(get_gnmi_del_req(get_port_chnl_list_path()), device_ip)


def get_port_chnl_from_device(device_ip: str, chnl_name: str):
    """
    Retrieves the port channel from the specified device using the device's IP address and the channel's name.

    Args:
        device_ip (str): The IP address of the device.
        chnl_name (str): The name of the channel.

    Returns:
        str: The port channel retrieved from the device.

    """
    return send_gnmi_get(device_ip, [get_port_chnl_path(chnl_name)])


def get_port_chnls_info_from_device(device_ip: str, chnl_name: str = None):
    """
    Retrieves port channel information from a device.

    Args:
        device_ip (str): The IP address of the device.
        chnl_name (str, optional): The name of the channel. Defaults to None.

    Returns:
        The port channel information retrieved from the device.
    """
    return send_gnmi_get(
        device_ip,
        [get_lag_member_table_list_path(), get_lag_table_list_path(chnl_name), get_port_chnl_path(chnl_name)],
    )


def get_lag_member_table_list(device_ip: str):
    """
    Retrieves the list of LAG (Link Aggregation Group) member table entries for a given device IP.

    Args:
        device_ip (str): The IP address of the device to retrieve the LAG member table from.

    Returns:
        The list of LAG member table entries retrieved from the device.

    Raises:
        Any exceptions that may occur during the retrieval process.
    """
    return send_gnmi_get(device_ip, [get_lag_member_table_list_path()])


def get_lag_table_list(device_ip: str, chnl_name: str = None):
    """
    Get the list of LAG tables for a given device IP and channel name.

    Args:
        device_ip (str): The IP address of the target device.
        chnl_name (str, optional): The name of the channel. Defaults to None.

    Returns:
        The list of LAG tables for the given device IP and channel name.
    """
    return send_gnmi_get(device_ip, [get_lag_table_list_path(chnl_name)])


def get_port_chnl_mem_list_path():
    """
    Generates the path for the 'PORTCHANNEL_MEMBER_LIST' element in the port channel
    channel memory list.

    Returns:
        The generated path for the 'PORTCHANNEL_MEMBER_LIST' element.
    """
    path = get_port_chnl_mem_base_path()
    path.elem.append(PathElem(name="PORTCHANNEL_MEMBER_LIST"))
    return path


def get_all_port_chnl_members(device_ip: str):
    """
    Retrieves all the members of a port channel on a given device.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        The list of members of the port channel.

    Raises:
        None.
    """
    return send_gnmi_get(device_ip, [get_port_chnl_mem_list_path()])


def get_port_chnl_mem_path(chnl_name: str, ifname: str):
    """
    Generate the path for a specific port channel member in the memory.

    Args:
        chnl_name (str): The name of the port channel.
        ifname (str): The name of the interface.

    Returns:
        Path: The generated path for the port channel member in the memory.
    """
    path = get_port_chnl_mem_base_path()
    path.elem.append(
        PathElem(
            name="PORTCHANNEL_MEMBER_LIST", key={"name": chnl_name, "ifname": ifname}
        )
    )
    return path


def remove_port_chnl_member(device_ip: str, chnl_name: str, ifname: str):
    """
    Remove a member from a port channel.

    Args:
        device_ip (str): The IP address of the target device.
        chnl_name (str): The name of the port channel.
        ifname (str): The interface name of the member to be removed.

    Returns:
        The result of sending a GNMI delete request to remove the member from the port channel.
    """
    return send_gnmi_set(
        get_gnmi_del_req(get_port_chnl_mem_path(chnl_name, ifname)), device_ip
    )


def del_port_chnl_from_device(device_ip: str, chnl_name: str = None):
    """
    Delete a port channel from a device.

    Args:
        device_ip (str): The IP address of the device.
        chnl_name (str, optional): The name of the channel to be deleted. Defaults to None.

    Returns:
        The response from the GNMI set request.

    """
    return send_gnmi_set(get_gnmi_del_req(get_port_chnl_path(chnl_name)), device_ip)


def add_port_chnl_member_on_device(device_ip: str, chnl_name: str, ifnames: list[str]):
    """
    Adds a member to a port channel on a device.

    Args:
        device_ip (str): The IP address of the device.
        chnl_name (str): The name of the port channel.
        ifnames (list[str]): A list of interface names to add to the port channel.

    Returns:
        str: The response from the send_gnmi_set function.
    """
    port_chnl_add = {"sonic-portchannel:PORTCHANNEL_MEMBER_LIST": []}
    for intf in ifnames:
        port_chnl_add.get("sonic-portchannel:PORTCHANNEL_MEMBER_LIST").append(
            {"ifname": intf, "name": chnl_name}
        )
    _logger.debug(f"Adding port channel member on device {device_ip} {port_chnl_add}")
    return send_gnmi_set(
        create_req_for_update(
            [create_gnmi_update(get_port_chnl_mem_list_path(), port_chnl_add)]
        ),
        device_ip,
    )


def add_port_chnl_on_device(
        device_ip: str, chnl_name: str, admin_status: str = None, mtu: int = None,
        static: bool = None, fallback: bool = None, fast_rate: bool = None,
        min_links: int = None, description: str = None, graceful_shutdown_mode: str = None,
        ip_addr_with_prefix: str = None,
):
    """
    Adds a port channel to a specific device.

    Args:
        device_ip (str): The IP address of the device.
        chnl_name (str): The name of the port channel.
        admin_status (str, optional): The administrative status of the port channel.
            Valid values are "up" and "down". Defaults to None.
        mtu (int, optional): The Maximum Transmission Unit (MTU) of the port channel.
            Defaults to None.
        static (bool, optional): Whether the port channel is static or not. Defaults to None.
        fallback (bool, optional): Whether the port channel is a fallback port channel. Defaults to None.
        fast_rate (bool, optional): Whether the port channel uses fast rate. Defaults to None.
        min_links (int, optional): The minimum number of links in the port channel. Defaults to None.
        description (str, optional): The description of the port channel. Defaults to None.
        graceful_shutdown_mode (bool, optional): Whether the port channel is in graceful shutdown mode. Defaults to None.
        ip_addr_with_prefix (str, optional): The IP address and prefix of the port channel. Defaults to None.

    Returns:
        str: The result of the GNMI set operation.

    """
    port_chnl_add = {"sonic-portchannel:PORTCHANNEL_LIST": []}
    port_chnl_item = {"name": chnl_name}
    if admin_status is not None and admin_status in ["up", "down"]:
        port_chnl_item["admin_status"] = admin_status
    if mtu is not None:
        port_chnl_item["mtu"] = mtu
    if static is not None:
        port_chnl_item["static"] = static
    if fallback is not None:
        port_chnl_item["fallback"] = fallback
    if fast_rate is not None:
        port_chnl_item["fast_rate"] = fast_rate
    if min_links is not None:
        port_chnl_item["min_links"] = min_links
    if description is not None:
        port_chnl_item["description"] = description
    if graceful_shutdown_mode is not None:
        port_chnl_item["graceful_shutdown_mode"] = graceful_shutdown_mode.upper()
    port_chnl_add.get("sonic-portchannel:PORTCHANNEL_LIST").append(port_chnl_item)
    requests = [create_gnmi_update(get_port_chnl_list_path(), port_chnl_add)]
    if ip_addr_with_prefix is not None:
        ip, nw_addr, prefix_len = validate_and_get_ip_prefix(ip_addr_with_prefix)
        requests.append(
            get_port_channel_ip_update_req(port_channel_name=chnl_name, ip_address=ip, prefix_length=prefix_len)
        )
    return send_gnmi_set(
        create_req_for_update(requests),
        device_ip,
    )


def get_port_channel_vlan_gnmi_update_req(vlan_id: int, port_channel_name: str, if_mode: IFMode):
    """
    Generates a GNMI update request for configuring VLAN settings on a port channel.

    Parameters:
        vlan_id (int): The VLAN ID to be configured.
        port_channel_name (str): The name of the port channel.
        if_mode (IFMode): The interface mode to set, either ACCESS or TRUNK.

    Returns:
        The GNMI update request for setting VLAN configuration on the specified port channel.
    """
    return create_gnmi_update(
        get_gnmi_path(
            f"/openconfig-interfaces:interfaces/interface[name={port_channel_name}]/openconfig-if-aggregate:aggregation/openconfig-vlan:switched-vlan/config"
        ),
        (
            {
                "openconfig-vlan:config": {
                    "interface-mode": str(if_mode),
                    "access-vlan": vlan_id,
                }
            }
            if if_mode == IFMode.ACCESS
            else {
                "openconfig-vlan:config": {
                    "interface-mode": str(if_mode),
                    "trunk-vlans": [vlan_id],
                }
            }
        ),
    )


def set_port_channel_vlan_on_device(
        device_ip: str, port_channel_name: str, if_mode: IFMode, vlan_id: int
):
    """
    Sets the VLAN configuration on a port channel for a specified device.

    Parameters:
        device_ip (str): The IP address of the device.
        port_channel_name (str): The name of the port channel.
        if_mode (IFMode): The interface mode to set, either ACCESS or TRUNK.
        vlan_id (int): The VLAN ID to be configured.

    Returns:
        The result of sending a GNMI set request for configuring the VLAN settings on the port channel.
    """

    return send_gnmi_set(
        create_req_for_update(
            [get_port_channel_vlan_gnmi_update_req(vlan_id, port_channel_name, if_mode)]
        ),
        device_ip,
    )


def add_port_chnl_valn_members_on_device(
        device_ip: str, chnl_name: str, if_mode: IFMode, vlan_ids: list[int]
):
    """
    Adds VLAN members to a port channel on a device.

    Parameters:
        device_ip (str): The IP address of the device.
        chnl_name (str): The name of the port channel.
        if_mode (IFMode): The interface mode to set, either ACCESS or TRUNK.
        vlan_ids (list[int]): The VLAN IDs to be added to the port channel.
    Returns:
        The result of sending a GNMI set request for adding VLAN members to the port channel.
    """
    req = create_port_channel_vlan_gnmi_update_req(
        device_ip=device_ip, port_channel_name=chnl_name, if_mode=if_mode, vlan_ids=vlan_ids
    )
    return send_gnmi_set(
        create_req_for_update(
            [req]
        ),
        device_ip,
    )


def get_port_channel_vlan_memebers_path(port_channel_name: str):
    """
    Returns the path for the VLAN members of a port channel.

    Parameters:
        port_channel_name (str): The name of the port channel.

    Returns:
        The path for the VLAN members of the specified port channel.

    """
    return get_gnmi_path(
        f"/openconfig-interfaces:interfaces/interface[name={port_channel_name}]/openconfig-if-aggregate:aggregation/openconfig-vlan:switched-vlan/config"
    )


def create_port_channel_vlan_gnmi_update_req(
        device_ip: str, port_channel_name: str, if_mode: IFMode, vlan_ids: list[int]
):
    """
    Creates a GNMI update request for configuring VLAN members on a port channel.

    Parameters:
        device_ip (str): The IP address of the device.
        port_channel_name (str): The name of the port channel.
        if_mode (IFMode): The interface mode to set, either ACCESS or TRUNK.
        vlan_ids (list[int]): The VLAN IDs to be added to the port channel.

    Returns:
        The GNMI update request for configuring VLAN members on the specified port channel.
    """
    if vlan_ids is None or len(vlan_ids) == 0:
        _logger.error(f"Invalid VLAN IDs: {vlan_ids}")
        raise ValueError(f"Invalid VLAN IDs: {vlan_ids}")
    if if_mode == IFMode.ACCESS:
        # Remove all existing VLANs before adding new ones.
        # This is necessary because updating an access VLAN requires the existing access VLAN to be deleted first.
        # Additionally, switching from trunk to access mode requires the deletion of trunk VLANs.

        delete_all_port_channel_member_vlan_from_device(device_ip, port_channel_name)
        # The access VLAN is always the first one because it only accepts integers.
        return create_req_to_add_access_vlan(
            port_channel_name=port_channel_name, vlan_id=vlan_ids[0]
        )
    elif if_mode == IFMode.TRUNK:
        return create_req_to_add_trunk_vlan(
            port_channel_name=port_channel_name, vlan_ids=vlan_ids
        )
    else:
        _logger.error(f"Invalid interface mode: {if_mode}")
        raise ValueError(f"Invalid interface mode: {if_mode}")


def create_req_to_add_trunk_vlan(port_channel_name: str, vlan_ids: list[int]):
    """
    Creates a GNMI update request to add trunk VLANs to a port channel.

    Args:
        port_channel_name (str): The name of the port channel.
        vlan_ids (list[int]): The list of VLAN IDs to be added as trunk VLANs.

    Returns:
        The GNMI update request for adding trunk VLANs to the port channel.
    """
    return create_gnmi_update(
        get_port_channel_vlan_memebers_path(port_channel_name=port_channel_name),
        {
            "openconfig-vlan:config": {
                "interface-mode": str(IFMode.TRUNK),
                "trunk-vlans": format_and_get_trunk_vlans(vlan_ids),
            }
        }
    )


def create_req_to_add_access_vlan(port_channel_name: str, vlan_id: int):
    """
    Creates a GNMI update request to add an access VLAN to a port channel.

    Args:
        port_channel_name (str): The name of the port channel.
        vlan_id (int): The VLAN ID to be added as an access VLAN.

    Returns:
        The GNMI update request for adding an access VLAN to the specified port channel.
    """
    return create_gnmi_update(
        get_port_channel_vlan_memebers_path(port_channel_name=port_channel_name),
        {
            "openconfig-vlan:config": {
                "interface-mode": str(IFMode.ACCESS),
                "access-vlan": vlan_id,
            }
        },
    )


def get_port_channel_vlan_members_from_device(device_ip: str, port_channel_name: str):
    """
    Retrieves the VLAN members of a port channel from the device.

    Parameters:
        device_ip (str): The IP address of the device.
        port_channel_name (str): The name of the port channel.

    Returns:
        The VLAN members of the specified port channel as a list of integers.
    """
    return send_gnmi_get(device_ip, [get_port_channel_vlan_memebers_path(port_channel_name=port_channel_name)])


def delete_port_channel_member_vlan_from_device(
        device_ip: str, port_channel_name: str, if_mode: IFMode, vlan_ids: list[int]
):
    """
    Deletes the VLAN members of a port channel from the device.

    Parameters:
        device_ip (str): The IP address of the device.
        port_channel_name (str): The name of the port channel.
        if_mode (IFMode): The interface mode to set, either ACCESS or TRUNK.
        vlan_ids (list[int]): The VLAN IDs to be deleted from the port channel.

    Returns:
        The result of sending a GNMI set request for deleting the VLAN members of the port channel.
    """
    paths = []
    if vlan_ids is None or len(vlan_ids) == 0:
        _logger.error(f"Invalid VLAN IDs: {vlan_ids}")
        raise ValueError(f"Invalid VLAN IDs: {vlan_ids}")
    if if_mode == IFMode.TRUNK:
        for i in format_and_get_trunk_vlans(vlan_ids):
            paths.append(
                get_gnmi_path(
                    f"openconfig-interfaces:interfaces/interface[name={port_channel_name}]/openconfig-if-aggregate:aggregation/openconfig-vlan:switched-vlan/config/trunk-vlans[trunk-vlans={i}]"
                )
            )
    elif if_mode == IFMode.ACCESS:
        paths.append(
            get_gnmi_path(
                f"openconfig-interfaces:interfaces/interface[name={port_channel_name}]/openconfig-if-aggregate:aggregation/openconfig-vlan:switched-vlan/config/access-vlan"
            )
        )
    else:
        _logger.error(f"Invalid interface mode: {if_mode}")
        raise ValueError(f"Invalid interface mode: {if_mode}")
    return send_gnmi_set(req=get_gnmi_del_reqs(paths), device_ip=device_ip) if paths else None


def delete_all_port_channel_member_vlan_from_device(device_ip: str, port_channel_name: str):
    """
    Deletes all VLAN members of a port channel from the device.

    Parameters:
        device_ip (str): The IP address of the device.
        port_channel_name (str): The name of the port channel.

    Returns:
        The result of sending a GNMI set request for deleting all VLAN members of the port channel.
    """
    path = get_port_channel_vlan_memebers_path(port_channel_name=port_channel_name)
    return send_gnmi_set(get_gnmi_del_req(path=path), device_ip=device_ip)


def get_port_channel_ip_path(port_channel_name: str):
    """
    Returns the path for the IP details of a port channel.

    Parameters:
        port_channel_name (str): The name of the port channel.

    Returns:
        The path for the IP details of the specified port channel.

    """
    return get_gnmi_path(
        f"/openconfig-interfaces:interfaces/interface[name={port_channel_name}]/subinterfaces/subinterface[index=0]/openconfig-if-ip:ipv4/addresses"
    )


def get_port_channel_ip_path_with_ip(port_channel_name: str, ip_address: str):
    """
    Returns the path for the IP details of a port channel with an IP address.

    Parameters:
        port_channel_name (str): The name of the port channel.
        ip_address (str): The IP address of the port channel.

    Returns:
        The path for the IP details of the specified port channel with the specified IP address.
    """
    return get_gnmi_path(
        f"/openconfig-interfaces:interfaces/interface[name={port_channel_name}]/subinterfaces/subinterface[index=0]/openconfig-if-ip:ipv4/addresses/address[ip={ip_address}]"
    )


def get_port_channel_ip_update_req(port_channel_name: str, ip_address: str, prefix_length: int):
    """
    Returns the update request for the IP details of a port channel.

    Parameters:
        port_channel_name (str): The name of the port channel.
        ip_address (str): The IP address of the port channel.
        prefix_length (int): The prefix length of the IP address.

    Returns:
        The GNMI update request for the IP details of the specified port channel.
    """
    path = get_port_channel_ip_path(port_channel_name=port_channel_name)
    return create_gnmi_update(
        path,
        {
            "openconfig-if-ip:addresses": {
                "address": [
                    {
                        "ip": ip_address,
                        "openconfig-if-ip:config": {"ip": ip_address, "prefix-length": prefix_length},
                    }
                ]
            }
        }
    )


def remove_port_channel_ip_from_device(device_ip: str, port_channel_name: str, ip_address: str = None):
    """
    Removes the IP details of a port channel from the device.

    Parameters:
        device_ip (str): The IP address of the device.
        port_channel_name (str): The name of the port channel.
        ip_address (str, optional): The IP address of the port channel. If not provided, the IP details of the port channel will be removed.

    Returns:
        The result of sending a GNMI set request for removing the IP details of the port channel.
    """
    if ip_address is None:
        path = get_port_channel_ip_path(port_channel_name=port_channel_name)
    else:
        ip, nw_addr, prefix_len = validate_and_get_ip_prefix(ip_address)
        path = get_port_channel_ip_path_with_ip(port_channel_name=port_channel_name, ip_address=ip)
    return send_gnmi_set(
        get_gnmi_del_req(path),
        device_ip
    )


def get_port_channel_ip_details_from_device(device_ip: str, port_channel_name: str):
    """
    Retrieves the IP details of a port channel from the device.

    Parameters:
        device_ip (str): The IP address of the device.
        port_channel_name (str): The name of the port channel.

    Returns:
        The IP details of the specified port channel as a dictionary.
    """
    return send_gnmi_get(
        device_ip=device_ip,
        path=[
            get_port_channel_ip_path(port_channel_name=port_channel_name)
        ],
    )
