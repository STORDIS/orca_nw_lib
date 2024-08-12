from orca_nw_lib.device_db import get_device_db_obj

from orca_nw_lib.utils import get_logging

from orca_nw_lib.graph_db_models import Device, STP_VLAN
from orca_nw_lib.vlan_db import get_vlan_obj_from_db_using_id

_logger = get_logging().getLogger(__name__)


def copy_stp_vlan_obj(target_obj: STP_VLAN, src_obj: STP_VLAN):
    """
    Copy the properties of a source STP_VLAN object to a target STP_VLAN object.

    Args:
        target_obj (STP_VLAN): The target STP_VLAN object to copy the properties to.
        src_obj (STP_VLAN): The source STP_VLAN object to copy the properties from.

    Returns:
        None
    """
    target_obj.vlan_id = src_obj.vlan_id
    target_obj.bridge_priority = src_obj.bridge_priority
    target_obj.forwarding_delay = src_obj.forwarding_delay
    target_obj.hello_time = src_obj.hello_time
    target_obj.max_age = src_obj.max_age


def insert_device_stp_vlan_in_db(device: Device, stp_vlan_obj: dict):
    """
    Inserts the given STP VLAN object into the database for the specified device.

    Args:
        device (Device): The device object representing the device to insert the STP VLAN into.
        stp_vlan_obj (dict): A dictionary containing the STP VLAN object to insert, mapped to its members.

    Returns:
        None
    """
    _logger.info(f"Inserting STP Vlan on device {device.mgt_ip}.")
    for stp_vlan, members in stp_vlan_obj.items():
        if existing_stp_valn := get_stp_vlan_from_db(device.mgt_ip, stp_vlan.vlan_id):
            # updating stp vlan node in db
            copy_stp_vlan_obj(existing_stp_valn, stp_vlan)
            existing_stp_valn.save()
            new_vlan_obj = existing_stp_valn
        else:
            # inserting stp vlan node in db
            stp_vlan.save()
            new_vlan_obj = stp_vlan

        device.stp_vlan.connect(new_vlan_obj)

        # adding stp vlan  node in db
        vlan = get_vlan_obj_from_db_using_id(device.mgt_ip, stp_vlan.vlan_id)
        if vlan:
            vlan.stp_vlan.connect(new_vlan_obj)

    # removing stp vlan if it exists on db and not on device.
    stp_vlan_obj_from_db = get_stp_vlan_from_db(device.mgt_ip)
    for existing_vlan_in_db in stp_vlan_obj_from_db:
        if existing_vlan_in_db not in stp_vlan_obj:
            delete_stp_vlan_from_db(device_ip=device.mgt_ip, vlan_id=existing_vlan_in_db.vlan_id)


def get_stp_vlan_from_db(device_ip: str, vlan_id: int = None):
    """
    Retrieves the STP VLAN object from the database based on the device IP and VLAN ID.

    Args:
        device_ip (str): The IP address of the device.
        vlan_id (int, optional): The VLAN ID to retrieve. Defaults to None.

    Returns:
        STP_VLAN or None: The STP VLAN object if found, or None if not found.
            If vlan_id is not provided, returns a list of all STP VLAN objects for the device.
    """
    device: Device = get_device_db_obj(device_ip)
    if device:
        return device.stp_vlan.get_or_none(vlan_id=vlan_id) if vlan_id else device.stp_vlan.all()


def delete_stp_vlan_from_db(device_ip: str, vlan_id: int = None):
    """
    Deletes a STP VLAN object from the database based on the device IP and VLAN ID.

    Args:
        device_ip (str): The IP address of the device.
        vlan_id (int, optional): The VLAN ID to delete. Defaults to None.

    Returns:
        None
    """
    device: Device = get_device_db_obj(device_ip)
    stp_vlan = device.stp_vlan.get_or_none(vlan_id=vlan_id) if device else None
    if stp_vlan:
        stp_vlan.delete()
