from orca_nw_lib.utils import get_logging
from .breakout_gnmi import config_breakout_on_device, get_breakout_from_device, delete_breakout_from_device

from .breakout_db import get_breakout_from_db, insert_device_breakout_in_db
from .device_db import get_device_db_obj
from .graph_db_models import Breakout

_logger = get_logging().getLogger(__name__)


def _create_device_breakout_graph_object(device_ip: str, if_name: str = None):
    """
    Creates the breakout configuration graph object for a device.

    Args:
        device_ip (str): The IP address of the device.
        if_name (str): The name of the interface.

    Returns:
        The breakout configuration graph object.
    """
    breakout = get_breakout_from_device(device_ip).get(
        "sonic-port-breakout:BREAKOUT_CFG_LIST", []
    )
    breakout_obj_list = {}
    members = []
    for i in breakout:
        breakout_obj_list[
            Breakout(
                breakout_mode=i.get("brkout_mode"),
                if_name=i.get("ifname"),
                port=i.get("port"),
                lanes=i.get("lanes"),
                source_lanes=i.get("source_lanes"),
                target_lanes=i.get("target_lanes"),
                status=i.get("status"),
            )
        ] = members
    return breakout_obj_list


def discover_breakout(device_ip: str, if_name: str):
    """
    Discovers the breakout configuration on a device.

    Args:
        device_ip (str): The IP address of the device.
        if_name (str): The name of the interface.

    Returns:
        None
    """
    _logger.info(f"Discovering breakout on device {device_ip}.")
    devices = [get_device_db_obj(device_ip)] if device_ip else get_device_db_obj()
    for device in devices:
        _logger.info(f"Discovering breakout on device {device}.")
        try:
            insert_device_breakout_in_db(
                device, _create_device_breakout_graph_object(device.mgt_ip, if_name)
            )
        except Exception as e:
            _logger.error(f"Failed to discover breakout, Reason: {e}")
            raise


def config_breakout(
        device_ip: str, if_name: str, if_alias: str, index: int = None, num_breakouts: int = None,
        breakout_speed: str = None, num_physical_channels: int = None
):
    """
    Configures the interface breakout on a device.

    Args:
        device_ip (str): The IP address of the device.
        if_name (str): The name of the interface.
        if_alias (str): The alias of the interface.
        index (int): The index of the breakout.
        num_breakouts (int): The number of breakouts.
        breakout_speed (str): The breakout speed.
        num_physical_channels (int): The number of physical channels.

    Returns:
        None
    """
    _logger.info(f"Configuring interface breakout on interface {if_alias}.")
    try:
        config_breakout_on_device(
            device_ip=device_ip,
            if_name=if_name,
            if_alias=if_alias,
            index=index,
            num_breakouts=num_breakouts,
            breakout_speed=breakout_speed,
            num_physical_channels=num_physical_channels
        )
    except Exception as e:
        _logger.error(
            f"Configuring interface breakout on interface {if_alias} on device {device_ip} failed, Reason: {e}"
        )
        raise
    finally:
        discover_breakout(device_ip, if_name=if_name)


def get_breakout(device_ip: str, if_name: str = None):
    """
    Retrieves the breakout configuration from a device.

    Args:
        device_ip (str): The IP address of the device.
        if_name (str): The name of the interface.

    Returns:
        The breakout configuration as a dictionary.
    """
    data = get_breakout_from_db(device_ip, if_name)
    if data:
        if isinstance(data, list):
            return [i.__properties__ for i in data]
        else:
            return data.__properties__


def delete_breakout(device_ip: str, if_name: str):
    """
    Deletes the breakout configuration from a device.

    Args:
        device_ip (str): The IP address of the device.
        if_name (str): Name of the interface.
    Returns:
        None
    """
    _logger.info(f"Deleting interface breakout on interface {if_name}.")
    try:
        delete_breakout_from_device(device_ip, if_name)
    except Exception as e:
        _logger.error(
            f"Deleting interface breakout on interface {if_name} on device {device_ip} failed, Reason: {e}"
        )
        raise
    finally:
        discover_breakout(device_ip, if_name)
