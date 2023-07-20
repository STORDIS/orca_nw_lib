from .gnmi_pb2 import Path, PathElem
from .gnmi_util import send_gnmi_get
from .graph_db_models import Device
from .interfaces import getInterfaceOfDeviceFromDB
from .utils import get_logging
from .graph_db_models import Vlan

_logger = get_logging().getLogger(__name__)


def getVlanDBObj(device_ip: str):
    vlan_details = get_vlan_details_device(device_ip)
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
    return vlans_obj_vs_mem


def insertVlanInDB(device: Device, vlans_obj_vs_mem):
    for vlan, members in vlans_obj_vs_mem.items():
        vlan.save()
        device.vlans.connect(vlan)
        for mem in members:
            intf = getInterfaceOfDeviceFromDB(device.mgt_ip, mem)
            vlan.memberInterfaces.connect(intf) if intf else None


def get_vlan_base_path():
    return Path(
        target="openconfig",
        origin="sonic-vlan",
        elem=[
            PathElem(
                name="sonic-vlan",
            )
        ],
    )


def get_vlan_table_list_path():
    path = get_vlan_base_path()
    path.elem.append(PathElem(name="VLAN_TABLE"))
    path.elem.append(PathElem(name="VLAN_TABLE_LIST"))
    return path


def get_vlan_list_path():
    path = get_vlan_base_path()
    path.elem.append(PathElem(name="VLAN"))
    path.elem.append(PathElem(name="VLAN_LIST"))
    return path


def get_vlan_details_device(device_ip: str):
    return send_gnmi_get(
        device_ip=device_ip, path=[get_vlan_list_path(), get_vlan_table_list_path()]
    )
