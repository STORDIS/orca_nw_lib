import datetime
from typing import Dict, List
import pytz

from .common import IFMode, Speed, PortFec
from .device_db import get_device_db_obj
from .gnmi_sub import check_gnmi_subscription_and_apply_config
from .graph_db_models import Interface, SubInterface
from .interface_db import (
    get_all_interfaces_name_of_device_from_db,
    get_all_interfaces_of_device_from_db,
    get_interface_of_device_from_db,
    get_sub_interface_of_intfc_from_db,
    insert_device_interfaces_in_db, get_interface_by_alias_from_db,
)
from .interface_gnmi import (
    del_all_subinterfaces_of_all_interfaces_from_device,
    del_all_subinterfaces_of_interface_from_device,
    get_interface_from_device,
    set_if_vlan_on_device,
    set_interface_config_on_device,
    remove_vlan_from_if_from_device,
    config_interface_breakout_on_device,
    get_breakout_from_device,
    delete_interface_breakout_from_device,
    delete_interface_ip_from_device,
)
from .portgroup import discover_port_groups
from .portgroup_db import (
    get_port_group_id_of_device_interface_from_db,
    get_port_group_of_if_from_db,
)
from .utils import get_logging, get_if_alias

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
    if_lane_details = interfaces_json.get("sonic-port:PORT_LIST")
    for intfc in interfaces_json.get("openconfig-interfaces:interface") or []:
        intfc_state = intfc.get("state", {})
        config = intfc.get("config")
        if config is None:
            continue
        if_type = config.get("type", "")

        if (
            ("ether" or "loopback" in if_type.lower())
            and "PortChannel" not in intfc_state.get("name")
            and "Vlan" not in intfc_state.get("name")
            and "Management" not in intfc_state.get("name")
            and if_type != "openconfig-if-types-ext:IF_NVE"
        ):
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
                speed=(
                    Speed.getSpeedStrFromOCStr(s)
                    if (
                        s := intfc.get("openconfig-if-ethernet:ethernet", {})
                        .get("config", {})
                        .get("port-speed")
                    )
                    else None
                ),
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
            for sub_intfc in intfc.get("subinterfaces", {}).get("subinterface", []):
                for addr in (
                    sub_intfc.get("openconfig-if-ip:ipv4", {})
                    .get("addresses", {})
                    .get("address", [])
                ):
                    sub_intf_obj = SubInterface()
                    if addr.get("ip"):
                        config = addr.get("config", {})
                        sub_intf_obj.ip_address = addr.get("ip")
                        sub_intf_obj.prefix = config.get("prefix-length")
                        sub_intf_obj.secondary = config.get("secondary")
                    sub_intf_obj_list.append(sub_intf_obj)

            ## Now iterate lane details
            for indx, value in enumerate(if_lane_details or []):
                breakout_state = {}
                breakout_config = {}
                if len(value.get("alias", "").split("/")) > 2:
                    if_alias = get_if_alias(if_alias=value.get("alias"))
                    # Get breakout details
                    breakout_details = get_breakout_from_device(device_ip, if_alias).get(
                        "openconfig-platform-port:groups", {}
                    )
                    for i in breakout_details.get("group", []):
                        breakout_config = i.get("config", {})
                        breakout_state = i.get("state", {})
                if interface.name == value.get("ifname"):
                    interface.alias = value.get("alias")
                    interface.lanes = value.get("lanes")
                    interface.valid_speeds = value.get("valid_speeds")
                    interface.adv_speeds = value.get("adv_speeds")
                    interface.link_training = value.get("link_training")
                    interface.autoneg = value.get("autoneg")
                    interface.breakout_mode = "{}x{}".format(
                        breakout_config.get("num-breakouts"),
                        Speed.getSpeedStrFromOCStr(breakout_config.get("breakout-speed"))
                    ) if breakout_config else None
                    interface.breakout_supported = len(value.get("lanes", "").split(",")) > 1
                    interface.breakout_status = breakout_state.get("openconfig-port-breakout-ext:status", None)
                    ## To minimize iteration for element in outer loop
                    if_lane_details.pop(indx)
                    break

            intfc_graph_obj_list[interface] = sub_intf_obj_list
        elif "lag" in if_type.lower():
            _logger.debug(
                f"Interface will not be discovered in Ethernet discovery instead under Port Channel discovery. Interface type: {if_type}."
            )

        else:
            _logger.debug(
                f"Interface {intfc.get('name', '')} will not be discovered in Ethernet discovery. Interface type: {if_type}."
            )

    return intfc_graph_obj_list


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
            _merge_interface_and_sub_interface(intfc)
            if (intfc := get_interface_of_device_from_db(device_ip, intfc_name))
            else None
        )
    return [
        _merge_interface_and_sub_interface(intf)
        for intf in get_all_interfaces_of_device_from_db(device_ip) or []
        if intf
    ]


