from orca_nw_lib.common import STPEnabledProtocol
from orca_nw_lib.device_db import get_device_db_obj
from orca_nw_lib.graph_db_models import STP_GLOBAL
from orca_nw_lib.stp_db import insert_device_stp_in_db, get_stp_global_from_db

from orca_nw_lib.utils import get_logging, format_and_get_trunk_vlans

from orca_nw_lib.stp_gnmi import (config_stp_global_on_device,
                                  get_stp_global_config_from_device,
                                  delete_stp_global_from_device, delete_stp_global_disabled_vlans_from_device)

_logger = get_logging().getLogger(__name__)


def _create_stp_graph_object(device_ip: str):
    """
    Create STP graph object

    Args:
        device_ip (str): The IP address of the device
    """
    stp_global_config = get_stp_global_config_from_device(device_ip=device_ip)
    stp_obj_list = {}
    members = []
    _logger.debug(f"Retrieved stp global info from device {device_ip} {stp_global_config}")
    stp_config_details = stp_global_config.get("openconfig-spanning-tree:config", {})
    enabled_protocols = [
        STPEnabledProtocol.getEnabledProtocolStrFromOCStr(i)
        for i in stp_config_details.get("enabled-protocol", []) or []
    ]
    if stp_config_details and len(enabled_protocols):
        disabled_vlans = stp_config_details.get("openconfig-spanning-tree-ext:disabled-vlans", [])
        stp_obj_list[
            STP_GLOBAL(
                device_ip=device_ip,
                enabled_protocol=enabled_protocols,
                bpdu_filter=stp_config_details.get("bpdu-filter", None),
                loop_guard=stp_config_details.get("loop-guard", None),
                disabled_vlans=format_and_get_trunk_vlans(disabled_vlans) if disabled_vlans else None,
                rootguard_timeout=stp_config_details.get("openconfig-spanning-tree-ext:rootguard-timeout", None),
                portfast=stp_config_details.get("openconfig-spanning-tree-ext:portfast", None),
                hello_time=stp_config_details.get("openconfig-spanning-tree-ext:hello-time", None),
                max_age=stp_config_details.get("openconfig-spanning-tree-ext:max-age", None),
                forwarding_delay=stp_config_details.get("openconfig-spanning-tree-ext:forwarding-delay", None),
                bridge_priority=stp_config_details.get("openconfig-spanning-tree-ext:bridge-priority", None),
            )
        ] = members
    return stp_obj_list


def discover_stp(device_ip: str = None):
    """
    Discover STP on device

    Args:
        device_ip (str): The IP address of the device
    """
    _logger.info("Discovering STP.")
    devices = [get_device_db_obj(device_ip)] if device_ip else get_device_db_obj()
    for device in devices:
        _logger.info(f"Discovering STP on device {device}.")
        try:
            insert_device_stp_in_db(device, _create_stp_graph_object(device.mgt_ip))
        except Exception as e:
            _logger.error(f"Failed to discover STP, Reason: {e}")
            raise


def config_stp_global(
        device_ip: str, enabled_protocol: list, bpdu_filter: bool, bridge_priority: int,
        max_age: int, hello_time: int, forwarding_delay: int, disabled_vlans: list[int] = None,
        rootguard_timeout: int = None, loop_guard: bool = None, portfast: bool = None,
):
    """
    Configures the STP global settings on a device.

    Parameters:
        device_ip (str): The IP address of the device.
        enabled_protocol (list): List of enabled STP protocols. Valid Values: PVST, MSTP, RSTP, RAPID_PVST.
        bpdu_filter (bool): Enable/Disable BPDU filter. Valid Values: True, False.
        bridge_priority (int): The bridge priority value. Valid Range: 0-61440, only multiples of 4096.
        max_age (int): Maximum age value for STP. Valid Range: 6-40.
        hello_time (int): Hello time value for STP. Valid Range: 1-10.
        forwarding_delay (int): Forwarding delay value for STP. Valid Range: 4-30.
        disabled_vlans (list[int], optional): List of disabled VLANs. Defaults to None.
        rootguard_timeout (int, optional): Root guard timeout value. Valid Range to 5-600.
        loop_guard (bool, optional): Enable/Disable loop guard. Valid Values: True, False.
        portfast (bool, optional): Enable/Disable portfast. Valid Values: True, False.

    Raises:
        Exception: If there is an error while configuring STP on the device.

    """
    try:
        config_stp_global_on_device(
            device_ip=device_ip,
            enabled_protocol=enabled_protocol,
            bpdu_filter=bpdu_filter,
            loop_guard=loop_guard,
            disabled_vlans=disabled_vlans,
            rootguard_timeout=rootguard_timeout,
            portfast=portfast,
            hello_time=hello_time,
            max_age=max_age,
            forwarding_delay=forwarding_delay,
            bridge_priority=bridge_priority
        )
    except Exception as e:
        _logger.error(f"Failed to configure STP on device {device_ip}, Reason: {e}")
        raise
    finally:
        discover_stp()


def get_stp_global_config(device_ip: str):
    """
    Retrieves the STP global configuration for a specific device.

    Parameters:
        device_ip (str): The IP address of the device.

    Returns:
        Union[Dict[str, Any], None]: The STP global configuration properties if available, otherwise None.
    """
    stp = get_stp_global_from_db(device_ip)
    return stp.__properties__ if stp else None


def delete_stp_global_config(device_ip: str):
    """
    Deletes the STP global configuration on a device.

    Parameters:
        device_ip (str): The IP address of the device.

    Raises:
        Exception: If there is an error while deleting STP on the device.
    """
    try:
        delete_stp_global_from_device(device_ip=device_ip)
    except Exception as e:
        _logger.error(f"Failed to delete STP on device {device_ip}, Reason: {e}")
        raise
    finally:
        discover_stp()


def delete_stp_global_config_disabled_vlans(device_ip: str, disabled_vlans: list):
    """
    Deletes the STP global configuration disabled VLANs on a device.

    Parameters:
        device_ip (str): The IP address of the device.
        disabled_vlans (list): List of disabled VLANs.

    Raises:
        Exception: If there is an error while deleting STP on the device.
    """
    try:
        delete_stp_global_disabled_vlans_from_device(device_ip=device_ip, disabled_vlans=disabled_vlans)
    except Exception as e:
        _logger.error(f"Failed to delete STP on device {device_ip}, Reason: {e}")
        raise
    finally:
        discover_stp(device_ip=device_ip)

