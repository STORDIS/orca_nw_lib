import datetime
import ipaddress

from orca_nw_lib.interface import discover_interfaces
from orca_nw_lib.lldp import read_lldp_topo
from orca_nw_lib.portgroup import discover_port_groups


from .bgp import discover_bgp, discover_bgp_af_global


from .mclag import discover_mclag, discover_mclag_gw_macs

from .port_chnl import discover_port_chnl
from .vlan import discover_vlan
from .graph_db_models import Device
from .lldp import create_lldp_relations_in_db
from .utils import get_logging, get_orca_config
from .constants import network


_logger = get_logging().getLogger(__name__)


topology = {}


def insert_devices_in_db():
    """
    Insert devices and their neighbors into the database.

    This function iterates over the `topology` dictionary and inserts each device and its neighbors into the database.
    If a device with the same MAC address already exists in the database, it is skipped.
    For each neighbor of a device, if the neighbor device does not exist in the database, it is inserted.

    Parameters:
    None

    Returns:
    None
    """
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
    Discover the topology of the network.

    This function retrieves the network configuration from the ORCA config file and 
    starts the network discovery process. 
    The network to be discovered is specified in the configuration file. 

    Parameters:
    None

    Returns:
    bool: Returns True if the topology is successfully discovered and inserted into the database. 
    Returns False otherwise.
    """
    global topology
    nw_to_discover = get_orca_config().get(network)
    _logger.info(
        "Network Discovery Started using network provided {0}".format(nw_to_discover)
    )
    try:
        for ip_or_nw in nw_to_discover:
            ips = ipaddress.ip_network(ip_or_nw)
            for ip in ips:
                _logger.debug(f"Discovering device:{ip} and its neighbors.")
                read_lldp_topo(str(ip),topology)
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
        insert_devices_in_db()
    else:
        return False
    return True


def discover_all():
    """
    Discover all network devices and their configurations.

    This function performs the following tasks:
    - Calls the `discover_topology` function to discover the network topology.
    - Calls the `discover_interfaces` function to discover the interfaces of each device.
    - Calls the `create_lldp_relations_in_db` function to create the LLDP relations in the database.
    - Calls the `discover_port_groups` function to discover the port groups.
    - Calls the `discover_vlan` function to discover the VLAN configurations.
    - Calls the `discover_port_chnl` function to discover the port channel configurations.
    - Calls the `discover_mclag` function to discover the MCLAG configurations.
    - Calls the `discover_mclag_gw_macs` function to discover the MAC addresses of MCLAG gateways.
    - Calls the `discover_bgp` function to discover the BGP configurations.

    Returns:
    - True: If the discovery process was successful.
    - False: If the discovery process was unsuccessful.
    """
    discovery_start_time=datetime.datetime.now()
    if discover_topology():
        discover_interfaces()
        create_lldp_relations_in_db(topology)
        discover_port_groups()
        discover_vlan()
        discover_port_chnl()
        discover_mclag()
        discover_mclag_gw_macs()
        discover_bgp()
        discover_bgp_af_global()
    
        discovery_end_time=datetime.datetime.now()
       

        _logger.info(f"!! Discovered successfully {len(topology)} Devices in {discovery_end_time - discovery_start_time} !!")
        return True
    _logger.info("!! Discovery was Unsuccessful !!")
    return False
