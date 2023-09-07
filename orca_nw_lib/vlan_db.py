from orca_nw_lib.device import get_device_from_db
from orca_nw_lib.graph_db_models import Device, Vlan
from orca_nw_lib.interfaces import getInterfaceOfDeviceFromDB


def del_vlan_from_db(device_ip, vlan_name: str = None):
    device: Device = get_device_from_db(device_ip)
    vlan = device.vlans.get_or_none(name=vlan_name) if device else None
    if vlan:
        vlan.delete()


def get_vlan_obj_from_db(device_ip, vlan_name: str = None):
    device: Device = get_device_from_db(device_ip)
    return (
        device.vlans.all()
        if not vlan_name
        else device.vlans.get_or_none(name=vlan_name)
    )


def get_vlan_mem_ifcs_from_db(device_ip, vlan_name: str):
    device: Device = get_device_from_db(device_ip)
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
        if v := get_vlan_obj_from_db(device.mgt_ip, vlan.name):
            # update existing vlan
            copy_vlan_obj_prop(v, vlan)
            v.save()
            device.vlans.connect(v)
        else:
            vlan.save()
            device.vlans.connect(vlan)

        saved_vlan = get_vlan_obj_from_db(device.mgt_ip, vlan.name)
        for mem in members:
            mem_rel = (
                saved_vlan.memberInterfaces.connect(intf)
                if saved_vlan
                and (intf := getInterfaceOfDeviceFromDB(device.mgt_ip, mem.get("ifname")))
                else None
            )
            mem_rel.tagging_mode=mem.get("tagging_mode")
            mem_rel.save()
    ## Handle the case when some or all vlans has been deleted from device but remained in DB
    ## Remove all vlans which are in DB but not on device
    for vlan_in_db in get_vlan_obj_from_db(device.mgt_ip):
        if vlan_in_db not in vlans_obj_vs_mem:
            del_vlan_from_db(device.mgt_ip, vlan_in_db.name)