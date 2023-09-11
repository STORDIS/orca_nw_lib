from orca_nw_lib.common import VlanTagMode
from orca_nw_lib.gnmi_pb2 import Path, PathElem
from orca_nw_lib.gnmi_util import (
    create_gnmi_update,
    create_req_for_update,
    get_gnmi_del_req,
    send_gnmi_get,
    send_gnmi_set,
)


def get_sonic_vlan_base_path() -> Path:
    """
    Generates a `Path` object for the sonic-vlan base path.

    Returns:
        Path: The `Path` object representing the sonic-vlan base path.
    """

    return Path(
        target="openconfig",
        origin="sonic-vlan",
        elem=[
            PathElem(
                name="sonic-vlan",
            )
        ],
    )


def get_vlan_table_list_path(vlan_name=None):
    path = get_sonic_vlan_base_path()
    path.elem.append(PathElem(name="VLAN_TABLE"))
    path.elem.append(
        PathElem(name="VLAN_TABLE_LIST")
    ) if not vlan_name else path.elem.append(
        PathElem(name="VLAN_TABLE_LIST", key={"name": vlan_name})
    )
    return path


def get_vlan_mem_path(vlan_name: str = None, intf_name: str = None):
    path = get_sonic_vlan_base_path()
    path.elem.append(PathElem(name="VLAN_MEMBER"))
    path.elem.append(
        PathElem(name="VLAN_MEMBER_LIST")
    ) if not vlan_name or not intf_name else path.elem.append(
        PathElem(name="VLAN_MEMBER_LIST", key={"name": vlan_name, "ifname": intf_name})
    )
    return path


def get_vlan_list_path(vlan_list_name=None):
    path = get_sonic_vlan_base_path()
    path.elem.append(PathElem(name="VLAN"))
    path.elem.append(
        PathElem(name="VLAN_LIST")
    ) if not vlan_list_name else path.elem.append(
        PathElem(name="VLAN_LIST", key={"name": vlan_list_name})
    )
    return path


def get_vlan_mem_tagging_path(vlan_name: str, intf_name: str):
    path = get_vlan_mem_path(vlan_name, intf_name)
    path.elem.append(PathElem(name="tagging_mode"))
    return path


def get_vlan_details_from_device(device_ip: str, vlan_name: str = None):
    """
    Retrieves VLAN details from a device.

    Args:
        device_ip (str): The IP address of the device.
        vlan_name (str, optional): The name of the VLAN. Defaults to None.

    Returns:
        The VLAN details retrieved from the device.

    Raises:
        None
    """
    return send_gnmi_get(
        device_ip=device_ip,
        path=[
            get_vlan_list_path(vlan_name),
            get_vlan_table_list_path(vlan_name),
            get_vlan_mem_path(),
        ],
    )


def del_vlan_from_device(device_ip: str, vlan_list_name: str = None):
    """
    Deletes a VLAN from a device.

    Parameters:
        device_ip (str): The IP address of the device.
        vlan_list_name (str, optional): The name of the VLAN list to delete. If not provided, 
        the function will delete the VLAN using the default VLAN base path.

    Returns:
        The result of the GNMI set operation.

    """
    return send_gnmi_set(
        get_gnmi_del_req(
            get_sonic_vlan_base_path()
            if not vlan_list_name
            else get_vlan_list_path(vlan_list_name)
        ),
        device_ip,
    )


def config_vlan_on_device(
    device_ip: str, vlan_name: str, vlan_id: int, mem_ifs: dict[str:VlanTagMode] = None
):
    payload = {"sonic-vlan:VLAN_LIST": [{"name": vlan_name, "vlanid": vlan_id}]}
    if mem_ifs:
        payload.get("sonic-vlan:VLAN_LIST")[0]["members"] = list(mem_ifs.keys())

    payload2 = {"sonic-vlan:VLAN_MEMBER_LIST": []}
    for m, tag in mem_ifs.items() if mem_ifs else []:
        payload2.get("sonic-vlan:VLAN_MEMBER_LIST").append(
            {"ifname": m, "name": vlan_name, "tagging_mode": str(tag)}
        )

    return send_gnmi_set(
        create_req_for_update(
            [
                create_gnmi_update(get_vlan_list_path(), payload),
                create_gnmi_update(get_vlan_mem_path(), payload2),
            ]
        ),
        device_ip,
    )


def add_vlan_mem_interface_on_device(
    device_ip: str, vlan_name: str, mem_ifs: dict[str:VlanTagMode]
):
    payload2 = {"sonic-vlan:VLAN_MEMBER_LIST": []}
    for m, tag in mem_ifs.items():
        payload2.get("sonic-vlan:VLAN_MEMBER_LIST").append(
            {"ifname": m, "name": vlan_name, "tagging_mode": str(tag)}
        )
    return send_gnmi_set(
        create_req_for_update(
            [
                create_gnmi_update(get_vlan_mem_path(), payload2),
            ]
        ),
        device_ip,
    )


def del_vlan_mem_interface_on_device(
    device_ip: str, vlan_name: str, if_name: str = None
):
    return send_gnmi_set(
        get_gnmi_del_req(get_vlan_mem_path(vlan_name, if_name)), device_ip
    )


def config_vlan_tagging_mode_on_device(
    device_ip: str, vlan_name: str, if_name: str, tagging_mode: VlanTagMode
):
    payload = {"sonic-vlan:tagging_mode": str(tagging_mode)}

    return send_gnmi_set(
        create_req_for_update(
            [
                create_gnmi_update(
                    get_vlan_mem_tagging_path(vlan_name, if_name), payload
                ),
            ]
        ),
        device_ip,
    )
