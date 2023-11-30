import datetime
from typing import Dict, List
from grpc._channel import _InactiveRpcError

import pytz

from orca_nw_lib.common import Speed, PortFec
from orca_nw_lib.device_db import get_device_db_obj
from orca_nw_lib.graph_db_models import Interface, SubInterface
from orca_nw_lib.interface_db import (
    get_all_interfaces_of_device_from_db,
    get_interface_of_device_from_db,
    get_sub_interface_of_intfc_from_db,
    insert_device_interfaces_in_db,
)
from orca_nw_lib.interface_gnmi import (
    del_all_subinterfaces_of_all_interfaces_from_device,
    del_all_subinterfaces_of_interface_from_device,
    get_interface_from_device,
    set_interface_config_on_device,
)
from orca_nw_lib.portgroup import discover_port_groups
from orca_nw_lib.portgroup_db import get_port_group_id_of_device_interface_from_db
from orca_nw_lib.utils import get_logging


_logger = get_logging().getLogger(__name__)


def _create_interface_graph_objects(device_ip: str, intfc_name: str = None):
    """
    Retrieves interface information from a device and creates interface graph objects.

    Parameters:
        device_ip (str): The IP address of the device.
        intfc_name (str, optional): The name of the interface. Defaults to None.

    Returns:
        Dict[Interface, List[SubInterface]]: A dictionary mapping Interface objects to a list of SubInterface objects.
    """
    interfaces_json = get_interface_from_device(device_ip, intfc_name)
    intfc_graph_obj_list: Dict[Interface, List[SubInterface]] = {}
    for intfc in interfaces_json.get("openconfig-interfaces:interface") or []:
        intfc_state = intfc.get("state", {})
        if_type = intfc.get("config").get("type")

        if (
            "ether" or "loopback" in if_type.lower()
        ) and "PortChannel" not in intfc_state.get("name"):
            # Port channels are separately discovered so skip them in interface discovery
            interface = Interface(
                name=intfc_state.get("name"),
                enabled=intfc_state.get("enabled"),
                mtu=intfc_state.get("mtu"),
                fec=PortFec.getFecStrFromOCStr(
                    intfc.get("openconfig-if-ethernet:ethernet", {})
                    .get("config", {})
                    .get("openconfig-if-ethernet-ext2:port-fec")
                ),
                speed=Speed.getSpeedStrFromOCStr(s)
                if (
                    s := intfc.get("openconfig-if-ethernet:ethernet", {})
                    .get("config", {})
                    .get("port-speed")
                )
                else None,
                oper_sts=intfc_state.get("oper-status"),
                admin_sts=intfc_state.get("admin-status"),
                description=intfc_state.get("description"),
                last_chng=(
                    (lambda utc_date: f"{str(utc_date)} {utc_date.tzinfo}")(
                        datetime.datetime.utcfromtimestamp(int(last_chng)).replace(
                            tzinfo=pytz.utc
                        )
                        if (last_chng := 1688989316)
                        else 0
                    )
                ),
                mac_addr=intfc_state.get("mac-address"),
            )
            sub_intf_obj_list = []
            for sub_intfc in intfc.get("subinterfaces", {}).get("subinterface", {}):
                sub_intf_obj = SubInterface()
                for addr in (
                    sub_intfc.get("openconfig-if-ip:ipv4", {})
                    .get("addresses", {})
                    .get("address")
                    or []
                ):
                    if addr.get("ip"):
                        sub_intf_obj.ip_address = addr.get("ip")
                    sub_intf_obj_list.append(sub_intf_obj)

            intfc_graph_obj_list[interface] = sub_intf_obj_list
        elif "lag" in if_type.lower():
            # its a port channel
            pass
        else:
            _logger.error(f"Unknown Interface type {if_type}")

    return intfc_graph_obj_list


def get_possible_speeds():
    return [str(e) for e in Speed]


def get_interface(device_ip: str, intfc_name=None):
    """
    Returns the properties of a network interface on a device.

    Args:
        device_ip (str): The IP address of the device.
        intfc_name (str, optional): The name of the interface. Defaults to None.

    Returns:
        Union[List[Dict[str, Any]], Dict[str, Any], None]: The properties of the interface
        if the interface exists, a list of properties of all interfaces on the device
        if no interface name is provided, or None if the interface does not exist.
    """
    if intfc_name:
        return (
            intfc.__properties__
            if (intfc := get_interface_of_device_from_db(device_ip, intfc_name))
            else None
        )
    return [
        intf.__properties__ for intf in get_all_interfaces_of_device_from_db(device_ip)
    ]


