from typing import List
from orca_nw_lib.common import IFMode, VlanAutoState
from orca_nw_lib.gnmi_pb2 import Path, PathElem
from orca_nw_lib.gnmi_util import (
    create_gnmi_update,
    create_req_for_update,
    get_gnmi_del_req,
    send_gnmi_get,
    send_gnmi_set,
    get_gnmi_path,
)
from orca_nw_lib.interface_gnmi import get_if_vlan_gnmi_update_req
from orca_nw_lib.port_chnl_gnmi import get_port_channel_vlan_gnmi_update_req
from .utils import validate_and_get_ip_prefix


def get_sonic_vlan_base_path() -> Path:
    """
    Generates a `Path` object for the sonic-vlan base path.

    Returns:
        Path: The `Path` object representing the sonic-vlan base path.
    """

    return Path(
        target="openconfig",
        origin="sonic-vlan",
        elem=[
            PathElem(
                name="sonic-vlan",
            )
        ],
    )


def get_vlan_table_list_path(vlan_name=None):
    """
    Generate the path for the VLAN table list in a Sonic switch.

    Args:
        vlan_name (str, optional): The name of the VLAN. Defaults to None.

    Returns:
        Path: The path for the VLAN table list.

    """
    path = get_sonic_vlan_base_path()
    path.elem.append(PathElem(name="VLAN_TABLE"))
    (
        path.elem.append(PathElem(name="VLAN_TABLE_LIST"))
        if not vlan_name
        else path.elem.append(PathElem(name="VLAN_TABLE_LIST", key={"name": vlan_name}))
    )
    return path


def get_vlan_mem_path(vlan_name: str = None, intf_name: str = None):
    """
    Generate the path for the VLAN member based on the VLAN name and interface name.

    Args:
        vlan_name (str, optional): The name of the VLAN. Defaults to None.
        intf_name (str, optional): The name of the interface. Defaults to None.

    Returns:
        Path: The generated path for the VLAN member.
    """

    path = get_sonic_vlan_base_path()
    path.elem.append(PathElem(name="VLAN_MEMBER"))
    (
        path.elem.append(PathElem(name="VLAN_MEMBER_LIST"))
        if not vlan_name or not intf_name
        else path.elem.append(
            PathElem(
                name="VLAN_MEMBER_LIST", key={"name": vlan_name, "ifname": intf_name}
            )
        )
    )
    return path


def get_vlan_list_path(vlan_list_name=None):
    """
    Generates the path to the VLAN list based on the given VLAN list name.

    Parameters:
        vlan_list_name (str): The name of the VLAN list. Defaults to None.

    Returns:
        path (Path): The path to the VLAN list.
    """
    path = get_sonic_vlan_base_path()
    path.elem.append(PathElem(name="VLAN"))
    (
        path.elem.append(PathElem(name="VLAN_LIST"))
        if not vlan_list_name
        else path.elem.append(PathElem(name="VLAN_LIST", key={"name": vlan_list_name}))
    )
    return path


def get_vlan_mem_tagging_path(vlan_name: str, intf_name: str):
    """
    Returns the path for VLAN tagging mode of a given VLAN and interface.

    Args:
        vlan_name (str): The name of the VLAN.
        intf_name (str): The name of the interface.

    Returns:
        Path: The path for VLAN tagging mode.
    """
    path = get_vlan_mem_path(vlan_name, intf_name)
    path.elem.append(PathElem(name="tagging_mode"))
    return path


def get_vlan_details_from_device(device_ip: str, vlan_name: str = None):
    """
    Retrieves VLAN details from a device.

    Args:
        device_ip (str): The IP address of the device.
        vlan_name (str, optional): The name of the VLAN. Defaults to None.

    Returns:
        The VLAN details retrieved from the device.

    Raises:
        None
    """
    return send_gnmi_get(
        device_ip=device_ip,
        path=[
            get_vlan_list_path(vlan_name),
            get_vlan_table_list_path(vlan_name),
            get_vlan_mem_path(),
        ],
    )


def get_vlan_ip_details_from_device(device_ip: str, vlan_name: str):
    return send_gnmi_get(
        device_ip=device_ip,
        path=[
            get_gnmi_path(
                f"/openconfig-interfaces:interfaces/interface[name={vlan_name}]/openconfig-vlan:routed-vlan/openconfig-if-ip:ipv4",
            )
        ],
    )


