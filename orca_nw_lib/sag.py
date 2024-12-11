# Configure logging
import logging

from orca_nw_lib.sag_gnmi import get_sag_info_from_device
from orca_nw_lib.sag_influxdb import insert_sag_info_in_influxdb
from orca_nw_lib.sag_promdb import insert_sag_info_in_promdb
from orca_nw_lib.utils import get_telemetry_db


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')



def get_sag_details(ip_addr: str) -> dict:
    
    """
    Retrieves the SAG (Static ARP Gateway) details for a specific device IP address.

    Args:
        ip_addr (str): The IP address of the device.

    Returns:
        dict: A dictionary containing the details of the SAG interface, including:
            - "interface_name" (str): Name of the interface.
            - "mode" (str): Mode of the interface.
            - "operational_status" (str): Operational status of the interface.
            - "ipv4_gateway" (str): IPv4 gateway address.
            - "ipv6_gateway" (str): IPv6 gateway address.
            - "virtual_mac" (str): Virtual MAC address.
            - "vrf" (str): VRF associated with the interface.
    """
    sag_data = get_sag_info_from_device(ip_addr)
    device_details = {}

    for sd in sag_data.items() or []:
        if sd[0] == "sonic-sag:sonic-sag":
            sag_data = sd[1]
            sag_intf_list = sag_data.get("SAG_INTF", {}).get("SAG_INTF_LIST", [])
            
            if sag_intf_list:
                sag_intf = sag_intf_list[0]  # Assuming you only want the first interface
                device_details.update({
                    "ifname": sag_intf.get("ifname"),
                    "mode": sag_intf.get("mode"),
                    "oper": sag_intf.get("oper"),
                    "v4GwIp": sag_intf.get("v4GwIp", [""])[0],
                    "v6GwIp": sag_intf.get("v6GwIp", [""])[0],
                    "vmac": sag_intf.get("vmac"),
                    "vrf": sag_intf.get("vrf")
                })
    
    return device_details


def discover_sag(device_ip:str):
    
    """
    Discovers the SAG information for a given device and inserts the details into a telemetry database.

    Args:
        device_ip (str): The IP address of the device.

    Raises:
        Exception: If an error occurs during the discovery process.
    """

    logger.debug("Discovering device with IP: %s", device_ip)
    try:
        logger.info("Discovering SAG with IP: %s", device_ip)
        sag_data = get_sag_details(device_ip)
        ## Check if the telemetry DB is influxdb or prometheus for inserting device info.
        if get_telemetry_db() == "influxdb":
            insert_sag_info_in_influxdb(device_ip, sag_data)
        elif get_telemetry_db() == "prometheus":
            insert_sag_info_in_promdb(device_ip, sag_data)
        else:
            logger.debug("Telemetry DB not configured, skipping SAG info insertion for IP: %s", device_ip)
    except Exception as e:
        logger.error("Error discovering device with IP %s: %s", device_ip, str(e))
        raise