def config_interface(device_ip: str, intfc_name: str, **kwargs):
    """
    Configure the interface of a device.

    Parameters:
        device_ip (str): The IP address of the device.
        intfc_name (str): The name of the interface.
        kwargs (dict): The configuration parameters of the interface.

    kwargs:
        enable (bool, optional): The enable status of the interface. Defaults to None.
        loopback (bool, optional): The loopback status of the interface. Defaults to None.
        mtu (int, optional): The maximum transmission unit of the interface. Defaults to None.
        speed (Speed, optional): The speed of the interface. Defaults to None.
        description (str, optional): The description of the interface. Defaults to None.
        ip (str, optional): The IP address of the interface. Defaults to None.
        ip_prefix_len (int, optional): The IP prefix length of the interface. Defaults to 0.
        index (int, optional): The index of the sub-interface. Defaults to 0.
        fec (PortFec, optional): Enable disable forward error correction. Defaults to None.

    raises:
        _InactiveRpcError: If the configuration of the interface fails.

    """
    _logger.debug(f"Configuring interface {intfc_name} on device {device_ip}")
    try:
        set_interface_config_on_device(device_ip, intfc_name, **kwargs)
        _logger.debug(f"Configured interface {intfc_name} on device {device_ip}")
    except _InactiveRpcError as err:
        _logger.error(
            f"Configuring interface {intfc_name} on device {device_ip} failed, Reason: {err.details()}"
        )
        raise
    finally:
        ## If switch supports port groups, discover all member interfaces of the port-group
        ## of which the intfc_name is the member of.
        discover_interfaces(device_ip, intfc_name,config_triggered_discovery=True)


def del_ip_from_intf(device_ip: str, intfc_name: str):
    """
    Delete an IP address from an interface.

    Parameters:
        device_ip (str): The IP address of the device.
        intfc_name (str): The name of the interface.

    Raises:
        _InactiveRpcError: If the deletion of the IP address from the interface fails.

    """
    try:
        del_all_subinterfaces_of_interface_from_device(device_ip, intfc_name)
    except _InactiveRpcError as err:
        _logger.error(
            f"Deleting IP address from interface {intfc_name} on device {device_ip} failed, Reason: {err.details()}"
        )
        raise
    finally:
        discover_interfaces(device_ip, intfc_name)


def discover_interfaces(
    device_ip: str = None,
    intfc_name: str = None,
    config_triggered_discovery: bool = False,
):
    _logger.info("Interface Discovery Started.")
    devices = [get_device_db_obj(device_ip)] if device_ip else get_device_db_obj()
    for device in devices:
        try:
            _logger.info(
                f"Discovering {intfc_name if intfc_name else 'all interfaces'} of device {device}."
            )
            insert_device_interfaces_in_db(
                device, _create_interface_graph_objects(device.mgt_ip, intfc_name)
            )
        except _InactiveRpcError as err:
            _logger.error(
                f"Interface Discovery Failed on device {device_ip}, Reason: {err.details()}"
            )
            raise

        ## If discovery is triggered due to config update via ORCA and the
        # device supports port-group then discover port-group
        ## of which the intfc_name is the member of.
        if (
            intfc_name
            and config_triggered_discovery
            and (
                pg_id := get_port_group_id_of_device_interface_from_db(
                    device_ip, intfc_name
                )
            )
        ):
            discover_port_groups(
                device_ip=device_ip,
                port_group_id=pg_id,
                config_triggered_discovery=config_triggered_discovery,
            )


def get_subinterfaces(device_ip: str, intfc_name: str):
    """
    Retrieves the subinterfaces of a given device IP and interface name from the database.

    Args:
        device_ip (str): The IP address of the device.
        intfc_name (str): The name of the interface.

    Returns:
        list: A list of dictionaries representing the properties of each subinterface.
    """

    return [
        sub_intfc.__properties__
        for sub_intfc in get_sub_interface_of_intfc_from_db(device_ip, intfc_name)
    ]


def del_all_subinterfaces_of_interface(device_ip: str, if_name: str):
    """
    Delete all subinterfaces of all interfaces.

    Raises:
        _InactiveRpcError: If the deletion of the subinterfaces fails.

    Returns:
        None
    """
    _logger.info("Deleting all subinterfaces of all interfaces.")
    try:
        del_all_subinterfaces_of_interface_from_device(device_ip, if_name)
    except _InactiveRpcError as err:
        _logger.error(
            f"Deleting all subinterfaces of all interfaces failed, Reason: {err.details()}"
        )
        raise
    finally:
        discover_interfaces(device_ip, if_name)


def del_all_subinterfaces_of_all_interfaces(device_ip: str):
    """
    Delete all subinterfaces of all interfaces.

    Raises:
        _InactiveRpcError: If the deletion of the subinterfaces fails.

    Returns:
        None
    """
    _logger.info("Deleting all subinterfaces of all interfaces.")
    try:
        del_all_subinterfaces_of_all_interfaces_from_device(device_ip)
    except _InactiveRpcError as err:
        _logger.error(
            f"Deleting all subinterfaces of all interfaces failed, Reason: {err.details()}"
        )
        raise
    finally:
        discover_interfaces(device_ip)
