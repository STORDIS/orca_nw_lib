from typing import List
from .device import getDeviceFromDB
from .graph_db_models import MCLAG_GW_MAC, Device, MCLAG
from .interfaces import getInterfaceOfDeviceFromDB
from .port_chnl_db import get_port_chnl_of_device_from_db
from .gnmi_pb2 import Path, PathElem
from .gnmi_util import (
    create_req_for_update,
    get_gnmi_del_req,
    create_gnmi_update,
    send_gnmi_get,
    send_gnmi_set,
)


def getMclagOfDeviceFromDB(device_ip: str, domain_id: int = None):
    device = getDeviceFromDB(device_ip)
    if domain_id:
        return device.mclags.get_or_none(domain_id=domain_id) if device else None
    else:
        return device.mclags.all() if device else None


def getMclagGwMacOfDeviceFromDB(device_ip: str, mac: str = None):
    device = getDeviceFromDB(device_ip)
    if mac:
        return device.mclag_gw_macs.get_or_none(gateway_mac=mac) if device else None
    else:
        return device.mclag_gw_macs.all() if device else None


def delMclagGwMacOfDeviceFromDB(device_ip: str, mac: str = None):
    device = getDeviceFromDB(device_ip)
    gw_mac = device.mclag_gw_macs.get_or_none(gateway_mac=mac) if device else None
    if gw_mac:
        gw_mac.delete()


def delMCLAGOfDeviceFromDB(device_ip: str, domain_id: int):
    device = getDeviceFromDB(device_ip)
    mclag = device.mclags.get_or_none(domain_id=domain_id) if device else None
    if mclag:
        mclag.delete()


def delMCLAGGatewayMacOfDeviceInDB(device_ip: str):
    device = getDeviceFromDB(device_ip)
    mclag = device.mclags.get_or_none() if device else None
    if mclag:
        mclag.gateway_macs = []
        mclag.save()


def getMCLAGsFromDB(device_ip: str, domain_id=None):
    op_dict = []
    if domain_id:
        mclag = getMclagOfDeviceFromDB(device_ip, domain_id)
        if mclag:
            op_dict.append(mclag.__properties__)
    else:
        mclags = getMclagOfDeviceFromDB(device_ip)
        for mclag in mclags or []:
            op_dict.append(mclag.__properties__)
    return op_dict


def createMclagGraphObjects(device_ip: str) -> dict:
    mclags_obj_list = {}
    mclag_config = get_mclag_config_from_device(device_ip)
    mclag = mclag_config.get("openconfig-mclag:mclag", {})
    mclag_domains_dict_list = mclag.get("mclag-domains", {}).get("mclag-domain")
    mclag_intfc_list = mclag.get("interfaces", {}).get("interface")

    for mclag_domain in mclag_domains_dict_list or []:
        mclag_obj = MCLAG(
            domain_id=mclag_domain.get("config").get("domain-id"),
            keepalive_interval=mclag_domain.get("config").get("keepalive-interval"),
            mclag_sys_mac=mclag_domain.get("config").get("mclag-system-mac"),
            peer_addr=mclag_domain.get("config").get("peer-address"),
            peer_link=mclag_domain.get("config").get("peer-link"),
            session_timeout=mclag_domain.get("config").get("session-timeout"),
            source_address=mclag_domain.get("config").get("source-address"),
            delay_restore=mclag_domain.get("config").get("delay-restore"),
            oper_status=mclag_domain.get("state").get("oper-status"),
            role=mclag_domain.get("state").get("role"),
            system_mac=mclag_domain.get("state").get("system-mac"),
        )
        intfc_list = []
        for mclag_intfc in mclag_intfc_list or []:
            if mclag_obj.domain_id == mclag_intfc.get("config").get("mclag-domain-id"):
                intfc_list.append(mclag_intfc.get("name"))

        mclags_obj_list[mclag_obj] = intfc_list

    return mclags_obj_list


def createMclagGwMacObj(device_ip: str)-> List[MCLAG_GW_MAC]:
    mclag_gw_objs = []
    resp=get_mclag_gateway_mac_from_device(device_ip)
    
    macs=oc_macs.get("mclag-gateway-mac") if (oc_macs:=resp.get("openconfig-mclag:mclag-gateway-macs")) else []
    
    for mac_data in macs:
        gw_mac=mac_data.get("gateway-mac")
        mclag_gw_objs.append(MCLAG_GW_MAC(gateway_mac=gw_mac))
        
    return mclag_gw_objs
        


