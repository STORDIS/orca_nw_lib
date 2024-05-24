import datetime
import ipaddress

from orca_nw_lib.gnmi_sub import gnmi_subscribe

from .interface import discover_interfaces
from .lldp import read_lldp_topo
from .portgroup import discover_port_groups


from .bgp import discover_bgp, discover_bgp_af_global


from .mclag import discover_mclag, discover_mclag_gw_macs

from .port_chnl import discover_port_chnl
from .vlan import discover_vlan
from .graph_db_models import Device
from .lldp import create_lldp_relations_in_db
from .utils import get_logging, get_networks, ping_ok


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


def discover_nw_features(device_ip: str):
    """
    Discovers various network features on the device with the given IP address.

    Parameters:
    - device_ip (str): The IP address of the device to be discovered.

    Returns:
    - report (list): A list of strings containing any errors or failures encountered during the discovery process.
    """
    
    report = []
    try:
        discover_interfaces(device_ip)
    except Exception as e:
        report.append(
            f"Interface Discovery Failed on device {device_ip}, Reason: {e}"
        )

    create_lldp_relations_in_db(topology)

    try:
        discover_port_groups(device_ip)
    except Exception as e:
        report.append(
            f"Port Group Discovery Failed on device {device_ip}, Reason: {e}"
        )

    try:
        discover_vlan(device_ip)
    except Exception as e:
        report.append(
            f"VLAN Discovery Failed on device {device_ip}, Reason: {e}"
        )

    try:
        discover_port_chnl(device_ip)
    except Exception as e:
        report.append(
            f"Port Channel Discovery Failed on device {device_ip}, Reason: {e}"
        )

    try:
        discover_mclag(device_ip)
    except Exception as e:
        report.append(
            f"MCLAG Discovery Failed on device {device_ip}, Reason: {e}"
        )
    try:
        discover_mclag_gw_macs(device_ip)
    except Exception as e:
        report.append(
            f"MCLAG GW MAC Discovery Failed on device {device_ip}, Reason: {e}"
        )
    try:
        discover_bgp(device_ip)
    except Exception as e:
        report.append(
            f"BGP Discovery Failed on device {device_ip}, Reason: {e}"
        )
    try:
        discover_bgp_af_global(device_ip)
    except Exception as e:
        report.append(
            f"BGP Global Discovery Failed on device {device_ip}, Reason: {e}"
        )
    ## Once Discovered the device, Subscribe for notfications
    gnmi_subscribe(device_ip)
    return report


def discover_lldp_topology(device_ip: str):
    """
    Discover the LLDP topology of a device.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        list: A list of LLDP reports.

    Raises:
        None
    """
    
    global topology
    _logger.debug(f"Discovering device:{device_ip} and its neighbors using LLDP.")
    lldp_report = []
    read_lldp_topo(device_ip, topology, lldp_report)

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
            "!! LLDP Discovery was Unsuccessful triggered with IP {0} !!".format(
                device_ip
            )
        )
    return lldp_report


def discover_device(ip_or_nw: str):
    """
    Discover devices in a network given an IP address or network.

    Args:
        ip_or_nw (str): The IP address or network to perform the discovery on.

    Returns:
        list: A list containing the discovery report, which includes information about the discovered devices and network features.

    """
    
    _logger.info(
        "Network Discovery Started using network provided {0}".format(ip_or_nw)
    )
    report = []
    if not ip_or_nw:
        _logger.error("Invalid network address- {ip_or_nw}, can not discover devices !!")
        return report
    for device_ip in ipaddress.ip_network(ip_or_nw):
        device_ip = str(device_ip)
        if not ping_ok(device_ip):
            log_msg = f"Can not discover, Device {device_ip} is not reachable !!"
            _logger.error(log_msg)
            report.append(log_msg)
            continue
        _logger.info("Discovering device :{}".format(device_ip))
        discovery_start_time = datetime.datetime.now()
        if lldp_report := discover_lldp_topology(device_ip):
            report += lldp_report
        for device_obj in topology:
            _logger.info(f"Discovering network features for {device_obj.mgt_ip}.")
            if nw_feature_report := discover_nw_features(device_obj.mgt_ip):
                report += nw_feature_report
        discovery_end_time = datetime.datetime.now()
        _logger.info(
            f"!! Discovered {len(topology)} Devices topology using {device_ip} in {discovery_end_time - discovery_start_time} !!"
        )
    ## topology dictionary should be emptied now, for further discovery requests
    topology.clear()
    return report


def discover_device_from_config() -> []:
    """
    Discover devices from the configuration file.

    This function iterates over the network addresses obtained from the
    'get_networks' function and calls the 'discover_device' function for each
    address. After iterating over all the addresses, it returns True.

    Returns:
        report (list): A report of discovered devices and statuses.
    """
    report = []
    for ip_or_nw in get_networks():
        if temp_report := discover_device(ip_or_nw):
            report += temp_report
    return report
