import ipaddress
import time

from orca_nw_lib.lldp_db import create_lldp_relations_in_db
from orca_nw_lib.system import discover_system
from .common import DiscoveryFeature

from .device import discover_device_basic_system_details, get_device_details
from .device_db import get_all_devices_ip_from_db
from .gnmi_sub import gnmi_subscribe, sync_response_received

from .interface import discover_interfaces, enable_all_ifs
from .lldp import discover_lldp_info, get_all_lldp_neighbor_device_ips
from .portgroup import discover_port_groups

from .bgp import discover_bgp, discover_bgp_neighbors

from .mclag import discover_mclag, discover_mclag_gw_macs
from .sag import discover_sag
from .platform import discover_platform

from .port_chnl import discover_port_chnl
from .stp import discover_stp
from .stp_port import discover_stp_port
from .stp_vlan import discover_stp_vlan
from .vlan import discover_vlan
from .utils import get_logging, get_networks, is_grpc_device_listening

_logger = get_logging().getLogger(__name__)

topology = {}


def _discover_device_and_enable_ifs(device_ip: str):
    report = []
    device_ip = str(device_ip)
    if not is_grpc_device_listening(device_ip):
        log_msg = f"Can not discover, Device {device_ip} is not reachable !!"
        _logger.error(log_msg)
        report.append(log_msg)
        return report
    _logger.info("Discovering device :{}".format(device_ip))

    discover_nw_features(device_ip, DiscoveryFeature.device_info)

    discover_nw_features(device_ip, DiscoveryFeature.interface)

    discover_nw_features(device_ip, DiscoveryFeature.port_group)

    ## Once Discovered the device's interfaces and port groups, Subscribe for notifications
    gnmi_subscribe(device_ip, force_resubscribe=True)
    # Retry mechanism with sleep time for sync_response_received
    max_retries = 5  # Set maximum number of retries
    retry_delay = 2  # Set delay between retries in seconds
    for _ in range(max_retries):
        sync_received = sync_response_received(device_ip)
        if sync_received:
            _logger.info(f"Sync response received for device {device_ip}.")
            break
        else:
            _logger.warning(
                f"Sync response not received for device {device_ip}, retrying in {retry_delay} seconds..."
            )
            time.sleep(retry_delay)
    else:
        _logger.error(f"Timeout waiting for sync response from device {device_ip}")
        report.append(f"Timeout waiting for sync response from device {device_ip}")

    # Enabling all IFs so that LLDP tables are populated.
    try:
        _logger.info(
            f"Enabling all interfaces on device {device_ip}, So that LLDP tables are populated."
        )
        enable_all_ifs(device_ip)
    except Exception as e:
        _logger.info(f"Interface Enable Failed on device {device_ip}, Reason: {e}")

    discover_nw_features(device_ip, DiscoveryFeature.lldp_info)


def _discover_device_and_lldp_info(device_ips: list):
    """
    Recursively discover a device and its neighbors using LLDP information.

    The function first discovers the device using discover_device_and_enable_ifs
    and then discovers all its LLDP neighbors. If a neighbor is not already
    discovered, it calls itself to discover the neighbor and so on.

    Args:
        device_ips (list): The IP address of the device to be discovered.

    Returns:
        None
    """

    # Discover interfaces, devices, port groups and lldp info first.
    for device_ip in device_ips:
        _discover_device_and_enable_ifs(device_ip)

    # Discover lldp neighbors for each discovered device.
    for device_ip in device_ips:
        for nbr_ip in get_all_lldp_neighbor_device_ips(device_ip):
            if not get_device_details(
                    nbr_ip
            ):  # Discover only if not already discovered in order to prevent loop
                _discover_device_and_lldp_info(device_ips=[nbr_ip])


def discover_device(device_ips: list, feature_to_discover: DiscoveryFeature = None):
    """
    Discover the devices, in the list `device_ips` with the features specified.
    Function not only discovers device's basic system details but also its network features and topology associated.
    If no feature is specified, a complete discovery of all of the features is triggered.

    Parameters:
        device_ips (list): List of device IPs to be discovered.
        feature_to_discover (DiscoveryFeature): Feature to discover. If not specified, a complete device discovery with all its features triggered.
        

    Returns:
        None
    """
    # Discover the device and its neighbors and basic device info
    device_ips = device_ips if isinstance(device_ips, list) else [device_ips]
    _discover_device_and_lldp_info(device_ips)

    # Discover the rest of the features
    # some links can only be created after all teh topology devices are discovered
    for ip in get_all_devices_ip_from_db() or []:
        create_lldp_relations_in_db(ip)
        if feature_to_discover:
            discover_nw_features(ip, feature_to_discover)
        else:
            discover_nw_features(ip, DiscoveryFeature.port_channel)
            discover_nw_features(ip, DiscoveryFeature.vlan)
            discover_nw_features(ip, DiscoveryFeature.mclag)
            discover_nw_features(ip, DiscoveryFeature.mclag_gw_macs)
            discover_nw_features(ip, DiscoveryFeature.bgp)
            discover_nw_features(ip, DiscoveryFeature.bgp_neighbors)
            discover_nw_features(ip, DiscoveryFeature.stp)
            discover_nw_features(ip, DiscoveryFeature.stp_port)
            discover_nw_features(ip, DiscoveryFeature.stp_vlan)
        gnmi_subscribe(ip)


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
        _logger.info(
            "Network Discovery Started using network provided {0}".format(ip_or_nw)
        )
        report = []
        if not ip_or_nw:
            _logger.error(
                "Invalid network address- {ip_or_nw}, can not discover devices !!"
            )
            return report
        discover_device(device_ips=[str(ip) for ip in ipaddress.ip_network(ip_or_nw, strict=False)])
    return report


