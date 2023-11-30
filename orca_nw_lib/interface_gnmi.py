from orca_nw_lib.common import PortFec, Speed
from orca_nw_lib.gnmi_pb2 import Path, PathElem
from orca_nw_lib.interface_db import get_all_interfaces_name_of_device_from_db
from orca_nw_lib.gnmi_util import (
    create_gnmi_update,
    create_req_for_update,
    get_gnmi_del_req,
    send_gnmi_get,
    send_gnmi_set,
)
from orca_nw_lib.portgroup import discover_port_groups
import orca_nw_lib.portgroup_db
import orca_nw_lib.portgroup_gnmi


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


def set_interface_config_on_device(
    device_ip: str,
    interface_name: str,
    enable: bool = None,
    mtu: int = None,
    loopback: bool = None,
    description: str = None,
    speed: Speed = None,
    ip: str = None,
    ip_prefix_len: int = 0,
    index: int = 0,
    fec: PortFec = None,
):
    """
    Set the interface configuration on a device.

    Args:
        device_ip (str): The IP address of the device.
        interface_name (str): The name of the interface.
        enable (bool, optional): Whether to enable the interface. Defaults to None.
        mtu (int, optional): The maximum transmission unit (MTU) size. Defaults to None.
        loopback (bool, optional): Whether to enable loopback mode. Defaults to None.
        description (str, optional): The interface description. Defaults to None.
        speed (Speed, optional): The interface speed. Defaults to None.
        ip (str, optional): The IP address of the subinterface. Defaults to None.
        ip_prefix_len (int, optional): The prefix length of the IP address. Defaults to 0.
        index (int, optional): The index of the subinterface. Defaults to 0.
        fec (bool, optional): Whether to enable forward error correction. Defaults to None.


    Returns:
        None: If no updates were made.
        str: The response from sending the GNMI set request.

    """
    updates = []

    if enable is not None:
        updates.append(
            create_gnmi_update(
                get_intfc_enabled_path(interface_name),
                {"openconfig-interfaces:enabled": enable},
            )
        )

    if fec is not None:
        updates.append(
            create_gnmi_update(
                get_port_fec_path(interface_name),
                {"openconfig-if-ethernet-ext2:port-fec": str(fec)},
            )
        )

    if mtu is not None:
        base_config_path = get_intfc_config_path(interface_name)
        base_config_path.elem.append(PathElem(name="mtu"))
        updates.append(
            create_gnmi_update(
                base_config_path,
                {"openconfig-interfaces:mtu": mtu},
            )
        )

    if loopback is not None:
        base_config_path = get_intfc_config_path(interface_name)
        base_config_path.elem.append(PathElem(name="loopback-mode"))
        updates.append(
            create_gnmi_update(
                base_config_path,
                {"openconfig-interfaces:loopback-mode": loopback},
            )
        )

    if description is not None:
        base_config_path = get_intfc_config_path(interface_name)
        base_config_path.elem.append(PathElem(name="description"))
        updates.append(
            create_gnmi_update(
                base_config_path,
                {"openconfig-interfaces:description": description},
            )
        )

    if speed is not None:
        # if switch supports port groups then configure speed on port-group otherwise directly on interface
        if (pg_id := orca_nw_lib.portgroup_db.get_port_group_id_of_device_interface_from_db(
                device_ip, interface_name
            )
        ):
            updates.append(
                create_gnmi_update(
                    orca_nw_lib.portgroup_gnmi._get_port_group_speed_path(pg_id),
                    {"openconfig-port-group:speed": speed.get_oc_val()},
                )
            )

        else:
            updates.append(
                create_gnmi_update(
                    get_intfc_speed_path(interface_name),
                    {"port-speed": speed.get_oc_val()},
                )
            )

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
                                        "prefix-length": ip_prefix_len,
                                        "secondary": False,
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
                get_sub_interface_path(interface_name),
                ip_payload,
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

    return send_gnmi_get(device_ip=device_ip, path=[get_interface_path(intfc_name)])


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
