from typing import List, Set
from orca_nw_lib.interface import get_interface
from orca_nw_lib.interface_db import get_all_interfaces_name_of_device_from_db, set_interface_config_in_db
from orca_nw_lib.lldp_gnmi import get_lldp_interfaces_from_device
from .device import create_device_graph_object
from .utils import get_logging
from .lldp_gnmi import get_lldp_nbr_from_device


_logger = get_logging().getLogger(__name__)


def _create_lldp_info(device_ip, if_name: str = None):
    lldp_response = get_lldp_nbr_from_device(device_ip, if_name).get(
        "openconfig-lldp:interface"
    )
    nbr_dict = {} ## {nbr_ip:[Eth0,Eth1].........}
    for lldp in lldp_response or []:
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
            

def read_lldp_topo(ip: str, topology, lldp_report: list):
    """
    Generate the function comment for the given function body in a markdown code block with the correct language syntax.

    Parameters:
        ip (str): The IP address of the device.
        topology: The current topology dictionary.
        lldp_report (list): The list to store the LLDP report.

    Returns:
        None
    """

    try:
        device = create_device_graph_object(ip)
        if device not in topology:
            nbrs = []
            try:
                nbrs = get_lldp_neighbors(ip)
            except Exception as e:
                log_str = (
                    f"Neighbors of Device {ip} couldn't be discovered reason : {e}."
                )
                _logger.info(log_str)
                lldp_report.append(log_str)

            temp_arr = []
            for nbr in nbrs:
                try:
                    nbr_device = create_device_graph_object(nbr.get("nbr_ip"))

                    # Following check prevents adding an empty device object in topology.
                    # with no mgt_ip any no other properties as well.
                    # This may happen if device is pingable but gnmi connection can not be established.
                    if nbr_device.mgt_intf:
                        temp_arr.append(
                            {
                                "nbr_device": create_device_graph_object(
                                    nbr.get("nbr_ip")
                                ),
                                "nbr_port": nbr.get("nbr_port"),
                                "local_port": nbr.get("local_port"),
                            }
                        )
                except Exception as e:
                    log_str = f"Device {nbr.get('nbr_ip')} couldn't be discovered reason : {e}."
                    _logger.info(log_str)
                    lldp_report.append(log_str)

            topology[device] = temp_arr

            for nbr in nbrs or []:
                read_lldp_topo(nbr.get("nbr_ip"), topology, lldp_report)
    except Exception as e:
        log_str = f"Device {ip} couldn't be discovered reason : {e}."
        _logger.info(log_str)
        lldp_report.append(log_str)
