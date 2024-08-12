from orca_nw_lib.port_chnl_db import get_port_chnl_of_device_from_db

from orca_nw_lib.interface_db import get_interface_of_device_from_db

from orca_nw_lib.graph_db_models import Device, STP_PORT

from orca_nw_lib.utils import get_logging

from orca_nw_lib.device_db import get_device_db_obj

_logger = get_logging().getLogger(__name__)


def set_stp_port_config_in_db(
        device_ip: str, if_name: str = None, edge_port: str = None, link_type: str = None, guard: str = None,
        bpdu_guard: bool = None, bpdu_filter: bool = None, portfast: bool = None, uplink_fast: bool = None,
        bpdu_guard_port_shutdown: bool = None, cost: int = None, port_priority: int = None,
        stp_enabled: bool = None
):
    """
    Sets the STP port channel members on a device.

    Parameters:
        device_ip (str): The IP address of the device.
        if_name (str, optional): The interface name. Defaults to None.
        edge_port (str, optional): The edge port. Defaults to None.
        link_type (str, optional): The link type. Defaults to None.
        guard (str, optional): The guard. Defaults to None.
        bpdu_guard (str, optional): The BPDU guard. Defaults to None.
        bpdu_filter (str, optional): The BPDU filter. Defaults to None.
        portfast (str, optional): The portfast. Defaults to None.
        uplink_fast (str, optional): The uplink fast. Defaults to None.
        bpdu_guard_port_shutdown (str, optional): The BPDU guard port shutdown. Defaults to None.
        cost (str, optional): The cost. Defaults to None.
        port_priority (str, optional): The port priority. Defaults to None.
        stp_enabled (str, optional): The STP enabled. Defaults to None.
    """
    if device_ip and if_name:
        stp_port = STP_PORT(
            if_name=if_name,
            edge_port=edge_port,
            link_type=link_type,
            guard=guard,
            bpdu_guard=bpdu_guard,
            bpdu_filter=bpdu_filter,
            portfast=portfast,
            uplink_fast=uplink_fast,
            bpdu_guard_port_shutdown=bpdu_guard_port_shutdown,
            cost=cost,
            port_priority=port_priority,
            stp_enabled=stp_enabled
        )
        device = get_device_db_obj(device_ip)
        if device:
            insert_device_stp_port_in_db(
                device=device, stp_port_obj={stp_port: []}
            )


def get_stp_port_members_from_db(device_ip: str, if_name: str = None):
    """
    Gets the STP port channel members from a device.

    Parameters:
        device_ip (str): The IP address of the device.
        if_name (str, optional): The name of the interface. Defaults to None.
    """
    device = get_device_db_obj(device_ip)
    if if_name is None:
        return device.stp_port.all() if device else None
    else:
        return device.stp_port.get_or_none(if_name=if_name) if device else None


def save_to_db(device_ip: str, stp_port_obj: STP_PORT):
    """
    Saves the STP port channel members to a device.

    Parameters:
        device_ip (str): The IP address of the device.
        stp_port_obj (STP_PORT): The STP_PORT object to save.
    """
    device = get_device_db_obj(device_ip)
    device.stp_port.connect(stp_port_obj)

    # adding stp port interface or portchannel node in db
    if "ethernet" in stp_port_obj.if_name.lower():
        intfc = get_interface_of_device_from_db(device.mgt_ip, stp_port_obj.if_name)
        intfc.stp_port.connect(stp_port_obj)
    elif "portchannel" in stp_port_obj.if_name.lower():
        port_chnl = get_port_chnl_of_device_from_db(device.mgt_ip, stp_port_obj.if_name)
        port_chnl.stp_port.connect(stp_port_obj)


def copy_stp_port_obj(target_obj: STP_PORT, src_obj: STP_PORT):
    """
    Copy the properties of a source STP_GLOBAL object to a target STP_GLOBAL object.

    Args:
        target_obj (STP_GLOBAL): The target STP_GLOBAL object to copy the properties to.
        src_obj (STP_GLOBAL): The source STP_GLOBAL object to copy the properties from.

    Returns:
        None
    """
    target_obj.if_name = src_obj.if_name
    target_obj.edge_port = src_obj.edge_port
    target_obj.link_type = src_obj.link_type
    target_obj.guard = src_obj.guard
    target_obj.bpdu_guard = src_obj.bpdu_guard
    target_obj.bpdu_filter = src_obj.bpdu_filter
    target_obj.portfast = src_obj.portfast
    target_obj.uplink_fast = src_obj.uplink_fast
    target_obj.bpdu_guard_port_shutdown = src_obj.bpdu_guard_port_shutdown
    target_obj.cost = src_obj.cost
    target_obj.port_priority = src_obj.port_priority
    target_obj.stp_enabled = src_obj.stp_enabled


def insert_device_stp_port_in_db(device: Device, stp_port_obj: dict):
    """
    Insert the STP_PORT object in the database.

    Args:
        device (Device): The device object.
        stp_port_obj (dict): The STP port object.
    """
    _logger.info(f"Inserting STP Port on device {device.mgt_ip}.")
    for stp_port, members in stp_port_obj.items():
        if existing_stp_port := get_stp_port_members_from_db(device.mgt_ip, stp_port.if_name):
            # updating stp port node in db
            copy_stp_port_obj(existing_stp_port, stp_port)
            existing_stp_port.save()
            new_port_obj = existing_stp_port
        else:
            # inserting stp port node in db
            stp_port.save()
            new_port_obj = stp_port

        device.stp_port.connect(new_port_obj)

        # adding stp port interface or portchannel node in db
        if "ethernet" in new_port_obj.if_name.lower():
            intfc = get_interface_of_device_from_db(device.mgt_ip, stp_port.if_name)
            intfc.stp_port.connect(new_port_obj)
        elif "portchannel" in new_port_obj.if_name.lower():
            port_chnl = get_port_chnl_of_device_from_db(device.mgt_ip, stp_port.if_name)
            port_chnl.stp_port.connect(new_port_obj)

    # removing stp port if it exists on db and not on device.
    stp_port_obj_from_db = get_stp_port_members_from_db(device.mgt_ip)
    for existing_port_in_db in stp_port_obj_from_db:
        if existing_port_in_db not in stp_port_obj:
            delete_stp_port_member_from_db(device_ip=device.mgt_ip, if_name=existing_port_in_db.if_name)


def delete_stp_port_member_from_db(device_ip: str, if_name: str):
    """
    device_ip (str): The IP address of the device.
    if_name (str): The name of the interface.
    """
    stp_port = get_stp_port_members_from_db(device_ip, if_name)
    if stp_port:
        stp_port.delete()
