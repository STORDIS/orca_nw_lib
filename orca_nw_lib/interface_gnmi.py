from urllib.parse import quote_plus

from orca_nw_lib.utils import validate_and_get_ip_prefix

from .common import IFMode, PortFec, Speed
from .gnmi_pb2 import Path, PathElem
from .interface_db import get_all_interfaces_name_of_device_from_db
from .gnmi_util import (
    create_gnmi_update,
    create_req_for_update,
    get_gnmi_del_req,
    get_gnmi_path,
    send_gnmi_get,
    send_gnmi_set,
    get_logging,
)
import orca_nw_lib.portgroup_db
import orca_nw_lib.portgroup_gnmi
from .utils import get_number_of_breakouts_and_speed, get_if_alias

_logger = get_logging().getLogger(__name__)


def get_interface_base_path():
    """
    Generates the base path for the interface in the OpenConfig format.

    Returns:
        Path: The base path for the interface in the OpenConfig format.
    """
    return Path(
        target="openconfig",
        elem=[
            PathElem(
                name="openconfig-interfaces:interfaces",
            )
        ],
    )


def get_sub_interface_base_path(intfc_name: str):
    """
    Get the base path for the sub-interface of a given interface.

    Args:
        intfc_name (str): The name of the interface.

    Returns:
        Path: The base path for the sub-interface.

    Raises:
        None

    Examples:
        >>> get_sub_interface_base_path("Ethernet0")
        <Path object at 0x7f8b4a00>

    Note:
        This function assumes that the interface exists and is valid.
    """
    path = get_interface_path(intfc_name)
    path.elem.append(PathElem(name="subinterfaces"))
    return path


def get_sub_interface_path(intfc_name: str):
    """
    Generates the path for a sub-interface based on the given interface name.

    Args:
        intfc_name (str): The name of the interface.

    Returns:
        path (Path): The path for the sub-interface.

    """
    path = get_sub_interface_base_path(intfc_name)
    path.elem.append(PathElem(name="subinterface"))
    return path


def get_sub_interface_index_path(intfc_name: str, index: int):
    """
    Get the path for the sub-interface with the specified index.

    Parameters:
        intfc_name (str): The name of the interface.
        index (int): The index of the sub-interface.

    Returns:
        Path: The path for the sub-interface.
    """
    path = get_sub_interface_base_path(intfc_name)
    path.elem.append(PathElem(name="subinterface", key={"index": str(index)}))
    return path


def get_interface_path(intfc_name: str = None):
    """
    Get the path of an interface.

    Args:
        intfc_name (str, optional): The name of the interface. Defaults to None.

    Returns:
        Path: The path of the interface.
    """

    path = get_interface_base_path()
    path.elem.append(
        PathElem(name="interface", key={"name": intfc_name})
        if intfc_name
        else PathElem(name="interface")
    )
    return path


def get_interface_counters_path(intfc_name: str):
    """
    Generates the path to the counters for a given interface.

    Args:
        intfc_name (str): The name of the interface.

    Returns:
        Path: The path to the counters.
    """
    path = get_interface_path(intfc_name)
    path.elem.append(PathElem(name="state"))
    path.elem.append(PathElem(name="counters"))
    return path


def get_intfc_config_path(intfc_name: str):
    """
    Generates the path to the config file for a given interface.

    Args:
        intfc_name (str): The name of the interface.

    Returns:
        Path: The path to the config file.
    """
    path = get_interface_path(intfc_name)
    path.elem.append(PathElem(name="config"))
    return path


def get_oc_ethernet_config_path(intfc_name: str):
    """
    Generates the path to the oc ethernet config for a given interface.

    Args:
        intfc_name (str): The name of the interface.

    Returns:
        Path: The path to the config file.
    """
    path = get_interface_path(intfc_name)
    path.elem.append(PathElem(name="openconfig-if-ethernet:ethernet"))
    path.elem.append(PathElem(name="config"))
    return path


