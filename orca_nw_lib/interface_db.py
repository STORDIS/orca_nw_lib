from orca_nw_lib.common import Speed
from orca_nw_lib.device_db import get_device_db_obj
from orca_nw_lib.graph_db_models import Device, Interface, SubInterface


def get_all_interfaces_of_device_from_db(device_ip: str):
    """
    Get all interfaces of a device from the database.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        list: A list of all interfaces of the device from the database. Returns None if the device is not found in the database.
    """
    device = get_device_db_obj(device_ip)
    return device.interfaces.all() if device else None


def get_interface_of_device_from_db(device_ip: str, interface_name: str) -> Interface:
    """
    Retrieves the interface of a device from the database based on the device's IP and the interface name.

    Parameters:
        device_ip (str): The IP address of the device.
        interface_name (str): The name of the interface.

    Returns:
        Interface: The interface object if it exists in the database for the given device and interface name,
                   otherwise returns None.
    """
    device = get_device_db_obj(device_ip)
    return (
        get_device_db_obj(device_ip).interfaces.get_or_none(name=interface_name)
        if device
        else None
    )


def get_sub_interface_of_device_from_db(device_ip: str, sub_if_ip: str) -> SubInterface:
    """
    Retrieves the sub-interface of a device from the database based on the device IP address and sub-interface IP address.

    Args:
        device_ip (str): The IP address of the device.
        sub_if_ip (str): The IP address of the sub-interface.

    Returns:
        SubInterface: The sub-interface object if found, otherwise None.
    """
    for intf in get_all_interfaces_of_device_from_db(device_ip) or []:
        if si := intf.subInterfaces.get_or_none(ip_address=sub_if_ip):
            return si


def get_sub_interface_of_intfc_from_db(
    device_ip: str, if_name: str, sub_if_ip: str = None
):
    """
    Retrieves a sub-interface of an interface from the database.

    Parameters:
        device_ip (str): The IP address of the device.
        if_name (str): The name of the interface.
        sub_if_ip (str, optional): The IP address of the sub-interface. Defaults to None.

    Returns:
        sub_interface or list: The sub-interface if sub_if_ip is provided, otherwise a list of all sub-interfaces.

    """
    intf = get_interface_of_device_from_db(device_ip, if_name)
    if intf:
        if sub_if_ip:
            return intf.subInterfaces.get__or_none(ip_address=sub_if_ip)
        else:
            return intf.subInterfaces.all()
    return None


def get_sub_interface_from_db(sub_if_ip: str) -> SubInterface:
    """
    Retrieve a sub-interface from the database based on its IP address.

    Args:
        sub_if_ip (str): The IP address of the sub-interface to retrieve.

    Returns:
        SubInterface: The SubInterface object representing the retrieved sub-interface.
                     Returns None if the sub-interface is not found in the database.
    """
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


def set_interface_config_in_db(
    device_ip: str,
    if_name: str,
    enable: bool = None,
    mtu=None,
    speed: Speed = None,
    description: str = None,
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

    Returns:
        None

    """

    interface = get_interface_of_device_from_db(device_ip, if_name)
    if interface:
        if enable is not None:
            interface.enabled = enable
        if mtu is not None:
            interface.mtu = mtu
        if speed is not None:
            interface.speed = str(speed)
        if description is not None:
            interface.description = description
    interface.save()


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

        for sub_i in sub_intfc:
            if si := get_sub_interface_of_device_from_db(
                device.mgt_ip, sub_i.ip_address
            ):
                si.ip_address = sub_i.ip_address
                si.save()
                saved_i.subInterfaces.connect(si) if saved_i else None
            else:
                sub_i.save()
                saved_i.subInterfaces.connect(sub_i) if saved_i else None


def get_all_interfaces_name_of_device_from_db(device_ip: str):
    """
    Get all the interface names of a device from the database.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        list: A list of interface names if interfaces exist for the device, else None.
    """
    intfcs = get_all_interfaces_of_device_from_db(device_ip)
    return [intfc.name for intfc in intfcs] if intfcs else None
