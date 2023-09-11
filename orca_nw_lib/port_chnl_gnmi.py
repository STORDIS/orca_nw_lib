from orca_nw_lib.gnmi_pb2 import PathElem
from orca_nw_lib.gnmi_util import create_gnmi_update, create_req_for_update, send_gnmi_get, send_gnmi_set
from orca_nw_lib.portgroup_gnmi import get_port_chnl_mem_base_path
from .gnmi_pb2 import Path, PathElem
from .gnmi_util import (
    create_gnmi_update,
    create_req_for_update,
    get_gnmi_del_req,
    send_gnmi_get,
    send_gnmi_set,
)


def get_port_chnl_root_path() -> Path:
    return Path(
        target="openconfig",
        origin="sonic-portchannel",
        elem=[
            PathElem(name="sonic-portchannel"),
        ],
    )


def get_port_chnl_base_path() -> Path:
    path = get_port_chnl_root_path()
    path.elem.append(PathElem(name="PORTCHANNEL"))
    return path


def get_port_chnl_list_path() -> Path:
    path = get_port_chnl_base_path()
    path.elem.append(PathElem(name="PORTCHANNEL_LIST"))
    return path


def get_port_chnl_path(chnl_name: str=None):
    path = get_port_chnl_base_path()
    if chnl_name:
        path.elem.append(PathElem(name="PORTCHANNEL_LIST", key={"name": chnl_name}))
    else:
        path.elem.append(PathElem(name="PORTCHANNEL_LIST"))
    return path


def get_lag_member_table_list_path() -> Path:
    path = get_port_chnl_root_path()
    path.elem.append(PathElem(name="LAG_MEMBER_TABLE"))
    path.elem.append(PathElem(name="LAG_MEMBER_TABLE_LIST"))
    return path


def get_lag_table_list_path(chnl_name: str = None) -> Path:
    path = get_port_chnl_root_path()
    path.elem.append(PathElem(name="LAG_TABLE"))

    if chnl_name:
        path.elem.append(PathElem(name="LAG_TABLE_LIST", key={"lagname": chnl_name}))
    else:
        path.elem.append(PathElem(name="LAG_TABLE_LIST"))

    return path


def del_all_port_chnl(device_ip: str):
    return send_gnmi_set(get_gnmi_del_req(get_port_chnl_list_path()), device_ip)


def get_port_chnl_from_device(device_ip: str, chnl_name: str):
    return send_gnmi_get(device_ip, [get_port_chnl_path(chnl_name)])


def get_port_chnls_info_from_device(device_ip: str, chnl_name: str = None):
    return send_gnmi_get(
        device_ip,
        [get_lag_member_table_list_path(), get_lag_table_list_path(chnl_name)],
    )


def get_lag_member_table_list(device_ip: str):
    return send_gnmi_get(device_ip, [get_lag_member_table_list_path()])


def get_lag_table_list(device_ip: str, chnl_name: str = None):
    return send_gnmi_get(device_ip, [get_lag_table_list_path(chnl_name)])


def get_port_chnl_mem_list_path():
    path = get_port_chnl_mem_base_path()
    path.elem.append(PathElem(name="PORTCHANNEL_MEMBER_LIST"))
    return path


def get_all_port_chnl_members(device_ip: str):
    return send_gnmi_get(device_ip, [get_port_chnl_mem_list_path()])


def get_port_chnl_mem_path(chnl_name: str, ifname: str):
    path = get_port_chnl_mem_base_path()
    path.elem.append(
        PathElem(
            name="PORTCHANNEL_MEMBER_LIST", key={"name": chnl_name, "ifname": ifname}
        )
    )
    return path


def remove_port_chnl_member(device_ip: str, chnl_name: str, ifname: str):
    return send_gnmi_set(
        get_gnmi_del_req(get_port_chnl_mem_path(chnl_name, ifname)), device_ip
    )


def del_port_chnl_from_device(device_ip: str, chnl_name: str=None):
    return send_gnmi_set(get_gnmi_del_req(get_port_chnl_path(chnl_name)), device_ip)


def add_port_chnl_member(device_ip: str, chnl_name: str, ifnames: list[str]):
    port_chnl_add = {"sonic-portchannel:PORTCHANNEL_MEMBER_LIST": []}
    for intf in ifnames:
        port_chnl_add.get("sonic-portchannel:PORTCHANNEL_MEMBER_LIST").append(
            {"name": chnl_name, "ifname": intf}
        )
    return send_gnmi_set(
        create_req_for_update(
            [create_gnmi_update(get_port_chnl_mem_list_path(), port_chnl_add)]
        ),
        device_ip,
    )


def add_port_chnl_on_device(
    device_ip: str, chnl_name: str, admin_status: str = None, mtu: int = None
):
    port_chnl_add = {"sonic-portchannel:PORTCHANNEL_LIST": []}
    port_chnl_item = {"name": chnl_name}
    if admin_status is not None and admin_status in ["up", "down"]:
        port_chnl_item["admin_status"] = admin_status
    if mtu is not None:
        port_chnl_item["mtu"] = mtu

    port_chnl_add.get("sonic-portchannel:PORTCHANNEL_LIST").append(port_chnl_item)
    return send_gnmi_set(
        create_req_for_update(
            [create_gnmi_update(get_port_chnl_list_path(), port_chnl_add)]
        ),
        device_ip,
    )