def get_intfc_speed_path(intfc_name: str):
    """
    Generates the path to retrieve the interface speed for a given interface.

    Args:
        intfc_name (str): The name of the interface.

    Returns:
        Path: The path to retrieve the interface speed.
    """
    path = get_oc_ethernet_config_path(intfc_name)
    path.elem.append(PathElem(name="port-speed"))
    return path


def get_port_fec_path(intfc_name: str):
    """
    Generates the path to retrieve the interface fec for a given interface.

    Args:
        intfc_name (str): The name of the interface.

    Returns:
        Path: The path to retrieve the interface fec.
    """
    path = get_oc_ethernet_config_path(intfc_name)
    path.elem.append(PathElem(name="openconfig-if-ethernet-ext2:port-fec"))
    return path


def get_intfc_enabled_path(intfc_name: str):
    """
    Get the enabled path for a given interface.

    Args:
        intfc_name (str): The name of the interface.

    Returns:
        Path: The enabled path for the specified interface.
    """
    path = get_intfc_config_path(intfc_name)
    path.elem.append(PathElem(name="enabled"))
    return path


def get_intfc_mtu_path(intfc_name: str):
    """
    Retrieves the interface MTU path for the specified interface name.

    Args:
        intfc_name (str): The name of the interface.

    Returns:
        Path: The interface MTU path.
    """
    path = get_intfc_config_path(intfc_name)
    path.elem.append(PathElem(name="mtu"))
    return path


def get_intfc_description_path(intfc_name: str):
    """
    Retrieves the interface description path for the specified interface name.

    Args:
        intfc_name (str): The name of the interface.

    Returns:
        Path: The interface description path.
    """
    path = get_intfc_config_path(intfc_name)
    path.elem.append(PathElem(name="description"))
    return path


