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
        device_ip: str, if_name: str = None, edge_port: str = None, link_type: str = None, guard: str = None,
        bpdu_guard: bool = None, bpdu_filter: bool = None, portfast: bool = None, uplink_fast: bool = None,
        bpdu_guard_port_shutdown: bool = None, cost: int = None, port_priority: int = None,
        stp_enabled: bool = None
):
    """
    Adds the STP port channel members on a device.

    Parameters:
        device_ip (str): The IP address of the device.
        if_name (str, optional): The name of the interface. Defaults to None.
        edge_port (str, optional): The name of the edge port. Defaults to None.
        link_type (str, optional): The link type. Defaults to None.
        guard (str, optional): The guard. Defaults to None.
        bpdu_guard (str, optional): The bpdu guard. Defaults to None.
        bpdu_filter (str, optional): The bpdu filter. Defaults to None.
        portfast (str, optional): The portfast. Defaults to None.
        uplink_fast (str, optional): The uplink fast. Defaults to None.
        bpdu_guard_port_shutdown (str, optional): The bpdu guard port shutdown. Defaults to None.
        cost (str, optional): The cost. Defaults to None.
        port_priority (str, optional): The port priority. Defaults to None.
        stp_enabled (str, optional): The STP enabled. Defaults to None.
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
    return send_gnmi_get(path=[path], device_ip=device_ip)


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
