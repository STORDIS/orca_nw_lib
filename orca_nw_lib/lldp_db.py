from .interface_db import (
    get_all_interfaces_of_device_from_db,
    get_interface_of_device_from_db,
)


def create_lldp_relations_in_db(device_ip):
    """
    Creates LLDP relations in the database based on the given topology.

    Args:
        topology (dict): A dictionary representing the topology of devices and their neighbors.

    Returns:
        None
    """
    # Iterate all interfaces of local device
    for local_if in get_all_interfaces_of_device_from_db(device_ip) or []:
        # Retrieve neighbor json of every interface and Iterate the Json
        if (nbr_info:=local_if.lldp_nbrs):
            for nbr_ip, nbr_ifs in nbr_info.items():
                for nbr_if in nbr_ifs or []:
                    nbr_if_db_obj = get_interface_of_device_from_db(nbr_ip, nbr_if)
                    if nbr_if_db_obj:
                        local_if.lldp_neighbour.connect(nbr_if_db_obj)
