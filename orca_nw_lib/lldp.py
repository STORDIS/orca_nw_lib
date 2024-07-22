from typing import Set
from orca_nw_lib.interface import get_interface
from orca_nw_lib.interface_db import get_all_interfaces_name_of_device_from_db, set_interface_config_in_db
from .utils import get_logging
from .lldp_gnmi import get_lldp_nbr_from_device


_logger = get_logging().getLogger(__name__)


def _create_lldp_info(device_ip, if_name: str = None):
    lldp_response = get_lldp_nbr_from_device(device_ip, if_name).get(
        "openconfig-lldp:interface"
    )
    for lldp in lldp_response or []:
        nbr_dict = {} ## Per local ethernet - in the format {nbr_ip:[Eth0,Eth1].........}
        local_if = lldp.get("name")
        # Check if neighbors node exists
        if lldp.get("neighbors") and (nbrs := lldp.get("neighbors").get("neighbor")):
            # iterate all neighbors
            for nbr in nbrs:
                if nbr.get("state").get("management-address"):
                    nbr_ip = nbr.get("state").get("management-address").split(",")[0]
                    nbr_port = nbr.get("state").get("port-id")
                    if (n_ip:=nbr_dict.get(nbr_ip)):
                        nbr_dict[n_ip].append(nbr_port) 
                    else: 
                        nbr_dict[nbr_ip]=[nbr_port]
            # Get the local interface from db and add lldp nbr info
            set_interface_config_in_db(device_ip, local_if, lldp_nbrs=nbr_dict)


def discover_lldp_info(device_ip):
    try:
        _logger.info(f"Discovering LLDP info of device : {device_ip}")
        _create_lldp_info(device_ip)
    except Exception as e:
        _logger.error(f"LLDP Discovery Failed on device {device_ip}, Reason: {e}")
        raise


def get_lldp_neighbors(device_ip: str, if_name:str):
    return i.get("lldp_nbrs") if (i:=get_interface(device_ip, intfc_name=if_name)) else None
    
def get_all_lldp_neighbor_device_ips(device_ip: str) -> Set[str]:
    nbr_device_ips=set()
    for if_name in get_all_interfaces_name_of_device_from_db(device_ip) or []:
        nbr_device_ips.update(nbr_info.keys()) if (nbr_info:=get_lldp_neighbors(device_ip, if_name)) else None
            
    return nbr_device_ips