def set_interface_config_on_device(
    device_ip: str,
    if_name: str,
    enable: bool = None,
    mtu: int = None,
    description: str = None,
    speed: Speed = None,
    ip_with_prefix: str = None,
    index: int = 0,
    fec: PortFec = None,
    if_mode: IFMode = None,
    vlan_id: int = None,
    autoneg: bool = None,
    adv_speeds: str = None,
    link_training: bool = None,
    secondary: bool = False,
):
    """
    Set the interface configuration on a device.

    Args:
        device_ip (str): The IP address of the device.
        if_name (str): The name of the interface.
        enable (bool, optional): Whether to enable the interface. Defaults to None.
        mtu (int, optional): The maximum transmission unit (MTU) size. Defaults to None.
        description (str, optional): The interface description. Defaults to None.
        speed (Speed, optional): The interface speed. Defaults to None.
        ip_with_prefix (str, optional): The IP address with prefix. Defaults to None.
        index (int, optional): The index of the subinterface. Defaults to 0.
        fec (bool, optional): Whether to enable forward error correction. Defaults to None.
        if_mode (IFMode, optional): The interface mode. Defaults to None.
        vlan_id (int, optional): The VLAN ID of the interface. Defaults to None.
        autoneg (bool, optional): Whether to enable auto-negotiation. Defaults to None.
        adv_speeds (str, optional): The list of advertised speeds. Defaults to "all".
        link_training (bool, optional): Whether to enable link training. Defaults to None.

    Returns:
        None: If no updates were made.
        str: The response from sending the GNMI set request.
port-fec
    """
    updates = []

    if enable is not None:
        updates.append(
            create_gnmi_update(
                get_intfc_enabled_path(if_name),
                {"openconfig-interfaces:enabled": enable},
            )
        )

    if fec is not None:
        updates.append(
            create_gnmi_update(
                get_port_fec_path(if_name),
                {"openconfig-if-ethernet-ext2:port-fec": str(fec)},
            )
        )

    if mtu is not None:
        base_config_path = get_intfc_mtu_path(if_name)
        updates.append(
            create_gnmi_update(
                base_config_path,
                {"openconfig-interfaces:mtu": mtu},
            )
        )

    if description is not None:
        base_config_path = get_intfc_description_path(if_name)
        updates.append(
            create_gnmi_update(
                base_config_path,
                {"openconfig-interfaces:description": description},
            )
        )

    if speed is not None:
        # if switch supports port groups then configure speed on port-group otherwise directly on interface
        if pg_id := orca_nw_lib.portgroup_db.get_port_group_id_of_device_interface_from_db(
            device_ip, if_name
        ):
            _logger.debug(
                "Interface %s belongs to port-group %s. Speed of port-group will be updated for device_ip: %s, pg_id: %s, speed: %s.",
                if_name,
                pg_id,
                device_ip,
                pg_id,
                speed.get_oc_val(),
            )
            updates.append(
                create_gnmi_update(
                    orca_nw_lib.portgroup_gnmi.get_port_group_speed_path(pg_id),
                    {"openconfig-port-group:speed": speed.get_oc_val()},
                )
            )

        else:
            _logger.debug(
                "Interface does not belong to port-group. Speed of interface will be updated for device_ip: %s, interface_name: %s, speed: %s.",
                device_ip,
                if_name,
                speed.get_oc_val(),
            )
            updates.append(
                create_gnmi_update(
                    get_intfc_speed_path(if_name),
                    {"port-speed": speed.get_oc_val()},
                )
            )
    if ip_with_prefix is not None:
        ip, nw_addr, prefix_len = validate_and_get_ip_prefix(ip_with_prefix)
        if ip is not None:
            ip_payload = {
                "openconfig-interfaces:subinterface": [
                    {
                        "config": {"index": index},
                        "index": index,
                        "openconfig-if-ip:ipv4": {
                            "addresses": {
                                "address": [
                                    {
                                        "ip": ip,
                                        "config": {
                                            "prefix-length": prefix_len,
                                            "secondary": secondary,
                                        },
                                    }
                                ]
                            }
                        },
                    }
                ]
            }
            updates.append(
                create_gnmi_update(
                    get_sub_interface_path(if_name),
                    ip_payload,
                )
            )
    if if_mode and vlan_id:
        updates.append(get_if_vlan_gnmi_update_req(vlan_id, if_name, if_mode))
    if autoneg is not None:
        payload = {
            "openconfig-if-ethernet:config": {
                "auto-negotiate": autoneg,
            }
        }
        updates.append(
            create_gnmi_update(
                get_gnmi_path(f"openconfig-interfaces:interfaces/interface[name={if_name}]/openconfig-if-ethernet:ethernet/config"),
                payload
            )
        )
    if adv_speeds is not None:
        payload = {
            "openconfig-if-ethernet:config": {
                "advertised-speed": adv_speeds,
            }
        }
        updates.append(
            create_gnmi_update(
                get_gnmi_path(f"openconfig-interfaces:interfaces/interface[name={if_name}]/openconfig-if-ethernet:ethernet/config"),
                payload
            )
        )
    if link_training is not None:
        payload = {
            "openconfig-if-ethernet:config": {
                "standalone-link-training": link_training,
            }
        }
        updates.append(
            create_gnmi_update(
                get_gnmi_path(f"openconfig-interfaces:interfaces/interface[name={if_name}]/openconfig-if-ethernet:ethernet/config"),
                payload
            )
        )
    if updates:
        return send_gnmi_set(
            create_req_for_update(updates),
            device_ip,
        )

    else:
        return None