def get_mclag_path():
    return Path(
        target="openconfig",
        elem=[
            PathElem(name="openconfig-mclag:mclag"),
        ],
    )


def get_mclag_if_path():
    path = get_mclag_path()
    path.elem.append(PathElem(name="interfaces"))
    path.elem.append(PathElem(name="interface"))
    return path


def get_mclag_gateway_mac_path():
    path = get_mclag_path()
    path.elem.append(PathElem(name="mclag-gateway-macs"))
    return path


def get_mclag_domain_path():
    path = get_mclag_path()
    path.elem.append(PathElem(name="mclag-domains"))
    path.elem.append(PathElem(name="mclag-domain"))
    return path


def config_mclag_domain_on_device(
    device_ip: str,
    domain_id: int,
    source_addr: str,
    peer_addr: str,
    peer_link: str,
    mclag_sys_mac: str,
    keepalive_int: int = None,
    session_timeout: int = None,
    delay_restore: int = None,
):
    mclag_config_json = {
        "openconfig-mclag:mclag-domain": [
            {
                "domain-id": 0,
                "config": {
                    "domain-id": 0,
                    "source-address": "string",
                    "peer-address": "string",
                    "peer-link": "string",
                    "mclag-system-mac": "string",
                },
            }
        ]
    }

    for mc_lag in mclag_config_json.get("openconfig-mclag:mclag-domain"):
        mc_lag.update({"domain-id": domain_id})
        mc_lag.get("config").update({"domain-id": domain_id})
        mc_lag.get("config").update({"source-address": source_addr})
        mc_lag.get("config").update({"peer-address": peer_addr})
        mc_lag.get("config").update({"peer-link": peer_link})
        mc_lag.get("config").update({"mclag-system-mac": mclag_sys_mac})
        if keepalive_int:
            mc_lag.get("config").update({"keepalive-interval": keepalive_int})
        if session_timeout:
            mc_lag.get("config").update({"session-timeout": session_timeout})
        if delay_restore:
            mc_lag.get("config").update({"delay-restore": delay_restore})

    return send_gnmi_set(
        create_req_for_update(
            [create_gnmi_update(get_mclag_domain_path(), mclag_config_json)]
        ),
        device_ip,
    )


def config_mclag_mem_portchnl_on_device(
    device_ip: str, mclag_domain_id: int, port_chnl_name: str
):
    payload = {
        "openconfig-mclag:interface": [
            {
                "name": port_chnl_name,
                "config": {"name": port_chnl_name, "mclag-domain-id": mclag_domain_id},
            }
        ]
    }
    return send_gnmi_set(
        create_req_for_update([create_gnmi_update(get_mclag_if_path(), payload)]),
        device_ip,
    )


def get_mclag_mem_portchnl_on_device(device_ip: str):
    return send_gnmi_get(device_ip=device_ip, path=[get_mclag_if_path()])


def del_mclag_mem_portchnl_on_device(device_ip: str):
    return send_gnmi_set(get_gnmi_del_req(get_mclag_if_path()), device_ip)


def config_mclag_gateway_mac_on_device(device_ip: str, mclag_gateway_mac: str):
    mclag_gateway_mac_json = {
        "openconfig-mclag:mclag-gateway-macs": {
            "mclag-gateway-mac": [
                {
                    "gateway-mac": mclag_gateway_mac,
                    "config": {"gateway-mac": mclag_gateway_mac},
                }
            ]
        }
    }

    return send_gnmi_set(
        create_req_for_update(
            [create_gnmi_update(get_mclag_gateway_mac_path(), mclag_gateway_mac_json)]
        ),
        device_ip,
    )


def get_mclag_gateway_mac_from_device(device_ip: str):
    return send_gnmi_get(device_ip=device_ip, path=[get_mclag_gateway_mac_path()])


def del_mclag_gateway_mac_from_device(device_ip: str):
    return send_gnmi_set(get_gnmi_del_req(get_mclag_gateway_mac_path()), device_ip)


def get_mclag_domain_from_device(device_ip: str):
    return send_gnmi_get(device_ip=device_ip, path=[get_mclag_domain_path()])


def get_mclag_config_from_device(device_ip: str):
    return send_gnmi_get(device_ip=device_ip, path=[get_mclag_path()])


def del_mclag_from_device(device_ip: str):
    return send_gnmi_set(get_gnmi_del_req(get_mclag_path()), device_ip)


