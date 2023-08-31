from ast import List
from .device import getDeviceFromDB
from .common import VlanTagMode
from .gnmi_pb2 import Path, PathElem
from .gnmi_util import (
    create_gnmi_update,
    create_req_for_update,
    get_gnmi_del_req,
    send_gnmi_get,
    send_gnmi_set,
)
from .graph_db_models import Device
from .interfaces import getInterfaceOfDeviceFromDB
from .utils import get_logging
from .graph_db_models import Vlan

_logger = get_logging().getLogger(__name__)


def getVlanDBObj(device_ip: str):
    vlan_details = get_vlan_details_from_device(device_ip)
    vlans_obj_vs_mem = {}
    for vlan in vlan_details.get("sonic-vlan:VLAN_LIST") or []:
        vlans_obj_vs_mem[
            Vlan(
                vlanid=vlan.get("vlanid"),
                name=vlan.get("name"),
            )
        ] = vlan.get("members")

    for vlan in vlan_details.get("sonic-vlan:VLAN_TABLE_LIST") or []:
        for key in vlans_obj_vs_mem:
            if key.name == vlan.get("name"):
                key.mtu = vlan.get("mtu")
                key.admin_status = vlan.get("admin_status")
                key.oper_status = vlan.get("oper_status")

    for vlan in vlan_details.get("sonic-vlan:VLAN_MEMBER_LIST") or []:
        # TODO Store stagging information per member interface basis
        break

    return vlans_obj_vs_mem


def getJson(device_ip: str, v: Vlan):
    temp = v.__properties__
    temp["members"] = [
        mem.name for mem in get_vlan_mem_ifcs_from_db(device_ip, temp.get("name")) or []
    ]
    return temp


def getJsonOfVLANDetailsFromDB(device_ip, vlan_name: str = None):
    vlans = get_vlan_details_from_db(device_ip, vlan_name)
    op_dict = []
    try:
        for v in vlans or []:
            op_dict.append(getJson(device_ip, v))
    except TypeError:
        ## Its a single vlan object no need to iterate.
        op_dict.append(getJson(device_ip, vlans))
    return op_dict


def get_vlan_details_from_db(device_ip, vlan_name: str):
    device: Device = getDeviceFromDB(device_ip)
    return (
        device.vlans.all()
        if not vlan_name
        else device.vlans.get_or_none(name=vlan_name)
    )


def get_vlan_mem_ifcs_from_db(device_ip, vlan_name: str):
    device: Device = getDeviceFromDB(device_ip)
    # _logger.info(device)
    # _logger.info(vlan_name)
    # _logger.info(vv.name) if (vv:= device.vlans.get_or_none(name=vlan_name)) else None
    return (
        v.memberInterfaces.all()
        if device and device.vlans and (v := device.vlans.get_or_none(name=vlan_name))
        else None
    )


def copy_vlan_obj_prop(target_vlan_obj: Vlan, source_vlan_obj: Vlan):
    target_vlan_obj.vlanid = source_vlan_obj.vlanid
    target_vlan_obj.name = source_vlan_obj.name
    target_vlan_obj.mtu = source_vlan_obj.mtu
    target_vlan_obj.admin_status = source_vlan_obj.admin_status
    target_vlan_obj.oper_status = source_vlan_obj.oper_status


def insertVlanInDB(device: Device, vlans_obj_vs_mem):
    for vlan, members in vlans_obj_vs_mem.items():
        if v := get_vlan_details_from_db(device.mgt_ip, vlan.name):
            # update existing vlan
            copy_vlan_obj_prop(v, vlan)
            v.save()
            device.vlans.connect(v)
        else:
            vlan.save()
            device.vlans.connect(vlan)

        saved_vlan= get_vlan_details_from_db(device.mgt_ip, vlan.name)
        for mem in members:
            saved_vlan.memberInterfaces.connect(intf) if saved_vlan and (intf := getInterfaceOfDeviceFromDB(device.mgt_ip, mem)) else None


def get_sonic_vlan_base_path():
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


def get_vlan_list_path(vlan_list_name=None):
    path = get_sonic_vlan_base_path()
    path.elem.append(PathElem(name="VLAN"))
    path.elem.append(
        PathElem(name="VLAN_LIST")
    ) if not vlan_list_name else path.elem.append(
        PathElem(name="VLAN_LIST", key={"name": vlan_list_name})
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


def get_vlan_mem_tagging_path(vlan_name: str, intf_name: str):
    path = get_vlan_mem_path(vlan_name, intf_name)
    path.elem.append(PathElem(name="tagging_mode"))
    return path


def get_vlan_details_from_device(device_ip: str, vlan_name: str = None):
    return send_gnmi_get(
        device_ip=device_ip,
        path=[
            get_vlan_list_path(vlan_name),
            get_vlan_table_list_path(vlan_name),
            get_vlan_mem_path(),
        ],
    )


def del_vlan_from_device(device_ip: str, vlan_list_name: str = None):
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
