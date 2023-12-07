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


def discover_lldp_topology(device_ip):
    """
    Discovers the LLDP topology for a given switch IP address or network and inserts it into the database.

    Args:
        device_ip (str): The IP address or network to discover the topology for.

    Returns:
        bool: True if the topology was discovered and inserted into the database, False otherwise.
    """
    global topology
    for ip in ipaddress.ip_network(device_ip):
        _logger.debug(f"Discovering device:{ip} and its neighbors.")
        try:
            read_lldp_topo(str(ip), topology)
        except Exception as err:
            _logger.error(err)
            return False
    if topology:
        _logger.info("Inserting Device LLDP topology to database.")
        insert_devices_in_db()
    else:
        return False
    return True


def discover_all():
    """
    Discover all networks and their features.

    This function retrieves the network configuration from the Orca configuration
    and starts the network discovery process for each network. It logs the start
    of the discovery process and the discovered topology for each network. If the
    discovery process fails for a network, it logs an error message. Finally, it
    logs the total number of devices discovered and the duration of the discovery
    process.

    Returns:
        None
    """
    nw_to_discover = get_orca_config().get(network)
    _logger.info(
        "Network Discovery Started using network provided {0}".format(nw_to_discover)
    )

    discovery_start_time = datetime.datetime.now()
    for ip_or_nw in nw_to_discover:
        for ip in ipaddress.ip_network(ip_or_nw):
            if discover_lldp_topology(ip):
                discover_nw_features()
                import pprint

                _logger.info(
                    "Discovered topology using network provided {0}: \n{1}".format(
                        nw_to_discover, pprint.pformat(topology)
                    )
                )
            else:
                _logger.info(
                    "!! Discovery was Unsuccessful for {0} !!".format(ip_or_nw)
                )
    discovery_end_time = datetime.datetime.now()
    _logger.info(
        f"!! Discovered successfully {len(topology)} Devices in {discovery_end_time - discovery_start_time} !!"
    )