def get_interface_from_device(device_ip: str, intfc_name: str = None):
    """
    Retrieves all interfaces from a device.

    Args:
        device_ip (str): The IP address of the device.
        intfc_name (str, optional): The name of the interface to retrieve. Defaults to None.

    Returns:
        The result of the GNMI get operation for the specified device and interface.
    """

    return send_gnmi_get(
        device_ip=device_ip,
        path=[
            get_interface_path(intfc_name),
            ## Additional path for getting lane details
            get_gnmi_path(
                f"sonic-port:sonic-port/PORT/PORT_LIST[ifname={intfc_name}]"
                if intfc_name
                else "sonic-port:sonic-port/PORT/PORT_LIST"
            ),
        ],
    )


def get_interface_config_from_device(device_ip: str, intfc_name: str):
    """
    Retrieves the interface configuration from the specified device.

    Args:
        device_ip (str): The IP address of the device.
        intfc_name (str): The name of the interface.

    Returns:
        The interface configuration retrieved from the device.

    Example:
        >>> get_interface_config_from_device("192.168.1.1", "Ethernet0")
    """
    return send_gnmi_get(device_ip=device_ip, path=[get_intfc_config_path(intfc_name)])


def get_interface_speed_from_device(device_ip: str, intfc_name: str):
    """
    Retrieves the interface speed from a specified device and interface.

    Args:
        device_ip (str): The IP address of the device.
        intfc_name (str): The name of the interface.

    Returns:
        The interface speed as a string.
    """
    return send_gnmi_get(device_ip=device_ip, path=[get_intfc_speed_path(intfc_name)])


def get_interface_status_from_device(device_ip: str, intfc_name: str):
    """
    Retrieves the interface status from a specified device and interface.

    Args:
        device_ip (str): The IP address of the device.
        intfc_name (str): The name of the interface.

    Returns:
        The interface status as a string.
    """
    return send_gnmi_get(device_ip=device_ip, path=[get_intfc_enabled_path(intfc_name)])


def get_all_subinterfaces_of_interface_from_device(device_ip: str, if_name: str):
    """
    Retrieves all subinterfaces of a specified interface from a specified device.

    Args:
        device_ip (str): The IP address of the device.
        if_name (str): The name of the interface.

    Returns:
        The subinterfaces of the interface retrieved from the device.
    """

    return send_gnmi_get(device_ip=device_ip, path=[get_sub_interface_path(if_name)])


def del_all_subinterfaces_of_interface_from_device(device_ip: str, if_name: str):
    """
    Deletes all subinterfaces of a specified interface from a specified device.

    Args:
        device_ip (str): The IP address of the device.
        if_name (str): The name of the interface.

    Returns:
        The result of the delete operation.
    """

    return send_gnmi_set(get_gnmi_del_req(get_sub_interface_path(if_name)), device_ip)


def del_all_subinterfaces_of_all_interfaces_from_device(device_ip: str):
    """
    Deletes all subinterfaces of all interfaces from a specified device.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        The result of the delete operation.
    """
    for ether in get_all_interfaces_name_of_device_from_db(device_ip):
        del_all_subinterfaces_of_interface_from_device(device_ip, ether)


def del_subinterface_of_interface_from_device(device_ip: str, if_name: str, index: int):
    """
    Deletes a subinterface of a specified interface from a specified device.

    Args:
        device_ip (str): The IP address of the device.
        if_name (str): The name of the interface.
        index (int): The index of the subinterface.

    Returns:
        The result of the delete operation.
    """

    return send_gnmi_set(
        get_gnmi_del_req(get_sub_interface_index_path(if_name, index)), device_ip
    )


def get_subinterface_from_device(device_ip: str, if_name: str, index: int):
    """
    Retrieves a subinterface of a specified interface from a specified device.

    Args:
        device_ip (str): The IP address of the device.
        if_name (str): The name of the interface.
        index (int): The index of the subinterface.

    Returns:
        The subinterface retrieved from the device.
    """

    return send_gnmi_get(
        device_ip=device_ip, path=[get_sub_interface_index_path(if_name, index)]
    )


