from .gnmi_pb2 import Path, PathElem
from .gnmi_util import (
    create_req_for_update,
    get_gnmi_del_req,
    create_gnmi_update,
    send_gnmi_get,
    send_gnmi_set,
)
from .graph_db_models import MCLAG
from .graph_db_utils import getMclagOfDeviceFromDB, getMCLAGOfDeviceFromDB


def getMCLAGsFromGraph(device_ip: str, domain_id=None):
    op_dict = []
    if domain_id:
        mclag = getMCLAGOfDeviceFromDB(device_ip, domain_id)
        if mclag:
            op_dict.append(mclag.__properties__)
    else:
        mclags = getMclagOfDeviceFromDB(device_ip)
        for mclag in mclags or []:
            op_dict.append(mclag.__properties__)
    return op_dict


def createMclagGraphObjects(device_ip: str) -> dict:
    mclags_obj_list = {}
    mclag_config = get_mclag_config(device_ip)
    mclag = mclag_config.get("openconfig-mclag:mclag", {})
    mclag_domains_dict_list = mclag.get("mclag-domains", {}).get("mclag-domain")
    mclag_intfc_list = mclag.get("interfaces", {}).get("interface")
    mclag_gateway_macs = mclag.get("mclag-gateway-macs", {}).get("mclag-gateway-mac")

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

        mclag_obj.gateway_macs = [(gw.get("gateway-mac")) for gw in mclag_gateway_macs or []]

        mclags_obj_list[mclag_obj] = intfc_list

    return mclags_obj_list


def get_mclag_path():
    return Path(
        target="openconfig",
        origin="openconfig-mclag",
        elem=[
            PathElem(name="mclag"),
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


def config_mclag_domain(
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


def config_mclag_mem_portchnl(
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


def get_mclag_mem_portchnl(device_ip: str):
    return send_gnmi_get(device_ip=device_ip, path=[get_mclag_if_path()])


def del_mclag_mem_portchnl(device_ip: str):
    return send_gnmi_set(get_gnmi_del_req(get_mclag_if_path()), device_ip)


def config_mclag_gateway_mac(device_ip: str, mclag_gateway_mac: str):
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


def get_mclag_gateway_mac(device_ip: str):
    return send_gnmi_get(device_ip=device_ip, path=[get_mclag_gateway_mac_path()])


def del_mclag_gateway_mac(device_ip: str):
    return send_gnmi_set(get_gnmi_del_req(get_mclag_gateway_mac_path()), device_ip)


def get_mclag_domain(device_ip: str):
    return send_gnmi_get(device_ip=device_ip, path=[get_mclag_domain_path()])


def get_mclag_config(device_ip: str):
    return send_gnmi_get(device_ip=device_ip, path=[get_mclag_path()])


def del_mclag(device_ip: str):
    return send_gnmi_set(get_gnmi_del_req(get_mclag_path()), device_ip)
