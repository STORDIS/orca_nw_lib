import threading
from typing import List, Optional

from .common import PortFec, Speed
from .device_db import get_device_db_obj
from .graph_db_models import Device, Interface, SubInterface
from .utils import get_logging

_logger = get_logging().getLogger(__name__)
interface_lock = threading.Lock()


def interface_operation(func):
    """
    Decorator to ensure thread safety for interface operations.
    """

    def wrapper(*args, **kwargs):
        # Acquire the lock before any interface operation
        with interface_lock:
            # Use a transaction to ensure atomicity
            # with db.transaction:
            return func(*args, **kwargs)

    return wrapper


def get_all_interfaces_of_device_from_db(device_ip: str) -> Optional[List[Interface]]:
    """
    Get all interfaces of a device from the database.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        list: A list of all interfaces of the device from the database. Returns None if the device is not found in the database.
    """
    if not device_ip:
        _logger.error("Device IP is required.")
        return None
    device = get_device_db_obj(device_ip)
    with interface_lock:
        return device.interfaces.all() if device else None


def get_interface_of_device_from_db(
    device_ip: str, interface_name: str
) -> Optional[Interface]:
    """
    Retrieves the interface of a device from the database based on the device's IP and the interface name.

    Parameters:
        device_ip (str): The IP address of the device.
        interface_name (str): The name of the interface.

    Returns:
        Interface: The interface object if it exists in the database for the given device and interface name,
                   otherwise returns None.
    """
    if not device_ip:
        _logger.error("Device IP is required.")
        return None
    if not interface_name:
        _logger.error("Interface name is required.")
        return None
    device = get_device_db_obj(device_ip)
    with interface_lock:
        return device.interfaces.get_or_none(name=interface_name) if device else None


def get_sub_interface_of_device_from_db(
    device_ip: str, sub_if_ip: str
) -> Optional[SubInterface]:
    """
    Retrieves the sub-interface of a device from the database based on the device IP address and sub-interface IP address.

    Args:
        device_ip (str): The IP address of the device.
        sub_if_ip (str): The IP address of the sub-interface.

    Returns:
        SubInterface: The sub-interface object if found, otherwise None.
    """
    if not device_ip:
        _logger.error("Device IP is required.")
        return None
    if not sub_if_ip:
        _logger.error("Sub-interface IP is required.")
        return None
    for intf in get_all_interfaces_of_device_from_db(device_ip) or []:
        if si := intf.subInterfaces.get_or_none(ip_address=sub_if_ip):
            return si


def get_sub_interface_of_intfc_from_db(
    device_ip: str, if_name: str, sub_if_ip: Optional[str] = None
) -> Optional[SubInterface] | List[SubInterface]:
    """
    Retrieves a sub-interface of an interface from the database.

    Parameters:
        device_ip (str): The IP address of the device.
        if_name (str): The name of the interface.
        sub_if_ip (str, optional): The IP address of the sub-interface. Defaults to None.

    Returns:
        sub_interface or list: The sub-interface if sub_if_ip is provided, otherwise a list of all sub-interfaces.

    """
    if not device_ip:
        _logger.error("Device IP is required.")
        return None
    if not if_name:
        _logger.error("Interface name is required.")
        return None
    intf = get_interface_of_device_from_db(device_ip, if_name)
    if intf:
        if sub_if_ip:
            return intf.subInterfaces.get_or_none(ip_address=sub_if_ip)
        else:
            return intf.subInterfaces.all()
    return None


def get_sub_interface_from_db(sub_if_ip: str) -> Optional[SubInterface]:
    """
    Retrieve a sub-interface from the database based on its IP address.

    Args:
        sub_if_ip (str): The IP address of the sub-interface to retrieve.

    Returns:
        SubInterface: The SubInterface object representing the retrieved sub-interface.
                     Returns None if the sub-interface is not found in the database.
    """
    if not sub_if_ip:
        _logger.error("Sub-interface IP is required.")
        return None
    devices = get_device_db_obj()
    for device in devices:
        if si := get_sub_interface_of_device_from_db(device.mgt_ip, sub_if_ip):
            return si