def _merge_interface_and_sub_interface(intfc: Interface):
    """
    Merges the interface and sub-interface properties into a single dictionary.

    Args:
        intfc (Interface): The interface object.

    Returns:
        Dict[str, Any]: The merged properties of the interface and sub-interface.
    """
    subinterfaces = intfc.subInterfaces.all()
    # Extract the first subinterface IP address if it exists
    # Only one ip address is allowed per interface
    if subinterfaces:
        return {**intfc.__properties__, "ip_address": [
            {
                "ip_address": i.__properties__.get("ip_address"),
                "secondary": i.__properties__.get("secondary"),
                "prefix": i.__properties__.get("prefix"),
            } for i in subinterfaces
        ]}
    return intfc.__properties__


def get_pg_of_if(device_ip: str, intfc_name: str):
    """
    Retrieves the port group of the specified interface from the database.

    Args:
        device_ip (str): The IP address of the device.
        intfc_name (str): The name of the interface.

    Returns:
        The port group of the specified interface.
    """
    return (
        pg.__properties__
        if (pg := get_port_group_of_if_from_db(device_ip, intfc_name))
        else None
    )


def enable_all_ifs(device_ip: str):
    """
    Enable all interfaces on a device.

    Parameters:
        device_ip (str): The IP address of the device.
    """
    if_name_list = get_all_interfaces_name_of_device_from_db(device_ip)
    for intf_name in if_name_list or []:
        try:
            config_interface(device_ip=device_ip, if_name=intf_name, enable=True)
        except Exception as e:
            _logger.debug(
                f"Failed to enable interface {intf_name} on device {device_ip}. Error: {e}"
            )


@check_gnmi_subscription_and_apply_config
def config_interface(device_ip: str, if_name: str, **kwargs):
    """
    Configure the interface of a device.

    Parameters:
        device_ip (str): The IP address of the device.
        if_name (str): The name of the interface.
        kwargs (dict): The configuration parameters of the interface.

    kwargs:
        enable (bool, optional): The enable status of the interface. Defaults to None.
        mtu (int, optional): The maximum transmission unit of the interface. Defaults to None.
        speed (Speed, optional): The speed of the interface. Defaults to None.
        description (str, optional): The description of the interface. Defaults to None.
        ip_with_prefix (str, optional): The IP address and prefix of the interface. Defaults to None.
        index (int, optional): The index of the sub-interface. Defaults to 0.
        fec (PortFec, optional): Enable disable forward error correction. Defaults to None.
        secondary (bool, optional): The secondary status of the interface. Defaults to False.

    """
    _logger.debug("Configuring interface %s on device %s", if_name, device_ip)
    try:
        set_interface_config_on_device(device_ip, if_name, **kwargs)
        _logger.debug(
            "Configured interface %s on device %s -> %s", if_name, device_ip, kwargs
        )
    except Exception as e:
        _logger.error(
            f"Configuring interface {if_name} on device {device_ip} failed, Reason: {e}"
        )
        raise
    finally:
        ## discover the interface esp. the subinterfaces if there is a request to set IP
        # on the interface because currently there are no gNMI subscription available
        # for subinterface updates.
        if kwargs.get("ip_with_prefix"):
            discover_interfaces(device_ip, if_name)


