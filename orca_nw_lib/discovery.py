import ipaddress

from orca_nw_lib.interface import discover_interfaces
from orca_nw_lib.portgroup import discover_port_groups


from .bgp import discover_bgp


from .mclag import discover_mclag, discover_mclag_gw_macs

from .port_chnl import discover_port_chnl
from .vlan import discover_vlan
from .device import create_device_graph_object
from .graph_db_models import Device
from .lldp import create_lldp_relations_in_db, get_lldp_neighbors
from .utils import get_logging, get_orca_config
from .constants import network


_logger = get_logging().getLogger(__name__)


topology = {}


def read_lldp_topo(ip: str):
    """
    Starting from an IP address, Read LLDP table recursively 
    untill all the connected devices are discovered.
    Keeps the discovered devices in the `topology` dictionary.
    Sample `topology` dictionary :
    {<Device: 10.10.130.212>: [{'local_port': 'Ethernet0',
                            'nbr_device': <Device: 10.10.130.210>,
                            'nbr_port': 'Ethernet1'}]}
    Args:
        ip (str): The IP address of the device.

    Returns:
        None

    Raises:
        Exception: If there is an error while discovering the device.

    Description:
        This function reads the LLDP (Link Layer Discovery Protocol) topology of a device. It takes an IP address as input and creates a device graph object using the `create_device_graph_object` function. If the device is not already in the `topology` dictionary, it retrieves the LLDP neighbors of the device using the `get_lldp_neighbors` function. For each neighbor, it creates a neighbor device graph object and checks if the neighbor device has a management interface. If it does, it appends the neighbor device and its corresponding ports to a temporary array. The temporary array is then assigned to the `topology` dictionary with the device as the key. Finally, the function recursively calls itself for each neighbor device to discover their LLDP topology.

        If an exception occurs during the execution of the function, an error message is logged using the `_logger` object.

    """
    try:
        device = create_device_graph_object(ip)
        if device not in topology:
            nbrs = get_lldp_neighbors(ip)
            temp_arr = []
            for nbr in nbrs:
                nbr_device = create_device_graph_object(nbr.get("nbr_ip"))
                # Following check prevents adding an empty device object in topology.
                # with no mgt_ip any no other properties as well.
                # This may happen if device is pingable but gnmi connection can not be established.
                if nbr_device.mgt_intf and nbr_device.mgt_intf:
                    temp_arr.append(
                        {
                            "nbr_device": create_device_graph_object(nbr.get("nbr_ip")),
                            "nbr_port": nbr.get("nbr_port"),
                            "local_port": nbr.get("local_port"),
                        }
                    )

            topology[device] = temp_arr

            for nbr in nbrs or []:
                read_lldp_topo(nbr.get("nbr_ip"))
    except Exception as te:
        _logger.info(f"Device {ip} couldn't be discovered reason : {te}.")


def insert_topology_in_db(topology):
    for device, neighbors in topology.items():
        if Device.nodes.get_or_none(mac=device.mac) is None:
            device.save()
        # create its neighbor
        for nbr in neighbors:
            nbr_device = nbr.get("nbr_device")
            if Device.nodes.get_or_none(mac=nbr_device.mac) is None:
                nbr_device.save()


def discover_topology():
    """
    Discover the network topology.

    This function discovers the network topology by querying the Orca configuration to obtain the network to be discovered.
    It then iterates over each IP and calls the function `read_lldp_topo` to discover the LLDP topology of the device and its neighbors.

    Parameters:
        None

    Returns:
        bool: True if the network topology was successfully discovered and inserted into the database, False otherwise.
    """
    nw_to_discover = get_orca_config().get(network)
    _logger.info(
        "Network Discovery Started using network provided {0}".format(nw_to_discover)
    )
    try:
        for ip_or_nw in nw_to_discover:
            ips = ipaddress.ip_network(ip_or_nw)
            for ip in ips:
                _logger.debug(f"Discovering device:{ip} and its neighbors.")
                read_lldp_topo(str(ip))
        import pprint

        _logger.info(
            "Discovered topology using network provided {0}: \n{1}".format(
                nw_to_discover, pprint.pformat(topology)
            )
        )
        _logger.info(f"Total devices discovered:{len(topology)}")

    except ValueError as ve:
        _logger.error(ve)
        return False

    if topology:
        _logger.info("Inserting Device LLDP topology to database.")
        insert_topology_in_db(topology)
    else:
        return False
    return True


def create_lldp_rel():
    """
    Create an LLDP relation using the global dictionary `topology`.
    Function should be called after discovering the interfaces.

    Parameters:
        None

    Returns:
        None
    """
    _logger.info("Discovering LLDP relations.")
    create_lldp_relations_in_db(topology)


def discover_all():
    """
    Discover all devices in the network and gather information about their
    interfaces, port groups, VLANs, LLDP relationships, port channels,
    MCLAG configurations, MCLAG gateway MAC addresses, and BGP configurations.

    :return: True if the discovery was successful, False otherwise.
    """
    global topology

    topology = {}
    if discover_topology():
        discover_interfaces()
        create_lldp_rel()
        discover_port_groups()
        discover_vlan()
        discover_port_chnl()
        discover_mclag()
        discover_mclag_gw_macs()
        discover_bgp()

        _logger.info(f"!! Discovered successfully {len(topology)} Devices !!")
        return True
    _logger.info("!! Discovery was Unsuccessful !!")
    return False