def del_vlan_from_device(device_ip: str, vlan_name: str):
    return send_gnmi_set(
        get_gnmi_del_req(
            get_gnmi_path(
                f"/openconfig-interfaces:interfaces/interface[name={vlan_name}]"
            )
        ),
        device_ip,
    )


def config_vlan_on_device(
    device_ip: str,
    vlan_name: str,
    autostate: VlanAutoState = None,
    ip_addr_with_prefix: str = None,
    anycast_addr: List[str] = None,
    enabled: bool = None,
    descr: str = None,
    mem_ifs: dict[str:IFMode] = None,
    mtu: int = None,
):
    """
    Configures a VLAN on a network device.

    Args:
        device_ip (str): The IP address of the device.
        vlan_name (str): The name of the VLAN.
        vlan_id (int): The ID of the VLAN.
        autostate (VlanAutoState, optional): The autostate of the VLAN. Defaults to None.
        ip_addr_with_prefix (str, optional): The IP address with prefix of the VLAN. Defaults to None.
        anycast_addr (List[str], optional): The anycast address of the VLAN. Defaults to None.
        enabled (bool, optional): Whether the VLAN is enabled. Defaults to None.
        descr (str, optional): The description of the VLAN. Defaults to None.
        mem_ifs (dict[str:IFMode], optional): A dictionary mapping interface names to VLAN tag modes. Defaults to None.
        mtu (int, optional): The MTU of the VLAN. Defaults to None.

    Returns:
        The result of the GNMI set operation.
    """
    update_req = []
    update_req.append(
        create_gnmi_update(
            get_gnmi_path("openconfig-interfaces:interfaces"),
            {
                "openconfig-interfaces:interfaces": {
                    "interface": [{"name": vlan_name, "config": {"name": vlan_name}}]
                }
            },
        )
    )

    if enabled is not None:
        update_req.append(
            create_gnmi_update(
                get_gnmi_path(
                    f"openconfig-interfaces:interfaces/interface[name={vlan_name}]/config/enabled",
                ),
                {"openconfig-interfaces:enabled": enabled},
            )
        )
    if descr is not None:
        update_req.append(
            create_gnmi_update(
                get_gnmi_path(
                    f"openconfig-interfaces:interfaces/interface[name={vlan_name}]/config/description",
                ),
                {"openconfig-interfaces:description": descr},
            )
        )
    if mtu:
        update_req.append(
            create_gnmi_update(
                get_gnmi_path(
                    f"openconfig-interfaces:interfaces/interface[name={vlan_name}]/config/mtu",
                ),
                {"openconfig-interfaces:mtu": mtu},
            )
        )

    if ip_addr_with_prefix:
        ip, nw_addr, prefix_len = validate_and_get_ip_prefix(ip_addr_with_prefix)
        if ip and prefix_len:
            update_req.append(
                create_gnmi_update(
                    get_gnmi_path(
                        f"/openconfig-interfaces:interfaces/interface[name={vlan_name}]/openconfig-vlan:routed-vlan/openconfig-if-ip:ipv4/addresses",
                    ),
                    {
                        "openconfig-if-ip:addresses": {
                            "address": [
                                {
                                    "ip": ip,
                                    "openconfig-if-ip:config": {
                                        "ip": ip,
                                        "prefix-length": prefix_len,
                                    },
                                }
                            ]
                        }
                    },
                )
            )

    if autostate:
        update_req.append(
            create_gnmi_update(
                get_gnmi_path(
                    f"/sonic-vlan:sonic-vlan/VLAN/VLAN_LIST[name={vlan_name}]/autostate",
                ),
                {"sonic-vlan:autostate": str(autostate)},
            )
        )
    if mem_ifs:
        ## add an array to update_req returned by get_add_vlan_mem_req()
        update_req.append(get_add_vlan_member_request(vlan_name, mem_ifs))

    if anycast_addr:
        sag_gateway_array = []
        for addr in anycast_addr:
            ip, nw_addr, prefix_len = validate_and_get_ip_prefix(addr)
            sag_gateway_array.append(f"{ip}/{prefix_len}")
        if sag_gateway_array:
            update_req.append(
                create_gnmi_update(
                    get_gnmi_path(
                        f"openconfig-interfaces:interfaces/interface[name={vlan_name}]/openconfig-vlan:routed-vlan/openconfig-if-ip:ipv4/openconfig-interfaces-ext:sag-ipv4/config/static-anycast-gateway"
                    ),
                    {
                        "openconfig-interfaces-ext:static-anycast-gateway": sag_gateway_array
                    },
                )
            )

    return send_gnmi_set(
        create_req_for_update(update_req),
        device_ip,
    )


