import json
import datetime
import logging

from orca_nw_lib.device_gnmi import (
    get_device_meta_data,
    get_device_mgmt_intfc_info,
    get_device_img_name,
    get_device_details_from_device
)
from orca_nw_lib.influxdb_utils import create_point, write_to_influx

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def get_device_info(device_ip):
    """
    Retrieves the details of a device based on its IP address and sends the details to InfluxDB.
    
    Args:
        device_ip (str): The IP address of the device.
    
    Raises:
        Exception: If the device info cannot be retrieved.
    """
    try:
        logger.info("Retrieving device info for IP: %s", device_ip)
        
        metadata = get_device_meta_data(device_ip)
        mgmt_info = get_device_mgmt_intfc_info(device_ip)
        img_info = get_device_img_name(device_ip)
        details = get_device_details_from_device(device_ip)
        
        influx_data = {
            "Hostname": metadata["sonic-device-metadata:DEVICE_METADATA"]["DEVICE_METADATA_LIST"][0]["hostname"],
            "Image Name": details["img_name"],
            "Management Interface": details["mgt_intf"],
            "Management IP": details["mgt_ip"],
            "Hardware SKU": details["hwsku"],
            "MAC Address": details["mac"],
            "Platform": details["platform"],
            "Device Type": details["type"]
        }
        
        print("Device data for InfluxDB:", influx_data)
        send_to_influxdb(device_name="Device_Info", details=influx_data)
        logger.info("Device info sent to InfluxDB successfully for IP: %s", device_ip)
    
    except Exception as e:
        logger.error("Error retrieving device info for IP %s: %s", device_ip, e)


def send_to_influxdb(device_name: str, details: dict):
    """
    Writes device metrics to InfluxDB.
    
    Args:
        device_name (str): Name of the device to write metrics for.
        details (dict): A dictionary of device metrics.
    
    Raises:
        Exception: If data cannot be written to InfluxDB.
    """
    try:
        logger.info("Sending metrics to InfluxDB for device: %s", device_name)
        
        point = create_point(device_name)
        point.tag("device", "Device_Info")
        
        for key, value in details.items():
            point.field(key, value)
        
        point.time(datetime.datetime.now(datetime.timezone.utc))
        write_to_influx(point=point)
        
        logger.debug("Metrics for %s: %s", device_name, details)
        logger.info("Metrics for device %s sent to InfluxDB.", device_name)
    
    except Exception as e:
        logger.error("Error writing data to InfluxDB for device %s: %s", device_name, e)


def fetch_timeseries_data(device_ip: str):
    """
    Thread function to fetch and send time series data to InfluxDB.
    
    Args:
        device_ip (str): The IP address of the device for data collection.
    
    Raises:
        Exception: If there's an error fetching time series data.
    """
    try:
        logger.info("Starting time series data collection for IP: %s", device_ip)
        
        result = get_device_details_from_device(device_ip)
        logger.debug("Data received from device %s: %s", device_ip, result)
        
        details = {
            "path": "default_path",  # Adjust according to fetched data
            "value": json.dumps(result)
        }
        
        send_to_influxdb(device_name="default_device", details=details)
        logger.info("Time series data sent to InfluxDB for IP: %s", device_ip)
    
    except Exception as e:
        logger.error("Error fetching time series data for device IP %s: %s", device_ip, e)
