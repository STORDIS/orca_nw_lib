from orca_nw_lib.utils import get_logging

from orca_nw_lib.gnmi_util import (get_gnmi_path,
                                   send_gnmi_set,
                                   create_req_for_update,
                                   create_gnmi_update,
                                   get_gnmi_del_req,
                                   send_gnmi_get, )

_logger = get_logging().getLogger(__name__)


def get_stp_port_path(if_name: str = None):
    """
    Returns the GNMi path for the specified STP port interface.

    Args:
        if_name (str, optional): The name of the STP port interface. Defaults to None.

    Returns:
        Path: The GNMi path for the specified STP port interface.
    """
    if if_name is None:
        return get_gnmi_path("/openconfig-spanning-tree:stp/interfaces/interface")
    return get_gnmi_path(
        f"/openconfig-spanning-tree:stp/interfaces/interface[name={if_name}]"
    )


def add_stp_port_members_on_device(
        device_ip: str, if_name: str, bpdu_guard: bool, uplink_fast: bool, stp_enabled: bool,
        link_type: str = None, guard: str = None, edge_port: str = None, bpdu_filter: bool = None,
        portfast: bool = None, bpdu_guard_port_shutdown: bool = None,
        cost: int = None, port_priority: int = None,
):
    """
    Adds the STP port channel members on a device.

    Parameters:
        device_ip (str, Required): The IP address of the device.
        if_name (str, Required): The name of the interface.
        bpdu_guard (bool, Required): Enable/Disable BPDU guard. Valid Values: True, False.
        uplink_fast (bool, Required): Enable/Disable uplink fast. Valid Values: True, False.
        stp_enabled (bool, Required): Enable/Disable STP. Valid Values: True, False.
        edge_port (str, Optional): The name of the edge port. Valid Values: EDGE_AUTO, EDGE_ENABLE, EDGE_DISABLE.
        link_type (str, Optional): The type of the link. Valid Values: P2P, SHARED.
        guard (str, Optional): The guard. Valid Values: NONE, ROOT, LOOP.
        bpdu_filter (bool, Optional): Enable/Disable BPDU filter. Valid Values: True, False.
        portfast (bool, Optional): Enable/Disable portfast. Valid Values: True, False.
        bpdu_guard_port_shutdown (bool, Optional): Enable/Disable BPDU guard port shutdown. Valid Values: True, False.
        cost (int, Optional): The cost. Valid Range: 1-200000000.
        port_priority (int, Optional): The port priority. Valid Range: 0-240.
    Returns:
        dict: A dictionary containing the STP port channel members.
    Raises:
        Exception: If there is an error while adding STP on the device.
    """
    path = get_stp_port_path(if_name)
    req_data = {
        "name": if_name,
    }
    if edge_port:
        req_data["edge-port"] = str(edge_port)
    if link_type:
        req_data["link-type"] = str(link_type)
    if guard:
        req_data["guard"] = str(guard)
    if bpdu_guard is not None:
        req_data["bpdu-guard"] = bpdu_guard
    if bpdu_filter is not None:
        req_data["bpdu-filter"] = bpdu_filter
    if portfast is not None:
        req_data["openconfig-spanning-tree-ext:portfast"] = portfast
    if uplink_fast is not None:
        req_data["openconfig-spanning-tree-ext:uplink-fast"] = uplink_fast
    if bpdu_guard_port_shutdown is not None:
        req_data["openconfig-spanning-tree-ext:bpdu-guard-port-shutdown"] = bpdu_guard_port_shutdown
    if cost:
        req_data["openconfig-spanning-tree-ext:cost"] = cost
    if port_priority:
        req_data["openconfig-spanning-tree-ext:port-priority"] = port_priority
    if stp_enabled is not None:
        req_data["openconfig-spanning-tree-ext:spanning-tree-enable"] = stp_enabled

    # deleting stp port config if exists before adding because subscribe does not support update.
    # therefore deleting and adding again.
    try:
        delete_stp_port_member_from_device(device_ip=device_ip, if_name=if_name)
    except Exception as e:
        _logger.error(e)

    # adding stp port config
    return send_gnmi_set(
        req=create_req_for_update(
            [create_gnmi_update(path=path, val={
                "openconfig-spanning-tree:interface": [
                    {
                        "name": if_name,
                        "config": req_data
                    }
                ]
            })]
        ),
        device_ip=device_ip
    )


def get_stp_port_members_from_device(device_ip: str, if_name: str = None):
    """
    Retrieves the STP port channel members from a device.

    Parameters:
        device_ip (str): The IP address of the device.
        if_name (str, optional): The name of the interface. Defaults to None.

    Returns:
        dict: A dictionary containing the STP port channel members.
    """
    path = get_stp_port_path(if_name)
    response = send_gnmi_get(path=[path], device_ip=device_ip)
    return response if response else {}


def delete_stp_port_member_from_device(device_ip: str, if_name: str = None):
    """
    Deletes the STP port channel members from a device.

    Parameters:
        device_ip (str): The IP address of the device.
        if_name (str, optional): The name of the interface. Defaults to None.

    Returns:
        dict: A dictionary containing the STP port channel members.
    """
    path = get_stp_port_path(if_name)
    return send_gnmi_set(
        get_gnmi_del_req(path=path), device_ip=device_ip
    )