def set_ip_addr_on_vlan_on_device(
    device_ip: str, vlan_name: str, ip_addr_with_prefix: str
):
    ip, nw_addr, prefix_len = validate_and_get_ip_prefix(ip_addr_with_prefix)
    return send_gnmi_set(
        create_req_for_update(
            [
                create_gnmi_update(
                    get_gnmi_path(
                        f"/openconfig-interfaces:interfaces/interface[name={vlan_name}]/openconfig-vlan:routed-vlan/openconfig-if-ip:ipv4/addresses",
                    ),
                    {
                        "openconfig-if-ip:addresses": {
                            "address": [
                                {
                                    "ip": ip,
                                    "openconfig-if-ip:config": {
                                        "ip": ip,
                                        "prefix-length": prefix_len,
                                    },
                                }
                            ]
                        }
                    },
                )
            ]
        ),
        device_ip,
    )


def get_add_vlan_mem_req(vlan_id: int, mem_ifs: dict[str:IFMode]):
    """
    Generates a list of GNMI updates for adding VLAN member interfaces.

    Args:
        vlan_id (int): The ID of the VLAN.
        mem_ifs (dict[str:IFMode]): A dictionary mapping interface names to their mode.

    Returns:
        list: A list of GNMI updates for adding VLAN member interfaces.
    """
    req = []
    for if_name, if_mode in mem_ifs.items():
        if "portchannel" in if_name.lower():
            req.append(get_port_channel_vlan_gnmi_update_req(vlan_id, if_name, if_mode))
        else:
            req.append(get_if_vlan_gnmi_update_req(vlan_id, if_name, if_mode))
    return req


def add_vlan_mem_interface_on_device(
    device_ip: str, vlan_id: int, mem_ifs: dict[str:IFMode]
):
    """
    Adds a VLAN member interface on a device using the specified device IP, VLAN ID, and member interfaces dictionary.

    Args:
        device_ip (str): The IP address of the device.
        vlan_id (int): The ID of the VLAN.
        mem_ifs (dict[str:IFMode]): A dictionary mapping interface names to their mode.

    Returns:
        The result of sending a GNMI set request to add the VLAN member interface.
    """
    return send_gnmi_set(
        create_req_for_update(get_add_vlan_mem_req(vlan_id, mem_ifs)),
        device_ip,
    )


def del_vlan_mem_interface_on_device(
    device_ip: str, vlan_id: int, if_name: str, if_mode: IFMode
):
    """
    Deletes a VLAN member interface on a device using the specified device IP, VLAN ID, interface name, and interface mode.

    Args:
        device_ip (str): The IP address of the device.
        vlan_id (int): The ID of the VLAN.
        if_name (str): The name of the interface to be removed from the VLAN.
        if_mode (IFMode): The mode of the interface to be removed from the VLAN.

    Returns:
        Result of sending a GNMI set request to delete the VLAN member interface.
    """

    return send_gnmi_set(
        get_gnmi_del_req(
            get_gnmi_path(
                f"openconfig-interfaces:interfaces/interface[name={if_name}]/openconfig-if-ethernet:ethernet/openconfig-vlan:switched-vlan/config/trunk-vlans[trunk-vlans={vlan_id}]"
                if if_mode == IFMode.TRUNK
                else f"openconfig-interfaces:interfaces/interface[name={if_name}]/openconfig-if-ethernet:ethernet/openconfig-vlan:switched-vlan/config/access-vlan"
            )
            if "ethernet" in if_name.lower()  ## Its a port channel
            else get_gnmi_path(
                f"openconfig-interfaces:interfaces/interface[name={if_name}]/openconfig-if-aggregate:aggregation/openconfig-vlan:switched-vlan/config/trunk-vlans[trunk-vlans={vlan_id}]"
                if if_mode == IFMode.TRUNK
                else f"openconfig-interfaces:interfaces/interface[name={if_name}]/openconfig-if-aggregate:aggregation/openconfig-vlan:switched-vlan/config/access-vlan"
            )
        ),
        device_ip,
    )