def discover_nw_features(device_ip: str, feature: DiscoveryFeature) -> None:
    """
    Discover network features for a given device.

    Parameters:
        device_ip (str): Device IP address.
        feature (str): Feature to trigger discovery.

    Returns:
        None
    """
    match feature:
        case DiscoveryFeature.interface:
            try:
                discover_interfaces(device_ip)
            except Exception as e:
                _logger.info(f"Interface Discovery Failed on device {device_ip}, Reason: {e}")
                return f"Interface Discovery Failed on device {device_ip}, Reason: {e}"
        case DiscoveryFeature.port_group:
            try:
                discover_port_groups(device_ip)
            except Exception as e:
                _logger.info(f"Port Group Discovery Failed on device {device_ip}, Reason: {e}")
                return f"Port Group Discovery Failed on device {device_ip}, Reason: {e}"
        case DiscoveryFeature.device_info:
            try:
                discover_device_basic_system_details(device_ip)
            except Exception as e:
                _logger.info(f"Device Info Discovery Failed on device {device_ip}, Reason: {e}")
                return f"Device Info Discovery Failed on device {device_ip}, Reason: {e}"
        case DiscoveryFeature.lldp_info:
            try:
                discover_lldp_info(device_ip)
            except Exception as e:
                _logger.info(f"LLDP Info Discovery Failed on device {device_ip}, Reason: {e}")
                return f"LLDP Info Discovery Failed on device {device_ip}, Reason: {e}"
        case DiscoveryFeature.mclag:
            try:
                discover_mclag(device_ip)
            except Exception as e:
                _logger.info(f"MCLAG Discovery Failed on device {device_ip}, Reason: {e}")
                return f"MCLAG Discovery Failed on device {device_ip}, Reason: {e}"
        case DiscoveryFeature.mclag_gw_macs:
            try:
                discover_mclag_gw_macs(device_ip)
            except Exception as e:
                _logger.info(f"MCLAG GW MAC Discovery Failed on device {device_ip}, Reason: {e}")
                return f"MCLAG GW MAC Discovery Failed on device {device_ip}, Reason: {e}"
        case DiscoveryFeature.vlan:
            try:
                discover_vlan(device_ip)
            except Exception as e:
                _logger.info(f"VLAN Discovery Failed on device {device_ip}, Reason: {e}")
                return f"VLAN Discovery Failed on device {device_ip}, Reason: {e}"
        case DiscoveryFeature.port_channel:
            try:
                discover_port_chnl(device_ip)
            except Exception as e:
                _logger.info(f"Port Channel Discovery Failed on device {device_ip}, Reason: {e}")
                return f"Port Channel Discovery Failed on device {device_ip}, Reason: {e}"
        case DiscoveryFeature.bgp:
            try:
                discover_bgp(device_ip)
            except Exception as e:
                _logger.info(f"BGP Discovery Failed on device {device_ip}, Reason: {e}")
                return f"BGP Discovery Failed on device {device_ip}, Reason: {e}"
        case DiscoveryFeature.bgp_neighbors:
            try:
                discover_bgp_neighbors(device_ip)
            except Exception as e:
                _logger.info(f"BGP Neighbor Discovery Failed on device {device_ip}, Reason: {e}")
                return f"BGP Neighbor Discovery Failed on device {device_ip}, Reason: {e}"
        case DiscoveryFeature.stp:
            try:
                discover_stp(device_ip)
            except Exception as e:
                _logger.info(f"STP Discovery Failed on device {device_ip}, Reason: {e}")
                return f"STP Discovery Failed on device {device_ip}, Reason: {e}"
        case DiscoveryFeature.sag:
            try:
                discover_sag(device_ip) 
            except Exception as e:  
                _logger.info(f"SAG Discovery Failed on device {device_ip}, Reason: {e}")
                return f"SAG Discovery Failed on device {device_ip}, Reason: {e}"
        case DiscoveryFeature.stp_port:
            try:
                discover_stp_port(device_ip)
            except Exception as e:
                _logger.info(f"STP Port Discovery Failed on device {device_ip}, Reason: {e}")
                return f"STP Port Discovery Failed on device {device_ip}, Reason: {e}"
        case DiscoveryFeature.platform:
            try:
                discover_platform(device_ip)
            except Exception as e:
                _logger.info(f"Platform Port Discovery Failed on device {device_ip}, Reason: {e}")
                return f"Platform Port Discovery Failed on device {device_ip}, Reason: {e}"
        case DiscoveryFeature.stp_vlan:
            try:
                discover_stp_vlan(device_ip)
            except Exception as e:
                _logger.info(f"STP VLAN Discovery Failed on device {device_ip}, Reason: {e}")
                return f"STP VLAN Discovery Failed on device {device_ip}, Reason: {e}"
        case DiscoveryFeature.system:
            try:
                discover_system(device_ip)
            except Exception as e:
                _logger.info(f"System Discovery Failed on device {device_ip}, Reason: {e}")
                return f"System Discovery Failed on device {device_ip}, Reason: {e}"
        case _:
            _logger.error("Invalid feature specified")
            return "Invalid feature specified"
