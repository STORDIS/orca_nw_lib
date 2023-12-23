import datetime
import ipaddress

from .interface import discover_interfaces
from .lldp import read_lldp_topo
from .portgroup import discover_port_groups


from .bgp import discover_bgp, discover_bgp_af_global


from .mclag import discover_mclag, discover_mclag_gw_macs

from .port_chnl import discover_port_chnl
from .vlan import discover_vlan
from .graph_db_models import Device
from .lldp import create_lldp_relations_in_db
from .utils import get_logging, get_networks


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


def discover_nw_features(device_ip: str = None):
    """
    Discovers the network features of a device or all the devices
    which are discovered using the `read_lldp_topo` function already.
    Args:
        device_ip (str): The IP address of the device to discover the network features for,
        if not specified network features are discovered for all devices in the database.

    Returns:
        None
    """
    discover_interfaces(device_ip)
    create_lldp_relations_in_db(topology)
    discover_port_groups(device_ip)
    discover_vlan(device_ip)
    discover_port_chnl(device_ip)
    discover_mclag(device_ip)
    discover_mclag_gw_macs(device_ip)
    discover_bgp(device_ip)
    discover_bgp_af_global(device_ip)


def discover_lldp_topology(device_ip: str):
    """
    Discovers the LLDP topology for a given switch IP address or network and inserts it into the database.

    Args:
        device_ip (str): The IP address or network to discover the topology for.

    Returns:
        bool: True if the topology was discovered and inserted into the database, False otherwise.
    """
    global topology
    _logger.debug(f"Discovering device:{device_ip} and its neighbors using LLDP.")
    try:
        read_lldp_topo(device_ip, topology)
    except Exception as err:
        _logger.error(err)
        return False
    
    if topology:
        import pprint
        _logger.info(
            "Discovered topology using IP provided {0}: \n{1}".format(
                device_ip, pprint.pformat(topology)
            )
        )
        _logger.info("Inserting Device LLDP topology to database.")
        insert_devices_in_db()
    else:
        _logger.info(
            "!! Discovery was Unsuccessful for {0} !!".format(device_ip)
        )
        return False
    
    return True

def discover_device(ip_or_nw: str):
    """
    Discovers devices in a network using the provided IP address or network.

    Args:
        ip_or_nw (str): The IP address or network to perform the network discovery on.

    Returns:
        None
    """
    _logger.info(
            "Network Discovery Started using network provided {0}".format(ip_or_nw)
        )
    for device_ip in ipaddress.ip_network(ip_or_nw):
        device_ip=str(device_ip)
        _logger.info(
                "Discovering device :{}".format(device_ip)
            )
        discovery_start_time = datetime.datetime.now()
        result=discover_lldp_topology(device_ip)
        for device_obj in topology:
            _logger.info(f"Discovering network features for {device_obj.mgt_ip}.")
            discover_nw_features(device_obj.mgt_ip)
        discovery_end_time = datetime.datetime.now()
        _logger.info(
            f"!! Discovered {len(topology)} Devices topology using {device_ip} in {discovery_end_time - discovery_start_time} !!"
        )
    ## topology dictionary should be emptied now, for further discovery requests
    topology.clear()
    
    return result

def discover_device_from_config() -> bool:
    """
    Discover devices from the configuration file.

    This function iterates over the network addresses obtained from the
    'get_networks' function and calls the 'discover_device' function for each
    address. After iterating over all the addresses, it returns True.

    Returns:
        bool: True indicating that the device discovery was successful.
    """
    for ip_or_nw in get_networks():
        discover_device(ip_or_nw)
    return True