def copy_intfc_object_props(target_intfc: Interface, source_intfc: Interface):
    """
    Copies the properties of the source interface object to the target interface object.

    Parameters:
        target_intfc (Interface): The target interface object to copy the properties to.
        source_intfc (Interface): The source interface object to copy the properties from.

    Returns:
        None
    """
    if not target_intfc:
        _logger.error("Target interface object is required.")
        return None
    if not source_intfc:
        _logger.error("Source interface object is required.")
        return None
    target_intfc.name = source_intfc.name
    target_intfc.enabled = source_intfc.enabled
    target_intfc.mtu = source_intfc.mtu
    target_intfc.fec = source_intfc.fec
    target_intfc.speed = source_intfc.speed
    target_intfc.oper_sts = source_intfc.oper_sts
    target_intfc.admin_sts = source_intfc.admin_sts
    target_intfc.description = source_intfc.description
    target_intfc.last_chng = source_intfc.last_chng
    target_intfc.mac_addr = source_intfc.mac_addr
    target_intfc.alias = source_intfc.alias
    target_intfc.lanes = source_intfc.lanes
    target_intfc.valid_speeds = source_intfc.valid_speeds
    target_intfc.adv_speeds = source_intfc.adv_speeds
    target_intfc.link_training = source_intfc.link_training
    target_intfc.autoneg = source_intfc.autoneg
    target_intfc.breakout_mode = source_intfc.breakout_mode
    target_intfc.breakout_supported = source_intfc.breakout_supported
    target_intfc.breakout_status = source_intfc.breakout_status


def set_interface_config_in_db(
    device_ip: str,
    if_name: str,
    enable: Optional[bool] = None,
    mtu: Optional[int] = None,
    speed: Optional[Speed] = None,
    description: Optional[str] = None,
    fec: Optional[PortFec] = None,
    autoneg: Optional[bool] = None,
    adv_speeds: Optional[str] = None,
    link_training: Optional[bool] = None,
    lldp_nbrs: Optional[List[str]] = None,
):
    """
    Sets the configuration of an interface in the database.

    Parameters:
        device_ip (str): The IP address of the device.
        if_name (str): The name of the interface.
        enable (bool, optional): Whether the interface should be enabled or not. Defaults to None.
        mtu (Any, optional): The maximum transmission unit (MTU) of the interface. Defaults to None.
        speed (Speed, optional): The speed of the interface. Defaults to None.
        description (str, optional): The description of the interface. Defaults to None.
        fec (PortFec, optional): The Forward Error Correction (FEC) mode of the interface. Defaults to None.

    Returns:
        None

    """
    if not device_ip:
        _logger.error("Device IP is required.")
        return None
    if not if_name:
        _logger.error("Interface name is required.")
        return None
    interface = get_interface_of_device_from_db(device_ip, if_name)
    with interface_lock:
        if interface:
            if enable is not None:
                _logger.debug(
                    "Updating interface %s enable state in DB object to %s",
                    interface,
                    enable,
                )
                interface.enabled = enable
            if mtu is not None:
                _logger.debug(
                    "Updating interface %s MTU in DB object to %s", interface, mtu
                )
                interface.mtu = mtu
            if speed is not None:
                _logger.debug(
                    "Updating interface %s speed in DB object to %s", interface, speed
                )
                interface.speed = str(speed)
            if description is not None:
                _logger.debug(
                    "Updating interface %s description in DB object to %s",
                    interface,
                    description,
                )
                interface.description = description
            if fec is not None:
                _logger.debug(
                    "Updating interface %s FEC in DB object to %s", interface, fec
                )
                interface.fec = str(fec)
            if autoneg is not None:
                _logger.debug(
                    "Updating interface %s auto-negotiate in DB object to %s",
                    interface,
                    autoneg,
                )
                interface.autoneg = "on" if autoneg else "off"
            if adv_speeds is not None:
                _logger.debug(
                    "Updating interface %s advertised-speed in DB object to %s",
                    interface,
                    adv_speeds,
                )
                interface.adv_speeds = str(adv_speeds)
            if link_training is not None:
                _logger.debug(
                    "Updating interface %s standalone-link-training in DB object to %s",
                    interface,
                    link_training,
                )
                interface.link_training = "on" if link_training else "off"
            if lldp_nbrs:
                _logger.debug(
                    "Updating interface %s LLDP neighbors in DB object to %s",
                    interface,
                    lldp_nbrs,
                )
                interface.lldp_nbrs = lldp_nbrs
            interface.save()
            _logger.debug("Saved interface config in DB %s", interface)


