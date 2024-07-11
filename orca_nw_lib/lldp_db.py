from orca_nw_lib.interface_db import get_interface_of_device_from_db


def create_lldp_relations_in_db(topology):
    """
    Creates LLDP relations in the database based on the given topology.

    Args:
        topology (dict): A dictionary representing the topology of devices and their neighbors.

    Returns:
        None
    """
    for device, neighbors in topology.items():
        for nbr in neighbors:
            nbr_device = nbr.get("nbr_device")

            local_intfc = get_interface_of_device_from_db(
                device.mgt_ip, nbr.get("local_port")
            )

            nbr_intfc = get_interface_of_device_from_db(
                nbr_device.mgt_ip, nbr.get("nbr_port")
            )
            if local_intfc and nbr_intfc:
                local_intfc.lldp_neighbour.connect(nbr_intfc)