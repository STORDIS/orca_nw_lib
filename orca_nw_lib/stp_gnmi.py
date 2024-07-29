from orca_nw_lib.gnmi_util import (get_gnmi_path,
                                   create_gnmi_update,
                                   send_gnmi_set,
                                   create_req_for_update,
                                   send_gnmi_get,
                                   get_gnmi_del_req, get_gnmi_del_reqs)
from orca_nw_lib.utils import format_and_get_trunk_vlans


def get_stp_global_config_path():
    """
    Returns the path of the STP global config.
    """
    return get_gnmi_path(
        "openconfig-spanning-tree:stp/global/config"
    )


def config_stp_global_on_device(
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
    request_data = {}
    if enabled_protocol is not None:
        request_data["enabled-protocol"] = [str(i) for i in enabled_protocol]
    if bpdu_filter is not None:
        request_data["bpdu-filter"] = bpdu_filter
    if hello_time:
        request_data["openconfig-spanning-tree-ext:hello-time"] = hello_time
    if max_age:
        request_data["openconfig-spanning-tree-ext:max-age"] = max_age
    if forwarding_delay:
        request_data["openconfig-spanning-tree-ext:forwarding-delay"] = forwarding_delay
    if bridge_priority:
        request_data["openconfig-spanning-tree-ext:bridge-priority"] = bridge_priority
    if loop_guard is not None:
        request_data["openconfig-spanning-tree-ext:loop-guard"] = loop_guard
    if rootguard_timeout is not None:
        request_data["openconfig-spanning-tree-ext:rootguard-timeout"] = rootguard_timeout
    if portfast is not None:
        request_data["openconfig-spanning-tree-ext:portfast"] = portfast
    if disabled_vlans is not None:
        request_data["openconfig-spanning-tree-ext:disabled-vlans"] = disabled_vlans
    request = create_gnmi_update(
        path=get_stp_global_config_path(),
        val={"openconfig-spanning-tree:config": request_data}
    )
    return send_gnmi_set(create_req_for_update([request]), device_ip)


def get_stp_global_config_from_device(device_ip: str):
    """
    Retrieves the global STP configuration from a specified device.

    Parameters:
        device_ip (str): The IP address of the device.

    Returns:
        dict: A dictionary containing the global STP configuration.
    """
    return send_gnmi_get(
        path=[get_stp_global_config_path()],
        device_ip=device_ip
    )


def delete_stp_global_from_device(device_ip: str):
    """
    Deletes the global STP configuration from a specified device.

    Parameters:
        device_ip (str): The IP address of the device.

    Returns:
        dict: A dictionary containing the global STP configuration.
    """
    return send_gnmi_set(
        req=get_gnmi_del_req(
            path=get_stp_global_config_path()
        ),
        device_ip=device_ip
    )


def delete_stp_global_disabled_vlans_from_device(device_ip: str, disabled_vlans: list):
    """
    Deletes the global STP configuration from a specified device.

    Parameters:
        device_ip (str): The IP address of the device.
        disabled_vlans (list): List of disabled VLANs.

    Returns:
        dict: A dictionary containing the global STP configuration.
    """
    requests = []
    for i in format_and_get_trunk_vlans(disabled_vlans):
        requests.append(
            get_gnmi_path(
                f"/openconfig-spanning-tree:stp/global/config/openconfig-spanning-tree-ext:disabled-vlans[disabled-vlans={i}]"
            )
        )
    return send_gnmi_set(req=get_gnmi_del_reqs(requests), device_ip=device_ip)
