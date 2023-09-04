from typing import List
from .device import getDeviceFromDB
from .graph_db_models import Device, Interface, PortChannel
from .interfaces import getInterfaceOfDeviceFromDB


def getPortChnlOfDeviceFromDB(device_ip: str, port_chnl_name: str) -> PortChannel:
    device = getDeviceFromDB(device_ip)
    return (
        getDeviceFromDB(device_ip).port_chnl.get_or_none(lag_name=port_chnl_name)
        if device
        else None
    )


def delPortChnlOfDeviceFromDB(device_ip: str, port_chnl_name: str):
    device = getDeviceFromDB(device_ip)
    chnl = (
        getDeviceFromDB(device_ip).port_chnl.get_or_none(lag_name=port_chnl_name)
        if device
        else None
    )
    if chnl:
        chnl.delete()


def getAllPortChnlOfDeviceFromDB(device_ip: str) -> List[PortChannel]:
    device = getDeviceFromDB(device_ip)
    return getDeviceFromDB(device_ip).port_chnl.all() if device else None


def get_port_chnl_members_from_db(
    device_ip: str, port_chnl_name: str, if_name: str = None
) -> Interface | List[Interface]:
    chnl = getPortChnlOfDeviceFromDB(device_ip, port_chnl_name)
    return (
        chnl.members.get_or_none(if_name)
        if if_name and chnl
        else chnl.members.all()
        if chnl
        else None
    )


def copy_port_chnl_prop(target_obj: PortChannel, src_obj: PortChannel):
    target_obj.lag_name = src_obj.lag_name
    target_obj.active = src_obj.active
    target_obj.admin_sts = src_obj.admin_sts
    target_obj.mtu = src_obj.mtu
    target_obj.name = src_obj.name  # name of protocol e.g. lacp
    target_obj.fallback_operational = src_obj.fallback_operational
    target_obj.oper_sts = src_obj.oper_sts
    target_obj.speed = src_obj.speed
    target_obj.oper_sts_reason = src_obj.oper_sts_reason


def insert_device_port_chnl_in_db(device: Device, portchnl_to_mem_list):
    for chnl, mem_list in portchnl_to_mem_list.items():
        if p_chnl := getPortChnlOfDeviceFromDB(device.mgt_ip, chnl.lag_name):
            copy_port_chnl_prop(p_chnl, chnl)
            p_chnl.save()
            device.port_chnl.connect(p_chnl)
        else:
            chnl.save()
            device.port_chnl.connect(chnl)
        saved_p_chnl = getPortChnlOfDeviceFromDB(device.mgt_ip, chnl.lag_name)
        for intf_name in mem_list:
            saved_p_chnl.members.connect(intf_obj) if saved_p_chnl and (
                intf_obj := getInterfaceOfDeviceFromDB(device.mgt_ip, intf_name)
            ) else None

    ## Handle the case when some or all port_chnl has been deleted from device but remained in DB
    ## Remove all port_chnl which are in DB but not on device
    for chnl_in_db in getAllPortChnlOfDeviceFromDB(device.mgt_ip):
        if chnl_in_db not in portchnl_to_mem_list:
            delPortChnlOfDeviceFromDB(device.mgt_ip, chnl_in_db.lag_name)
        ## Also disconnect interfaces if not a member of channel
        chnl_members_on_device = portchnl_to_mem_list.get(chnl_in_db)
        for mem in chnl_in_db.members.all() or []:
            if mem.name not in chnl_members_on_device:
                chnl_in_db.members.disconnect(mem)