def insert_device_interfaces_in_db(device: Device, interfaces: dict):
    """
    Insert device interfaces into the database.

    Parameters:
        device (Device): The device object to insert interfaces for.
        interfaces (dict): A dictionary of interfaces to insert, where the keys are interface names
            and the values are lists of sub-interfaces.

    Returns:
        None
    """
    if not device:
        _logger.error("Device object is required.")
        return None
    if not interfaces:
        _logger.error("Interfaces dictionary is required.")
        return None
    for intfc, sub_intfc in interfaces.items():
        if i := get_interface_of_device_from_db(device.mgt_ip, intfc.name):
            # Update existing node
            copy_intfc_object_props(i, intfc)
            i.save()
            device.interfaces.connect(i)
        else:
            intfc.save()
            device.interfaces.connect(intfc)

        saved_i = get_interface_of_device_from_db(device.mgt_ip, intfc.name)
        # Handle following cases:
        # 1. Discover already configured sub-interfaces
        # 2. New sub-interface added to interface
        # 3. Existing sub-interface(s) removed from interface
        # Easiest and efficient way is to delete all sub-interfaces and recreate all sub-interfaces
        # received in the dictionary after discovery.
        # because current implementation always discovers all the subinterfaces,
        # hence we have uptodate subinterfaces in the dictionary.
        saved_i.subInterfaces.disconnect_all()
        for si in saved_i.subInterfaces.all():
            si.delete()
        for sub_i in sub_intfc:
            sub_i.save()
            saved_i.subInterfaces.connect(sub_i) if saved_i else None

        # Assuming that this function will receive either one interface or all in the param. (Nothing in between)
        # Any thing more than one is considered to be all the interfaces of the device (may be it wont be true in coming future).
        # So, the param contains all the interfaces from device, we delete interfaces from the neo4j which are not in the ,
        # interface list from device.
        # This is useful in the cases e.g. breakout has been deletd from device 
        # but due to some error the broken out ports are not cleared from neo4j db,
        # User will still have a chance to resync the device interfaces because here the broken out port will be deleted from neo4j.
        # And neo4j is back in sync.
        if len(interfaces) > 1:
            for interface in get_all_interfaces_of_device_from_db(device.mgt_ip):
                if interface not in interfaces:
                    interface.delete()


def get_all_interfaces_name_of_device_from_db(device_ip: str) -> Optional[List[str]]:
    """
    Get all the interface names of a device from the database.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        list: A list of interface names if interfaces exist for the device, else None.
    """
    if not device_ip:
        _logger.error("Device IP is required.")
        return None
    intfcs = get_all_interfaces_of_device_from_db(device_ip)
    return [intfc.name for intfc in intfcs] if intfcs else None


def get_interface_by_alias_from_db(device_ip: str, alias: str) -> Optional[Interface]:
    """
    Get the interface object of a device by its alias.

    Args:
        device_ip (str): The IP address of the device.
        alias (str): The alias of the interface.

    Returns:
        Interface: The interface object if the interface exists, else None.
    """
    if not device_ip:
        _logger.error("Device IP is required.")
        return None
    if not alias:
        _logger.error("Interface alias is required.")
        return None
    device = get_device_db_obj(device_ip)
    return device.interfaces.get_or_none(alias=alias) if device else None
