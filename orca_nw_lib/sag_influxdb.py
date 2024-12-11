import logging
from orca_nw_lib.influxdb_utils import create_point, write_to_influx

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def insert_sag_info_in_influxdb(device_ip: str, sag_data: dict):
    """
    Inserts the SAG info data into InfluxDB.

    Args:
        device_ip (str): The IP address of the device.
        sag_data (dict): The SAG info data in dictionary format.

    Raises:
        Exception: If an error occurs while sending data to InfluxDB.
    """
    try:
        #print("sag_data", sag_data)
        # Create a Point object for the data
        point = create_point("SAG_INTF")
        sag_point = point.tag("device_ip", device_ip)
        sag_point.field("ifname", sag_data.get("ifname", ""))
        sag_point.field("mode", sag_data.get("mode", ""))
        sag_point.field("oper", sag_data.get("oper", ""))
        sag_point.field("v4GwIp", sag_data.get("v4GwIp", ""))
        sag_point.field("v6GwIp", sag_data.get("v6GwIp", ""))
        sag_point.field("vmac", sag_data.get("vmac", ""))
        sag_point.field("vrf", sag_data.get("vrf", ""))
        
        # Write the Point to the InfluxDB bucket
        write_to_influx(point=point)
        #logger.info("Metrics pushed to InfluxDB successfully for IP: %s", device_ip)
    
    except Exception as e:
        print(f"An error occurred while sending data to InfluxDB: {e}")