def create_mclag_peerlink_relations_in_db():
    for local_dev in getDeviceFromDB() or []:
        # there is only 1 mclag per device possible so always fetch index 0
        mclag_local = (
            mcl[0] if (mcl := getMclagOfDeviceFromDB(local_dev.mgt_ip)) else None
        )
        if mclag_local:
            peer_link_local = mclag_local.peer_link
            port_chnl_local = get_port_chnl_of_device_from_db(
                local_dev.mgt_ip, peer_link_local
            )
            if port_chnl_local:
                mclag_local.peer_link_node.connect(port_chnl_local)

            peer_addr = mclag_local.peer_addr
            mclag_remote = (
                mcl_r[0] if (mcl_r := getMclagOfDeviceFromDB(peer_addr)) else None
            )
            peer_link_remote = mclag_remote.peer_link if mclag_remote else None
            port_chnl_remote = get_port_chnl_of_device_from_db(peer_addr, peer_link_remote)
            if port_chnl_remote:
                mclag_remote.peer_link_node.connect(port_chnl_remote)

            port_chnl_local.peer_link.connect(
                port_chnl_remote
            ) if port_chnl_local and port_chnl_remote else None


def copy_mclag_obj_props(target_obj: MCLAG, src_obj: MCLAG):
    target_obj.domain_id = src_obj.domain_id
    target_obj.keepalive_interval = src_obj.keepalive_interval
    target_obj.mclag_sys_mac = src_obj.mclag_sys_mac
    target_obj.peer_addr = src_obj.peer_addr
    target_obj.peer_link = src_obj.peer_link
    target_obj.session_timeout = src_obj.session_timeout
    target_obj.source_address = src_obj.source_address
    target_obj.oper_status = src_obj.oper_status
    target_obj.role = src_obj.role
    target_obj.system_mac = src_obj.system_mac
    target_obj.delay_restore = src_obj.delay_restore


def insert_device_mclag_in_db(device: Device, mclag_to_intfc_list):
    for mclag, intfcs in mclag_to_intfc_list.items():
        if mclag_in_db := getMclagOfDeviceFromDB(device.mgt_ip, mclag.domain_id):
            copy_mclag_obj_props(mclag_in_db, mclag)
            mclag_in_db.save()
            device.mclags.connect(mclag_in_db)

        else:
            mclag.save()
            device.mclags.connect(mclag)

        saved_mclag = getMclagOfDeviceFromDB(device.mgt_ip, mclag.domain_id)

        for intf_name in intfcs:
            intf_obj = getInterfaceOfDeviceFromDB(device.mgt_ip, intf_name)
            if intf_obj:
                saved_mclag.intfc_members.connect(intf_obj)
            port_chnl_obj = get_port_chnl_of_device_from_db(device.mgt_ip, intf_name)
            if port_chnl_obj:
                saved_mclag.portChnl_member.connect(port_chnl_obj)

    ## Handle the case when some or all mclags has been deleted from device but remained in DB
    ## Remove all mclags which are in DB but not on device

    for mcl_in_db in getMclagOfDeviceFromDB(device.mgt_ip):
        if mcl_in_db not in mclag_to_intfc_list:
            delMCLAGOfDeviceFromDB(device.mgt_ip, mcl_in_db.domain_id)


def copy_mclag_gw_mac_props(target_obj:MCLAG_GW_MAC, src_obj:MCLAG_GW_MAC):
    target_obj.gateway_mac=src_obj.gateway_mac

def insert_device_mclag_gw_macs_in_db(device: Device, mclag_gw_macs:List[MCLAG_GW_MAC]):
    for mclag_gw_mac in mclag_gw_macs:
        if gw_mac_in_db := getMclagGwMacOfDeviceFromDB(device.mgt_ip, mclag_gw_mac.gateway_mac):
            copy_mclag_gw_mac_props(gw_mac_in_db, mclag_gw_mac)
            gw_mac_in_db.save()
            device.mclag_gw_macs.connect(gw_mac_in_db)
        else:
            mclag_gw_mac.save()
            device.mclag_gw_macs.connect(mclag_gw_mac)


    ## Handle the case when some or all mclags gw macs has been deleted from device but remained in DB
    ## Remove all mclags gw macs which are in DB but not on device

    for gw_mac_in_db in getMclagGwMacOfDeviceFromDB(device.mgt_ip):
        if gw_mac_in_db not in mclag_gw_macs:
            delMclagGwMacOfDeviceFromDB(device.mgt_ip, gw_mac_in_db.gateway_mac)
