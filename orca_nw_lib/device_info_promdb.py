import logging
from prometheus_client import CollectorRegistry, Info
from orca_nw_lib.promdb_utils import write_to_prometheus

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
 
# Create a registry for this device
registry = CollectorRegistry()
 
# Define an Info metric for device details
info_device_details = Info('device_info', 'Detailed information about the device', labelnames=["device_ip"], registry=registry)
 
def insert_device_info_in_prometheus(device_ip:str, device_info):
    """
    Converts the Device object into Prometheus metrics and pushes them to the Pushgateway.
   
    Args:
        device_info (Device): The Device object containing device details.
    """
    try:
        info_device_details.labels(device_ip=device_ip).info({
            "img_name": device_info.img_name,
            "mgt_interface": device_info.mgt_intf,
            "mgt_ip": device_info.mgt_ip,
            "hardware_sku": device_info.hwsku,
            "mac": device_info.mac,
            "platform": device_info.platform,
            "device_type": device_info.type,
            "system_status": str(1 if device_info.system_status == "System is ready" else 0)
        })
        write_to_prometheus(registry=registry)
        logger.info("Metrics successfully pushed to Pushgateway for device")
    except Exception as e:
        logger.error(f"Failed to push metrics to Pushgateway for device: {e}")