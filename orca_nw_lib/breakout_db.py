from orca_nw_lib.interface_db import (get_all_interfaces_of_device_from_db,
                                      get_interface_of_device_from_db)
from orca_nw_lib.utils import get_logging

from orca_nw_lib.graph_db_models import Device

from orca_nw_lib.graph_db_models import Breakout

_logger = get_logging().getLogger(__name__)


def get_breakout_from_db(device_ip: str, if_name=None) -> list[Breakout] | Breakout:
    """
    Get the breakout configuration of a device from the database.

    Args:
        device_ip (str): The IP address of the device.
        if_name (str): The alias of the interface.
    """
    if if_name:
        interface = get_interface_of_device_from_db(device_ip, if_name)
        return interface.breakout.get_or_none(if_name=if_name)
    else:
        breakouts = []
        interfaces = get_all_interfaces_of_device_from_db(device_ip)
        for i in interfaces:
            if i.breakout:
                breakouts.append(*i.breakout.all())
        return breakouts


def copy_breakout_obj(target_obj: Breakout, src_obj: Breakout):
    """
    Copy the breakout configuration from one object to another.

    Args:
        target_obj (Breakout): The target object.
        src_obj (Breakout): The source object.

    Returns:
        None
    """
    target_obj.breakout_mode = src_obj.breakout_mode
    target_obj.if_name = src_obj.if_name
    target_obj.port = src_obj.port
    target_obj.lanes = src_obj.lanes
    target_obj.source_lanes = src_obj.source_lanes
    target_obj.target_lanes = src_obj.target_lanes
    target_obj.status = src_obj.status


def insert_device_breakout_in_db(device: Device, breakout_obj: dict):
    """
    Insert the breakout configuration of a device into the database.

    Args:
        device (Device): The device object.
        breakout_obj (dict): The breakout configuration object.

    Returns:
        None
    """
    _logger.info(f"Inserting breakout on device {device.mgt_ip}.")
    new_breakout_obj = None
    for breakout, members in breakout_obj.items():
        if existing_breakout := get_breakout_from_db(device.mgt_ip, breakout.if_name):
            # updating breakout node in db
            if existing_breakout.if_name == breakout.if_name:
                copy_breakout_obj(existing_breakout, breakout)
                existing_breakout.save()
                new_breakout_obj = existing_breakout
        else:
            # inserting breakout node in db
            breakout.save()
            new_breakout_obj = breakout
        if new_breakout_obj:
            interface = get_interface_of_device_from_db(device.mgt_ip, breakout.if_name)
            interface.breakout.connect(new_breakout_obj)

    # removing breakout if it exists on db and not on device.
    breakout_obj_from_db = get_breakout_from_db(device.mgt_ip)
    if breakout_obj_from_db:
        for existing_breakout_in_db in breakout_obj_from_db:
            if existing_breakout_in_db not in breakout_obj:
                delete_breakout_member_from_db(
                    device_ip=device.mgt_ip, if_name=existing_breakout_in_db.if_name
                )


def delete_breakout_member_from_db(device_ip: str, if_name: str):
    """
    Deletes the breakout configuration of a device from the database.

    Args:
        device_ip (str): The IP address of the device.
        if_name (str): The name of the interface.
    """
    breakout = get_breakout_from_db(device_ip=device_ip, if_name=if_name)
    if breakout:
        breakout.delete()
