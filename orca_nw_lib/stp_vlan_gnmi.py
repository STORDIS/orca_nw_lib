from orca_nw_lib.gnmi_pb2 import Path

from orca_nw_lib.gnmi_util import (send_gnmi_set,
                                   get_gnmi_path,
                                   create_gnmi_update,
                                   create_req_for_update,
                                   send_gnmi_get,
                                   get_gnmi_del_req)


def get_stp_vlan_path(vlan_id: int = None) -> Path:
    """
    Returns the path to the STP VLAN configuration.

    Args:
        vlan_id (int, optional): The VLAN ID. Defaults to None.
    Returns:
        Path: The path to the STP VLAN configuration.
    """
    if vlan_id:
        get_gnmi_path(f"/openconfig-spanning-tree:stp/openconfig-spanning-tree-ext:pvst/vlans[vlan_id={vlan_id}]")
    return get_gnmi_path(f"/openconfig-spanning-tree:stp/openconfig-spanning-tree-ext:pvst/vlans")


def config_stp_vlan_on_device(
        device_ip: str, vlan_id: int, bridge_priority: int = None, forwarding_delay: int = None,
        hello_time: int = None, max_age: int = None
):
    """
    Configures STP on a device.

    Args:
        device_ip (str): The IP address of the device.
        vlan_id (int): The VLAN ID.
        bridge_priority (int, optional): The bridge priority. Defaults to None.
        forwarding_delay (int, optional): The forwarding delay. Defaults to None.
        hello_time (int, optional): The hello time. Defaults to None.
        max_age (int, optional): The maximum age. Defaults to None.

    Raises:
        Exception: If there is an error while configuring STP on the device.

    Returns:
        The result of sending a GNMI set request to configure STP on the device.
    """
    config = {
        "vlan-id": vlan_id,
    }
    if bridge_priority:
        config["bridge-priority"] = bridge_priority
    if forwarding_delay:
        config["forwarding-delay"] = forwarding_delay
    if hello_time:
        config["hello-time"] = hello_time
    if max_age:
        config["max-age"] = max_age
    request = create_gnmi_update(
        path=get_stp_vlan_path(),
        val={
            "openconfig-spanning-tree-ext:vlans": [
                {
                    "vlan-id": vlan_id,
                    "config": config
                }
            ]
        }
    )
    return send_gnmi_set(create_req_for_update([request]), device_ip)


def get_stp_vlan_from_device(device_ip: str, vlan_id: int = None):
    """
    Gets STP VLAN configuration from a device.

    Args:
        device_ip (str): The IP address of the device.
        vlan_id (int): The VLAN ID.

    Returns:
        The result of sending a GNMI get request to get STP VLAN configuration from the device.
    """
    try:
        response = send_gnmi_get(
            device_ip=device_ip,
            path=[get_stp_vlan_path(vlan_id=vlan_id)],
        )
        return response if response else {}
    except Exception:
        return {}


def delete_stp_vlan_from_device(device_ip: str, vlan_id: int):
    """
    Deletes STP VLAN configuration from a device.

    Args:
        device_ip (str): The IP address of the device.
        vlan_id (int): The VLAN ID.

    Returns:
        The result of sending a GNMI set request to delete STP VLAN configuration from the device.
    """
    return send_gnmi_set(
        device_ip=device_ip,
        req=get_gnmi_del_req(
            path=get_stp_vlan_path()
        )
    )