def vlan_ip_addr_oc_path(vlan_name, ip_addr=None):
    return (
        f"/openconfig-interfaces:interfaces/interface[name={vlan_name}]/openconfig-vlan:routed-vlan/openconfig-if-ip:ipv4/addresses/address[ip={ip_addr}]"
        if ip_addr
        else f"/openconfig-interfaces:interfaces/interface[name={vlan_name}]/openconfig-vlan:routed-vlan/openconfig-if-ip:ipv4/addresses/address"
    )


def remove_ip_from_vlan_on_device(device_ip: str, vlan_name: str):
    """
    Removes an IP address with prefix from a VLAN on a specific device.

    Args:
        device_ip (str): The IP address of the device.
        vlan_name (str): The name of the VLAN.
        ip_addr_with_prefix (str): The IP address with prefix to be removed from the VLAN.

    Returns:
        Result of sending a GNMI set request to remove the IP address from the VLAN on the device.
    """
    return send_gnmi_set(
        get_gnmi_del_req(get_gnmi_path(vlan_ip_addr_oc_path(vlan_name))),
        device_ip,
    )


def remove_anycast_addr_from_vlan_on_device(
    device_ip: str, vlan_name: str, anycast_ip: str
):
    """
    Removes an anycast IP address from a VLAN on a specific device.

    Args:
        device_ip (str): The IP address of the device.
        vlan_name (str): The name of the VLAN.
        anycast_ip (str): The anycast IP address to be removed from the VLAN.

    Returns:
        The result of sending a GNMI set request to remove the anycast IP address from the VLAN on the device.
    """
    path = get_gnmi_path(
        f"openconfig-interfaces:interfaces/interface[name={vlan_name}]/openconfig-vlan:routed-vlan/openconfig-if-ip:ipv4/openconfig-interfaces-ext:sag-ipv4/config"
    )
    path.elem.append(
        PathElem(
            name="static-anycast-gateway", key={"static-anycast-gateway": anycast_ip}
        )
    )
    return send_gnmi_set(
        get_gnmi_del_req(path),
        device_ip,
    )


def add_vlan_members_on_device(device_ip: str, vlan_name: str, mem_ifs: dict):
    """
    Adds VLAN members on a specific device.

    Args:
        device_ip (str): The IP address of the device.
        vlan_name (str): The name of the VLAN.
        mem_ifs (dict[str:IFMode]): A dictionary mapping interface names to their mode.

    Returns:
        The result of sending a GNMI set request to add the VLAN members on the device.
    """
    return send_gnmi_set(
        create_req_for_update(get_add_vlan_member_request(vlan_name, mem_ifs)),
        device_ip,
    )


def get_add_vlan_member_request(vlan_name: str, mem_ifs: dict):
    """
    Generates a list of GNMI updates for adding VLAN member interfaces.

    Args:
        vlan_name (str): The name of the VLAN.
        mem_ifs (dict[str:IFMode]): A dictionary mapping interface names to their mode.

    Returns:
        list: A list of GNMI updates for adding VLAN member interfaces.
    """
    req = []
    for if_name, if_mode in mem_ifs.items():
        req.append(
            {
                "name": vlan_name,
                "ifname": if_name,
                "tagging_mode": "tagged" if if_mode == IFMode.TRUNK else "untagged",
            }
        )
    path = get_gnmi_path("sonic-vlan:sonic-vlan/VLAN_MEMBER/VLAN_MEMBER_LIST")
    return create_gnmi_update(path, {"sonic-vlan:VLAN_MEMBER_LIST": req})


def delete_vlan_members_on_device(device_ip: str, vlan_name: str, intf_name: str):
    """
    Deletes VLAN members on a specific device.

    Args:
        device_ip (str): The IP address of the device.
        vlan_name (str): The name of the VLAN.
        intf_name (str): The name of the interface to be deleted from the VLAN.

    Returns:
        The result of sending a GNMI set request to delete the VLAN members on the device.
    """
    path = get_vlan_mem_path(vlan_name, intf_name=intf_name)
    return send_gnmi_set(get_gnmi_del_req(path=path), device_ip)
