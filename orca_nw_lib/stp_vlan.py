from orca_nw_lib.device_db import get_device_db_obj
from orca_nw_lib.graph_db_models import STP_VLAN
from orca_nw_lib.stp_vlan_db import insert_device_stp_vlan_in_db, get_stp_vlan_from_db

from orca_nw_lib.stp_vlan_gnmi import config_stp_vlan_on_device, get_stp_vlan_from_device, delete_stp_vlan_from_device
from orca_nw_lib.utils import get_logging

_logger = get_logging().getLogger(__name__)


def _create_stp_vlan_graph_object(device_ip: str):
    """
    Create STP graph object

    Args:
        device_ip (str): The IP address of the device
    """
    stp_vlan_config = get_stp_vlan_from_device(device_ip=device_ip)
    stp_vlan_obj_list = {}
    members = []
    _logger.debug(f"Retrieved stp vlan info from device {device_ip} {stp_vlan_config}")
    stp_config_details = stp_vlan_config.get("openconfig-spanning-tree-ext:vlans", [])
    for i in stp_config_details or []:
        stp_vlan_config = i.get("config", {})
        vlan_id = stp_vlan_config.get("vlan-id", None)
        if vlan_id:
            stp_vlan_obj_list[
                STP_VLAN(
                    vlan_id=vlan_id,
                    bridge_priority=stp_vlan_config.get("bridge-priority", None),
                    forwarding_delay=stp_vlan_config.get("forwarding-delay", None),
                    hello_time=stp_vlan_config.get("hello-time", None),
                    max_age=stp_vlan_config.get("max-age", None),
                )
            ] = members
    return stp_vlan_obj_list


def discover_stp_vlan(device_ip: str):
    """
    Discover the STP VLAN configuration on a device or all devices.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        None

    Raises:
        Exception: If there is an error discovering STP VLAN configuration on a device.
    """
    _logger.info("STP VLAN Discovery Started.")
    devices = [get_device_db_obj(device_ip)] if device_ip else get_device_db_obj()
    for device in devices:
        _logger.info(f"Discovering STP VLAN of device {device}.")
        try:
            insert_device_stp_vlan_in_db(
                device, _create_stp_vlan_graph_object(device.mgt_ip)
            )
        except Exception as e:
            _logger.error(
                f"Couldn't discover STP VLAN on device {device_ip}, Reason: {e}"
            )
            raise


def config_stp_vlan(
        device_ip: str, vlan_id: int, bridge_priority: int = None, forwarding_delay: int = None,
        hello_time: int = None, max_age: int = None
):
    """
    Configures the STP VLAN settings on a device.

    Parameters:
        device_ip (str): The IP address of the device.
        vlan_id (int): The VLAN ID to configure.
        bridge_priority (int, optional): The bridge priority value. Defaults to None.
        forwarding_delay (int, optional): The forwarding delay value. Defaults to None.
        hello_time (int, optional): The hello time value. Defaults to None.
        max_age (int, optional): The maximum age value. Defaults to None.

    Raises:
        Exception: If there is an error while configuring STP VLAN on the device.

    """
    try:
        config_stp_vlan_on_device(
            device_ip=device_ip,
            vlan_id=vlan_id,
            bridge_priority=bridge_priority,
            forwarding_delay=forwarding_delay,
            hello_time=hello_time,
            max_age=max_age
        )
    except Exception as e:
        _logger.error(f"Failed to configure STP VLAN on device {device_ip}, Reason: {e}")
        raise
    finally:
        discover_stp_vlan(device_ip=device_ip)


def get_stp_vlan(device_ip: str, vlan_id: int = None):
    """
    Retrieves the STP VLAN configuration from the database based on the provided device IP and VLAN ID.

    Args:
        device_ip (str): The IP address of the device.
        vlan_id (int, optional): The VLAN ID to retrieve the configuration for.
        If not provided, retrieves all VLAN configurations.

    Returns:
        list or dict: A list of STP VLAN objects if `vlan_id` is not provided,
        or a single STP VLAN object if `vlan_id` is provided.
    """
    stp_vlan = get_stp_vlan_from_db(device_ip=device_ip, vlan_id=vlan_id)
    if isinstance(stp_vlan, list):
        return [i.__properties__ for i in stp_vlan]
    else:
        return stp_vlan.__properties__ if stp_vlan else None


def delete_stp_vlan(device_ip: str, vlan_id: int = None):
    """
    Deletes STP VLAN configuration from a device.

    Args:
        device_ip (str): The IP address of the device.
        vlan_id (int, optional): The VLAN ID to delete the configuration for.

    Raises:
        Exception: If there is an error while deleting STP VLAN on the device.

    Returns:
        None
    """
    try:
        delete_stp_vlan_from_device(device_ip=device_ip, vlan_id=vlan_id)
    except Exception as e:
        _logger.error(f"Failed to delete STP VLAN on device {device_ip}, Reason: {e}")
        raise
    finally:
        discover_stp_vlan(device_ip=device_ip)
