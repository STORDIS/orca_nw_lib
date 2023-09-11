from orca_nw_lib.common import Speed
from orca_nw_lib.device_db import get_device_db_obj
from orca_nw_lib.graph_db_models import Device, Interface, SubInterface


def get_all_interfaces_of_device_from_db(device_ip: str):
    device = get_device_db_obj(device_ip)
    return device.interfaces.all() if device else None


def get_interface_of_device_from_db(device_ip: str, interface_name: str) -> Interface:
    device = get_device_db_obj(device_ip)
    return (
        get_device_db_obj(device_ip).interfaces.get_or_none(name=interface_name)
        if device
        else None
    )


def get_sub_interface_of_device_from_db(device_ip: str, sub_if_ip: str) -> SubInterface:
    for intf in get_all_interfaces_of_device_from_db(device_ip) or []:
        if si := intf.subInterfaces.get_or_none(ip_address=sub_if_ip):
            return si


def get_sub_interface_from_db(sub_if_ip: str) -> SubInterface:
    devices = get_device_db_obj()
    for device in devices:
        if si := get_sub_interface_of_device_from_db(device.mgt_ip, sub_if_ip):
            return si


def copy_intfc_object_props(target_intfc: Interface, source_intfc: Interface):
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
    intfcs = get_all_interfaces_of_device_from_db(device_ip)
    return [intfc.name for intfc in intfcs] if intfcs else None