def get_all_subinterfaces_from_device(device_ip: str, intfc_name: str):
    """
    Retrieves all subinterfaces from a device.

    Args:
        device_ip (str): The IP address of the device.
        intfc_name (str): The name of the interface.

    Returns:
        The result of the GNMI get operation for the subinterface path.
    """

    return send_gnmi_get(device_ip=device_ip, path=[get_sub_interface_path(intfc_name)])


def remove_vlan_from_if_from_device(
    device_ip: str, intfc_name: str, if_mode: IFMode = None
):
    """
    Removes the interface mode from a device.

    Args:
        device_ip (str): The IP address of the device.
        intfc_name (str): The name of the interface.
        if_mode (IFMode): The interface mode. Defaults to None. When None is passed, All the trunk and access VLANs are removed from Interface.

    Returns:
        The result of the gNMI delete operation.
    """
    path = None
    if if_mode == IFMode.ACCESS:
        path = get_gnmi_path(
            f"/openconfig-interfaces:interfaces/interface[name={intfc_name}]/openconfig-if-ethernet:ethernet/openconfig-vlan:switched-vlan/config/access-vlan"
        )
    elif if_mode == IFMode.TRUNK:
        path = get_gnmi_path(
            f"/openconfig-interfaces:interfaces/interface[name={intfc_name}]/openconfig-if-ethernet:ethernet/openconfig-vlan:switched-vlan/config/trunk-vlans"
        )
    else:
        path = get_gnmi_path(
            f"/openconfig-interfaces:interfaces/interface[name={intfc_name}]/openconfig-if-ethernet:ethernet/openconfig-vlan:switched-vlan"
        )

    return send_gnmi_set(
        get_gnmi_del_req(path),
        device_ip,
    )


def get_if_mode_from_device(device_ip: str, intfc_name: str):
    """
    Retrieves the interface mode from a device.

    Args:
        device_ip (str): The IP address of the device.
        intfc_name (str): The name of the interface.

    Returns:
        The interface mode as a string.
    """

    return send_gnmi_get(
        device_ip=device_ip,
        path=[
            get_gnmi_path(
                f"/openconfig-interfaces:interfaces/interface[name={intfc_name}]/openconfig-if-ethernet:ethernet/openconfig-vlan:switched-vlan/config/interface-mode"
            )
        ],
    )


