from orca_nw_lib.device import getDeviceFromDB
from orca_nw_lib.gnmi_pb2 import Path, PathElem
from orca_nw_lib.gnmi_util import (
    create_gnmi_update,
    create_req_for_update,
    get_gnmi_del_req,
    send_gnmi_get,
    send_gnmi_set,
)
from orca_nw_lib.graph_db_models import Device, PortChannel

from orca_nw_lib.interfaces import getInterfaceOfDeviceFromDB


def createPortChnlGraphObject(device_ip: str):
    port_chnl_json = get_port_chnls_all(device_ip)
    port_chnl_obj_list = {}
    if port_chnl_json:
        lag_table_json_list = (
            port_chnl_json.get("sonic-portchannel:sonic-portchannel")
            .get("LAG_TABLE", {})
            .get("LAG_TABLE_LIST")
        )
        lag_mem_table_json_list = (
            port_chnl_json.get("sonic-portchannel:sonic-portchannel")
            .get("LAG_MEMBER_TABLE", {})
            .get("LAG_MEMBER_TABLE_LIST")
        )
        for lag in lag_table_json_list or []:
            ifname_list = []
            for mem in lag_mem_table_json_list or []:
                if lag.get("lagname") == mem.get("name"):
                    ifname_list.append(mem.get("ifname"))
            port_chnl_obj_list[
                PortChannel(
                    active=lag.get("active"),
                    lag_name=lag.get("lagname"),
                    admin_sts=lag.get("admin_status"),
                    mtu=lag.get("mtu"),
                    name=lag.get("name"),
                    fallback_operational=lag.get("fallback_operational"),
                    oper_sts=lag.get("oper_status"),
                    speed=lag.get("speed"),
                    oper_sts_reason=lag.get("reason"),
                )
            ] = ifname_list
    return port_chnl_obj_list


def getAllPortChnlOfDeviceFromDB(device_ip: str):
    device = getDeviceFromDB(device_ip)
    return getDeviceFromDB(device_ip).port_chnl.all() if device else None


def getPortChnlOfDeviceFromDB(device_ip: str, port_chnl_name: str) -> PortChannel:
    device = getDeviceFromDB(device_ip)
    return (
        getDeviceFromDB(device_ip).port_chnl.get_or_none(lag_name=port_chnl_name)
        if device
        else None
    )


def getPortChnlDetailsFromDB(device_ip: str, port_chnl_name=None):
    op_dict = []
    if port_chnl_name:
        port_chnl = getPortChnlOfDeviceFromDB(device_ip, port_chnl_name)
        op_dict.append(port_chnl.__properties__)
    else:
        port_chnl = getAllPortChnlOfDeviceFromDB(device_ip)
        for chnl in port_chnl or []:
            op_dict.append(chnl.__properties__)
    return op_dict


def get_port_chnl_base_path():
    return Path(
        target="openconfig",
        origin="sonic-portchannel",
        elem=[
            PathElem(name="sonic-portchannel"),
            PathElem(name="PORTCHANNEL"),
        ],
    )


def get_port_chnl_list_path():
    path = get_port_chnl_base_path()
    path.elem.append(PathElem(name="PORTCHANNEL_LIST"))
    return path


def get_port_chnl_path(chnl_name: str):
    path = get_port_chnl_base_path()
    path.elem.append(PathElem(name="PORTCHANNEL_LIST", key={"name": chnl_name}))
    return path


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


def get_port_chnl_mem_base_path():
    return Path(
        target="openconfig",
        origin="sonic-portchannel",
        elem=[PathElem(name="sonic-portchannel"), PathElem(name="PORTCHANNEL_MEMBER")],
    )


def get_port_chnl_mem_list_path():
    path = get_port_chnl_mem_base_path()
    path.elem.append(PathElem(name="PORTCHANNEL_MEMBER_LIST"))
    return path


def get_port_chnl_mem_path(chnl_name: str, ifname: str):
    path = get_port_chnl_mem_base_path()
    path.elem.append(
        PathElem(
            name="PORTCHANNEL_MEMBER_LIST", key={"name": chnl_name, "ifname": ifname}
        )
    )
    return path


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


def get_all_port_chnl_members(device_ip: str):
    return send_gnmi_get(device_ip, [get_port_chnl_mem_list_path()])


def remove_port_chnl_member(device_ip: str, chnl_name: str, ifname: str):
    return send_gnmi_set(
        get_gnmi_del_req(get_port_chnl_mem_path(chnl_name, ifname)), device_ip
    )


def del_port_chnl_from_device(device_ip: str, chnl_name: str):
    return send_gnmi_set(get_gnmi_del_req(get_port_chnl_path(chnl_name)), device_ip)


def get_port_chnls_all(device_ip: str):
    path_intf_status_path = Path(
        target="openconfig",
        origin="sonic-portchannel",
        elem=[
            PathElem(name="sonic-portchannel"),
        ],
    )
    return send_gnmi_get(device_ip, [path_intf_status_path])


def get_port_chnl_from_device(device_ip: str, chnl_name: str):
    return send_gnmi_get(device_ip, [get_port_chnl_path(chnl_name)])


def del_all_port_chnl(device_ip: str):
    return send_gnmi_set(get_gnmi_del_req(get_port_chnl_list_path()), device_ip)


def insert_device_port_chnl_in_db(device: Device, portchnl_to_mem_list):
    for chnl, mem_list in portchnl_to_mem_list.items():
        chnl.save()
        device.port_chnl.connect(chnl)
        for intf_name in mem_list:
            intf_obj = getInterfaceOfDeviceFromDB(device.mgt_ip, intf_name)
            if intf_obj:
                chnl.members.connect(intf_obj)
