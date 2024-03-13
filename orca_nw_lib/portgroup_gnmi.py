from orca_nw_lib.common import Speed
from orca_nw_lib.gnmi_pb2 import Path, PathElem
from orca_nw_lib.gnmi_util import (
    create_gnmi_update,
    create_req_for_update,
    send_gnmi_get,
    send_gnmi_set,
)


def _get_port_groups_base_path():
    """
    Generates the base path for the port groups in the OpenConfig model.

    Returns:
        Path: The base path for the port groups.
    """

    return Path(
        target="openconfig",
        #origin="openconfig-port-group",
        elem=[
            PathElem(
                name="openconfig-port-group:port-groups",
            ),
        ],
    )


def _get_port_groups_path():
    """
    Generates the base path for the port groups in the OpenConfig model.

    Returns:
        Path: The base path for the port groups.
    """
    path = _get_port_groups_base_path()
    path.elem.append(
        PathElem(
            name="port-group",
        )
    )
    return path


def _get_port_group_path(port_group_id:str = None):
    """
    Generates the base path for the port groups in the OpenConfig model.

    Returns:
        Path: The base path for the port groups.
    """
    path = _get_port_groups_base_path()
    if port_group_id:
        path.elem.append(PathElem(name="port-group", key={"id": port_group_id}))
    else:
        path.elem.append(PathElem(name="port-group"))
    return path


def _get_port_group_config_path(port_group_id:str):
    """
    Generates the base path for the port groups in the OpenConfig model.

    Returns:
        Path: The base path for the port groups.
    """
    path = _get_port_group_path(port_group_id)
    path.elem.append(PathElem(name="config"))
    return path


def get_port_group_speed_path(port_group_id:str):
    """
    Generates the base path for the port groups in the OpenConfig model.

    Returns:
        Path: The base path for the port groups.
    """

    path = _get_port_group_config_path(port_group_id)
    path.elem.append(PathElem(name="speed"))
    return path


def get_port_chnl_mem_base_path():
    """
    Generates the base path for the port groups in the OpenConfig model.

    Returns:
        Path: The base path for the port groups.
    """

    return Path(
        target="openconfig",
        origin="sonic-portchannel",
        elem=[PathElem(name="sonic-portchannel"), PathElem(name="PORTCHANNEL_MEMBER")],
    )


def get_port_group_from_device(device_ip: str, port_group_id: str = None):
    """
    Get the port group from a device.

    Args:
        device_ip (str): The IP address of the device.
        id (int, optional): The ID of the port group. Defaults to None.

    Returns:
        The port group obtained from the device.

    """

    return send_gnmi_get(
        device_ip=device_ip, path=[_get_port_group_path(port_group_id)]
    )


def get_port_group_speed_from_device(device_ip: str, port_group_id: str):
    """
    Retrieve the port group speed from a device.

    Args:
        device_ip (str): The IP address of the device.
        id (int): The ID of the port group.

    Returns:
        The port group speed from the device.

    Raises:
        None.
    """
    return send_gnmi_get(
        device_ip=device_ip, path=[get_port_group_speed_path(port_group_id)]
    )


def set_port_group_speed_on_device(device_ip: str, port_group_id: str, speed: Speed):
    """
    Sets the speed of a port group on a device.

    Args:
        device_ip (str): The IP address of the device.
        id (int): The ID of the port group.
        speed (Speed): The desired speed for the port group.

    Returns:
        None: If the GNMI set operation was successful.
    """
    return send_gnmi_set(
        create_req_for_update(
            [
                create_gnmi_update(
                    get_port_group_speed_path(port_group_id),
                    {"openconfig-port-group:speed": speed.get_oc_val()},
                )
            ]
        ),
        device_ip,
    )
