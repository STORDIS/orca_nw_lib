from urllib.parse import quote_plus

from orca_nw_lib.gnmi_util import (get_gnmi_path,
                                   send_gnmi_set,
                                   create_req_for_update,
                                   create_gnmi_update,
                                   send_gnmi_get,
                                   get_gnmi_del_req)
from orca_nw_lib.utils import get_component_name_from_if_alias, get_logging

_logger = get_logging().getLogger(__name__)


def get_breakout_path(if_alias):
    """
    Returns the GNMI path for the breakout configuration.

    Args:
        if_alias (str): The alias of the interface.

    Returns:
        The GNMI path for the breakout configuration.
    """
    return get_gnmi_path(
        f"openconfig-platform:components/component[name={quote_plus(if_alias)}]/port/openconfig-platform-port:breakout-mode/groups"
    )


def get_breakout_sonic_path(if_name: str):
    """
    Returns the SONiC path for the breakout configuration.

    Args:
        if_name (str): The name of the interface.

    Returns:
        The SONiC path for the breakout configuration.
    """
    if if_name:
        return get_gnmi_path(
            f"sonic-port-breakout:sonic-port-breakout/BREAKOUT_CFG/BREAKOUT_CFG_LIST[ifname={if_name}]"
        )
    else:
        return get_gnmi_path("sonic-port-breakout:sonic-port-breakout/BREAKOUT_CFG/BREAKOUT_CFG_LIST")


def config_breakout_on_device(
        device_ip: str, if_name: str, if_alias: str, index: int = None, num_breakouts: int = None,
        breakout_speed: str = None, num_physical_channels: int = None
):
    """
    Configures the interface breakout on a device.

    Args:
        device_ip (str): The IP address of the device.
        if_name (str): Name of the interface.
        if_alias (str): The alias of the interface.
        index (int): The index of the breakout.
        num_breakouts (int): The number of breakouts.
        breakout_speed (str): The breakout speed.
        num_physical_channels (int): The number of physical channels.
    """
    if_alias = get_component_name_from_if_alias(if_alias)
    path = get_breakout_path(if_alias)
    config = {}
    if index is not None:
        config["index"] = index
    if num_breakouts is not None:
        config["num-breakouts"] = num_breakouts
    if breakout_speed:
        config["breakout-speed"] = breakout_speed
    if num_physical_channels is not None:
        config["num-physical-channels"] = num_physical_channels
    request = create_gnmi_update(
        path=path,
        val={
            "openconfig-platform-port:groups": {
                "group": [
                    {
                        "index": index,
                        "config": config
                    }
                ]
            }
        }
    )
    # updating cannot be done on breakout configuration because its status is always InProgress on the device.
    # so, delete the breakout if it already exists and recreate it with new config.
    try:
        delete_breakout_from_device(device_ip, if_name)
    except Exception as e:
        _logger.error(
            f"Deleting interface breakout on interface {if_name} on device {device_ip} failed, Reason: {e}"
        )
        pass
    return send_gnmi_set(
        create_req_for_update([request]), device_ip
    )


def get_breakout_from_device(device_ip: str, if_name: str = None):
    """
    Retrieves the breakout configuration from a device.

    Args:
        device_ip (str): The IP address of the device.
        if_name (str): The name of the interface.
    Returns:
        The breakout configuration as a dictionary.
    """
    return send_gnmi_get(
        device_ip=device_ip,
        path=[get_breakout_sonic_path(if_name=if_name)],
    )


def delete_breakout_from_device(device_ip: str, if_name: str):
    """
    Deletes the breakout configuration on a device.

    Args:
        device_ip (str): The IP address of the device.
        if_name (str): The alias of the interface.
    """

    path = get_breakout_sonic_path(if_name=if_name)
    return send_gnmi_set(
        get_gnmi_del_req(path=path), device_ip=device_ip
    )
