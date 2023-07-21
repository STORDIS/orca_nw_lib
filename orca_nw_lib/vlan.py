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


def insertVlanInDB(device: Device, vlans_obj_vs_mem):
    for vlan, members in vlans_obj_vs_mem.items():
        vlan.save()
        device.vlans.connect(vlan)
        for mem in members:
            intf = getInterfaceOfDeviceFromDB(device.mgt_ip, mem)
            vlan.memberInterfaces.connect(intf) if intf else None


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
    ) if vlan_name else path.elem.append(
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
    ) if not vlan_name and not intf_name else path.elem.append(
        PathElem(name="VLAN_MEMBER_LIST", key={"name": vlan_name, "ifname": intf_name})
    )
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
    payload = {
        "sonic-vlan:VLAN_LIST": [
            {"members": list(mem_ifs.keys()), "name": vlan_name, "vlanid": vlan_id}
        ]
    }
    payload2 = {"sonic-vlan:VLAN_MEMBER_LIST": []}
    for m, tag in mem_ifs.items():
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
