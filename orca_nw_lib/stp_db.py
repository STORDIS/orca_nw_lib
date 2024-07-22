from orca_nw_lib.device_db import get_device_db_obj
from orca_nw_lib.graph_db_models import STP_GLOBAL, Device

from orca_nw_lib.utils import get_logging

_logger = get_logging().getLogger(__name__)


def insert_device_stp_in_db(device: Device, stp_obj: dict):
    """
    Inserts the STP (Spanning Tree Protocol) configuration for a given device into the database.

    Args:
        device (Device): The device object for which the STP configuration is being inserted.
        stp_obj (dict): A dictionary containing the STP configuration for the device.
        The keys of the dictionary are the STP instances, and the values are lists of members for each STP instance.

    Returns:
        None
    """
    _logger.info(f"Inserting STP on device {device.mgt_ip}.")
    for stp, members in stp_obj.items():
        if stp_db_obj := get_stp_global_from_db(device.mgt_ip):
            copy_stp_global_obj(stp_db_obj, stp)
            stp_db_obj.save()
            device.stp_global.connect(stp_db_obj)
        else:
            stp.save()
            device.stp_global.connect(stp)
    # removing stp config if it exists on db and not on device.
    stp_obj_from_db = get_stp_global_from_db(device.mgt_ip)
    if stp_obj_from_db not in stp_obj:
        delete_stp_global_from_db(device_ip=device.mgt_ip)


def copy_stp_global_obj(target_obj: STP_GLOBAL, src_obj: STP_GLOBAL):
    """
    Copy the properties of a source STP_GLOBAL object to a target STP_GLOBAL object.

    Args:
        target_obj (STP_GLOBAL): The target STP_GLOBAL object to copy the properties to.
        src_obj (STP_GLOBAL): The source STP_GLOBAL object to copy the properties from.

    Returns:
        None
    """
    target_obj.enabled_protocol = src_obj.enabled_protocol
    target_obj.bpdu_filter = src_obj.bpdu_filter
    target_obj.loop_guard = src_obj.loop_guard
    target_obj.disabled_vlans = src_obj.disabled_vlans
    target_obj.rootguard_timeout = src_obj.rootguard_timeout
    target_obj.portfast = src_obj.portfast
    target_obj.hello_time = src_obj.hello_time
    target_obj.max_age = src_obj.max_age
    target_obj.forwarding_delay = src_obj.forwarding_delay
    target_obj.bridge_priority = src_obj.bridge_priority


def get_stp_global_from_db(device_ip: str):
    """
    Returns the STP_GLOBAL object for the specified device from the database.

    Args:
        device_ip (str): The IP address of the device for which to retrieve the STP_GLOBAL object.

    Returns:
        STP_GLOBAL: The STP_GLOBAL object for the specified device, or None if not found.
    """
    device = get_device_db_obj(device_ip)
    return device.stp_global.get_or_none(device_ip=device_ip) if device else None


def delete_stp_global_from_db(device_ip: str):
    """
    Deletes the STP_GLOBAL object for the specified device from the database.

    Args:
        device_ip (str): The IP address of the device for which to delete the STP_GLOBAL object.

    Returns:
        None
    """
    stp_obj = get_stp_global_from_db(device_ip)
    if stp_obj:
        stp_obj.delete()


def set_stp_config_in_db(
        device_ip: str, enabled_protocol: list | None, bpdu_filter: bool, bridge_priority: int,
        max_age: int, hello_time: int, forwarding_delay: int, disabled_vlans: list[int] = None,
        rootguard_timeout: int = None, loop_guard: bool = None, portfast: bool = None,
):
    """
    Sets the STP configuration for the specified device in the database.

    Args:
        device_ip (str): The IP address of the device for which to set the STP configuration.
        enabled_protocol (str): The list of enabled STP protocols.
        bpdu_filter (bool): Whether to enable or disable the BPDU filter.
        loop_guard (bool): Whether to enable or disable the loop guard.
        disabled_vlans (list): The list of disabled VLANs.
        rootguard_timeout (int): The root guard timeout value.
        portfast (bool): Whether to enable or disable portfast.
        hello_time (int): The hello time value.
        max_age (int): The maximum age value.
        forwarding_delay (int): The forwarding delay value.
        bridge_priority (int): The bridge priority value.

    Returns:
        None
    """
    stp_obj = get_stp_global_from_db(device_ip)
    if stp_obj:
        if enabled_protocol is not None:
            stp_obj.enabled_protocol = enabled_protocol
        if bpdu_filter is not None:
            stp_obj.bpdu_filter = bpdu_filter
        if loop_guard is not None:
            stp_obj.loop_guard = loop_guard
        if disabled_vlans is not None:
            stp_obj.disabled_vlans = disabled_vlans
        if rootguard_timeout is not None:
            stp_obj.rootguard_timeout = rootguard_timeout
        if portfast is not None:
            stp_obj.portfast = portfast
        if hello_time is not None:
            stp_obj.hello_time = hello_time
        if max_age is not None:
            stp_obj.max_age = max_age
        if forwarding_delay is not None:
            stp_obj.forwarding_delay = forwarding_delay
        if bridge_priority is not None:
            stp_obj.bridge_priority = bridge_priority
        if enabled_protocol is not None:
            stp_obj.save()
            _logger.info(f"Updated STP config on DB for {device_ip}.")