def get_if_vlan_gnmi_update_req(vlan_id: int, if_name: str, if_mode: IFMode):
    """
    Creates a GNMI update request for the interface mode.

    Args:
        vlan_id (int): The VLAN ID.
        if_name (str): The name of the interface.
        if_mode (IFMode): The interface mode.

    Returns:
        The GNMI update request.
    """

    return create_gnmi_update(
        get_gnmi_path(
            f"openconfig-interfaces:interfaces/interface[name={if_name}]/openconfig-if-ethernet:ethernet/openconfig-vlan:switched-vlan/config"
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


def set_if_vlan_on_device(device_ip: str, if_name: str, if_mode: IFMode, vlan_id: int):
    """
    Sets the interface mode on a device.

    Args:
        device_ip (str): The IP address of the device.
        if_name (str): The name of the interface.
        if_mode (IFMode): The interface mode.
        vlan_id (int): The VLAN ID.

    Returns:
        The result of the GNMI set operation.
    """

    return send_gnmi_set(
        create_req_for_update([get_if_vlan_gnmi_update_req(vlan_id, if_name, if_mode)]),
        device_ip,
    )


def get_breakout_path(if_alias):
    """
    Returns the GNMI path for the breakout configuration.

    Args:
        if_alias (str): The alias of the interface.

    Returns:
        The GNMI path for the breakout configuration.
    """
    return get_gnmi_path(
        f"openconfig-platform:components/component[name={quote_plus(if_alias)}]/port/openconfig-platform-port:breakout-mode/groups"
    )


def get_breakout_sonic_path(if_name: str):
    """
    Returns the SONiC path for the breakout configuration.

    Args:
        if_name (str): The name of the interface.

    Returns:
        The SONiC path for the breakout configuration.
    """
    if if_name:
        return get_gnmi_path(
            f"sonic-port-breakout:sonic-port-breakout/BREAKOUT_CFG/BREAKOUT_CFG_LIST[ifname={if_name}]"
        )
    else:
        return get_gnmi_path("sonic-port-breakout:sonic-port-breakout/BREAKOUT_CFG/BREAKOUT_CFG_LIST")


def config_interface_breakout_on_device(device_ip: str, if_alias: str, breakout_mode: str):
    """
    Configures the breakout mode on a device.

    Args:
        device_ip (str): The IP address of the device.
        if_alias (str): The alias of the interface.
        breakout_mode (str): The breakout mode.

    Returns:
        The result of the GNMI set operation.
    """
    if len(if_alias.split()) > 2:
        raise Exception("Invalid interface for breakout")
    if_alias = get_if_alias(if_alias)
    path = get_breakout_path(if_alias)
    num_breakouts, breakout_speed = get_number_of_breakouts_and_speed(breakout_mode=breakout_mode)
    config = {"index": 1, "num-physical-channels": 0}
    if num_breakouts is not None:
        config["num-breakouts"] = num_breakouts
    if breakout_speed:
        config["breakout-speed"] = breakout_speed
    request = create_gnmi_update(
        path=path,
        val={
            "openconfig-platform-port:groups": {
                "group": [
                    {
                        "index": 1,
                        "config": config
                    }
                ]
            }
        }
    )
    return send_gnmi_set(
        req=create_req_for_update([request]),
        device_ip=device_ip
    )


def get_breakout_from_device(device_ip: str, if_alias: str):
    """
    Retrieves the breakout configuration from a device.

    Args:
        device_ip (str): The IP address of the device.
        if_alias (str, optional): The alias of the interface.
    Returns:
        The breakout configuration as a dictionary.
    """
    return send_gnmi_get(
        device_ip=device_ip,
        path=[get_breakout_path(if_alias)],
    )


def delete_interface_breakout_from_device(device_ip: str, if_alias: str):
    """
    Deletes the breakout configuration on a device.

    Args:
        device_ip (str): The IP address of the device.
        if_alias (str): The alias of the interface.
    """
    if_alias = get_if_alias(if_alias)
    path = get_breakout_path(if_alias=if_alias)
    return send_gnmi_set(
        get_gnmi_del_req(path=path), device_ip=device_ip
    )


def delete_interface_ip_from_device(
        device_ip: str, if_name: str, index: int = 0, ip_address: str = None, secondary: bool = False
):
    """
    Deletes the IP configuration on a device.

    Args:
        device_ip (str): The IP address of the device.
        if_name (str): The name of the interface.
        secondary (bool): Whether the IP configuration is secondary or not.
        index (int, optional): The index of the subinterface. Defaults to 0.
        ip_address (str, optional): The IP address to delete. Defaults to None.
    """
    if ip_address:
        ip, nw_addr, prefix_len = validate_and_get_ip_prefix(ip_address)
        if secondary:
            path = get_gnmi_path(
                f"openconfig-interfaces:interfaces/interface[name={if_name}]/subinterfaces/subinterface[index={index}]/openconfig-if-ip:ipv4/addresses/address[ip={ip}]/config/secondary"
            )
        else:
            path = get_gnmi_path(
                f"openconfig-interfaces:interfaces/interface[name={if_name}]/subinterfaces/subinterface[index={index}]/openconfig-if-ip:ipv4/addresses/address[ip={ip}]"
            )
    else:
        path = get_gnmi_path(
            f"openconfig-interfaces:interfaces/interface[name={if_name}]/subinterfaces/subinterface[index={index}]/openconfig-if-ip:ipv4/addresses/address"
        )
    return send_gnmi_set(
        get_gnmi_del_req(path=path), device_ip=device_ip
    )