def del_ip_from_intf(
        device_ip: str, intfc_name: str, index: int = 0, ip_address: str = None, secondary: bool = False
):
    """
    Delete an IP address from an interface.

    Parameters:
        device_ip (str): The IP address of the device.
        intfc_name (str): The name of the interface.
        index (int, optional): The index of the subinterface. Defaults to 0.
        ip_address (str, optional): The IP address to delete. Defaults to None.
        secondary (bool, optional): The secondary status of the interface. Defaults to False.

    """
    try:
        delete_interface_ip_from_device(
            device_ip=device_ip, if_name=intfc_name, ip_address=ip_address, secondary=secondary
        )
    except Exception as e:
        _logger.error(
            f"Deleting IP address from interface {intfc_name} on device {device_ip} failed, Reason: {e}"
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
        except Exception as e:
            _logger.error(
                f"Interface Discovery Failed on device {device_ip}, Reason: {e}"
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

    Returns:
        None
    """
    _logger.info("Deleting all subinterfaces of all interfaces.")
    try:
        del_all_subinterfaces_of_interface_from_device(device_ip, if_name)
    except Exception as e:
        _logger.error(
            f"Deleting all subinterfaces of all interfaces failed, Reason: {e}"
        )
        raise
    finally:
        discover_interfaces(device_ip, if_name)


def del_all_subinterfaces_of_all_interfaces(device_ip: str):
    """
    Delete all subinterfaces of all interfaces.

    Returns:
        None
    """
    _logger.info("Deleting all subinterfaces of all interfaces.")
    try:
        del_all_subinterfaces_of_all_interfaces_from_device(device_ip)

    except Exception as e:
        _logger.error(
            f"Deleting all subinterfaces of all interfaces failed, Reason: {e}"
        )
        raise
    finally:
        discover_interfaces(device_ip)


def remove_vlan(device_ip: str, intfc_name: str, if_mode: IFMode = None):
    """
    Removes the VLAN from an interface.

    Args:
        device_ip (str): The IP address of the device.
        intfc_name (str): The name of the interface.
        if_mode (IFMode): The interface mode to remove. Defaults to None. When None is passed, All the trunk and access VLANs are removed from Interface.

    Returns:
        None
    """
    _logger.info(f"Removing interface mode {if_mode} from interface {intfc_name}.")
    try:
        remove_vlan_from_if_from_device(device_ip, intfc_name, if_mode)
    except Exception as e:
        _logger.error(
            f"Removing interface mode {if_mode} from interface {intfc_name} on device {device_ip} failed, Reason: {e}"
        )
        raise
    finally:
        discover_interfaces(device_ip, intfc_name)


def set_if_mode(device_ip: str, if_name: str, if_mode: IFMode, vlan_id: int):
    """
    Sets the interface mode on a device.

    Args:
        device_ip (str): The IP address of the device.
        if_name (str): The name of the interface.
        if_mode (IFMode): The interface mode to set.
        vlan_id (int): The VLAN ID to set.

    Returns:
        None
    """
    _logger.info(f"Setting interface mode {if_mode} on interface {if_name}.")
    try:
        set_if_vlan_on_device(device_ip, if_name, if_mode, vlan_id)
    except Exception as e:
        _logger.error(
            f"Setting interface mode {if_mode} on interface {if_name} on device {device_ip} failed, Reason: {e}"
        )
        raise
    finally:
        discover_interfaces(device_ip, if_name)


def config_interface_breakout(device_ip: str, if_alias: str, breakout_mode: str):
    """
    Configures the breakout configuration on a device.

    Args:
        device_ip (str): The IP address of the device.
        if_alias (str): Name of the interface.
        breakout_mode (str): The breakout mode to configure.

    Returns:
        None
    """
    try:
        config_interface_breakout_on_device(device_ip, if_alias, breakout_mode)
    except Exception as e:
        _logger.error(f"Configuring interface breakout on interface {if_alias} failed, Reason: {e}")
        raise
    finally:
        discover_interfaces(device_ip)


def delete_interface_breakout(device_ip: str, if_alias: str):
    """
    Deletes the breakout configuration from a device.

    Args:
        device_ip (str): The IP address of the device.
        if_alias (str): Name of the interface.
    Returns:
        None
    """
    _logger.info(f"Deleting interface breakout on interface Eth{if_alias}.")
    try:
        delete_interface_breakout_from_device(device_ip, if_alias)
    except Exception as e:
        _logger.error(
            f"Deleting interface breakout on interface Eth{if_alias} on device {device_ip} failed, Reason: {e}"
        )
        raise
    finally:
        ## Explicitly delete the broken out ports from neo4j db.
        
        # Generate a list of interface aliases using a helper function.
        # It generates aliases from 'if_alias', with range from 1 to 4. example: Eth1/1/1, Eth1/1/2, Eth1/1/3, Eth1/1/4
        aliases = _generate_interface_alias_list(if_alias, 1, 4)

        # Deleting interface from database 2-4 alias
        for i in aliases[1:]:
            # Get the interface associated with the alias from the database using the device's IP
            interface = get_interface_by_alias_from_db(device_ip=device_ip, alias=i)
            # Delete the interface entry if it exists
            if interface:
                interface.delete()
        # After the loop, get the main interface using the original 'if_alias'
        interface = get_interface_by_alias_from_db(device_ip=device_ip, alias=aliases[0])

        # If the interface is found, call a function to discover the interface with its name
        if interface:
            discover_interfaces(device_ip, interface.name)


def _generate_interface_alias_list(alias, start, end):
    """
    Generate a list of interface names based on the provided range.

    Args:
        alias (str): The alias of the interface.
        start (int): The starting number of the range.
        end (int): The ending number of the range.

    Returns:
        list: A list of interface aliases.
    """
    # Remove the last number from the interface base
    alias_split = alias.split('/')
    base_interface = f"{alias_split[0]}/{alias_split[1]}"

    # Generate and return the new interfaces in the range from start to end
    generated_aliases = [f"{base_interface}/{i}" for i in range(start, end + 1)]

    # Return the list of interfaces
    return generated_aliases
