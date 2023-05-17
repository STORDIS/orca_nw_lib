from typing import List
from orca_backend.gnmi_pb2 import Path, PathElem
from orca_backend.gnmi_util import get_gnmi_del_req, get_gnmi_update_req, send_gnmi_get, send_gnmi_set
from orca_backend.graph_db_models import MCLAG

    
def createMclagGraphObjects(device_ip: str)->dict:
    mclags_obj_list={}
    mclag_config=get_mclag_config(device_ip)
    mclag=mclag_config.get("openconfig-mclag:mclag")
    mclag_domains_dict_list=mclag.get("mclag-domains",{}).get("mclag-domain")
    mclag_intfc_list=mclag.get("interfaces",{}).get("interface")
    mclag_gateway_macs=mclag.get('mclag-gateway-macs',{}).get('mclag-gateway-mac')
    
    for mclag_domain in mclag_domains_dict_list:
        mclag_obj=MCLAG(domain_id=mclag_domain.get("config").get("domain-id"),
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
        intfc_list=[]
        for mclag_intfc in mclag_intfc_list or []:
            if mclag_obj.domain_id == mclag_intfc.get('config').get('mclag-id'):
                intfc_list.append(mclag_intfc.get('name'))
                
        mclag_obj.gateway_macs=[(gw.get("gateway-mac")) for gw in mclag_gateway_macs]
                
        mclags_obj_list[mclag_obj]=intfc_list
    
    return mclags_obj_list

def config_mclag_domain(device_ip: str, domain_id: int,
                        source_addr: str, peer_addr: str, peer_link: str,
                        mclag_sys_mac: str, keepalive_int: int = 0,
                        session_timeout: int = 0, delay_restore: int = 0):

    path = Path(target='openconfig',
                origin='openconfig-mclag',
                elem=[PathElem(name="mclag"),
                      PathElem(name="mclag-domains"),
                      PathElem(name="mclag-domain"),
                      ])

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
                    "keepalive-interval": 0,
                    "session-timeout": 0,
                    "delay-restore": 0
                }
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
        mc_lag.get("config").update({"keepalive-interval": keepalive_int})
        mc_lag.get("config").update({"session-timeout": session_timeout})
        mc_lag.get("config").update({"delay-restore": delay_restore})

    return send_gnmi_set(get_gnmi_update_req(path, mclag_config_json), device_ip)


def get_mclag_config(device_ip: str):
    path = Path(target='openconfig',
                origin='openconfig-mclag',
                elem=[PathElem(name="mclag"),
                      ])
    return send_gnmi_get(device_ip=device_ip,path=[path])


def del_mclag(device_ip: str):
    path = Path(target='openconfig',
                origin='openconfig-mclag',
                elem=[PathElem(name="mclag"),
                      ])
    return send_gnmi_set(get_gnmi_del_req(path), device_ip)