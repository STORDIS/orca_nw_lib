from orca_nw_lib.system_gnmi import get_system_info_from_device
from orca_nw_lib.system_influxdb import insert_system_in_influxdb
from orca_nw_lib.system_promdb import insert_system_in_prometheus
from orca_nw_lib.utils import get_logging, get_telemetry_db


_logger=logger = get_logging().getLogger(__name__)


def get_system_details(ip_addr: str) -> dict:
    """
    Create a system details dictionary based on the given IP address.

    Args:
        ip_addr (str): The IP address of the device.

    Returns:
        dict: A dictionary containing device system details.
    """
    sys_data = get_system_info_from_device(ip_addr)
    device_details = {}

    uptime = sys_data.get('openconfig-system-ext:state', {})
    device_details.update({
        "reboot_cause": uptime.get('reboot-cause'),
        "show_user_list": uptime.get('show-user-list'),
        "uptime": uptime.get('uptime')
    })
 
    ntp = sys_data.get('openconfig-system:server', [])
    ntp_state = ntp[0]['state']
    device_details.update({
        "server_address": ntp_state.get('address'),
        "now": ntp_state.get('now'),
        "peer_delay": ntp_state.get('peer-delay'),
        "peer_jitter": ntp_state.get('peer-jitter'),
        "peer_offset": ntp_state.get('peer-offset'),
        "peer_type": ntp_state.get('peer-type'),
        "poll_interval": ntp_state.get('poll-interval'),
        "reach": ntp_state.get('reach'),
        "sel_mode": ntp_state.get('sel-mode'),
        "stratum": ntp_state.get('stratum')
    })
    
    return device_details


def discover_system(device_ip:str):
    """
    Discover a system by its IP address and insert the system details into the database.

    Args:
        device_ip (str): The IP address of the device to be discovered.

    Raises:
        Exception: If an error occurs during the discovery process.
    """
    _logger.debug("Discovering device with IP: %s", device_ip)
    try:
        _logger.info("Discovering system with IP: %s", device_ip)
        system_data = get_system_details(device_ip)
        ## Check if the telemetry DB is influxdb or prometheus for inserting device info.
        if get_telemetry_db() == "influxdb":
            insert_system_in_influxdb(device_ip, system_data)
        elif get_telemetry_db() == "prometheus":
            insert_system_in_prometheus(device_ip, system_data)
        else:
            _logger.debug("Telemetry DB not configured, skipping system info insertion for IP: %s", device_ip)

    except Exception as e:
        _logger.error("Error discovering device with IP %s: %s", device_ip, str(e))
        raise