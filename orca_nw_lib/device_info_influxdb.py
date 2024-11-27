import logging

from orca_nw_lib.influxdb_utils import create_point, write_to_influx

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def insert_device_info_in_influxdb(device_ip:str, device_info):
    """
    Converts the Device object into a dictionary format and sends it to InfluxDB.
    Args:
        device_ip (String): The Device ip.
        device_info (Device): The Device object containing device details.
    """
    try:
        point = create_point("device_info") \
            .tag("device_ip", device_ip) \
            .field("img_name", device_info.img_name) \
            .field("mgt_interface", device_info.mgt_intf) \
            .field("mgt_ip", device_info.mgt_ip) \
            .field("hardware_sku", device_info.hwsku) \
            .field("mac", device_info.mac) \
            .field("platform", device_info.platform) \
            .field("device_type", device_info.type) \
            .field("system_status", 1 if device_info.system_status == "System is ready" else 0) \
            
        write_to_influx(point=point)
        logger.info("Device info sent to InfluxDB successfully for IP: %s", device_ip)
    except Exception as e:
        logger.error(f"Failed to push metrics to Pushgateway for device: {e}")