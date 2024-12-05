import logging
from prometheus_client import CollectorRegistry, Info

from orca_nw_lib.promdb_utils import write_to_prometheus

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

registry = CollectorRegistry()
# Example for PSU Info
psu_info = Info("psu_info", "PSU Information", labelnames=["device_ip"], registry=registry)

# Similarly for Fan Info
fan_info = Info("fan_info", "Fan Information", labelnames=["device_ip"], registry=registry)

# For Temperature Info
temp_info = Info("temperature_info", "Temperature Information", labelnames=["device_ip"], registry=registry)

# For I2C Error Stats
#i2c_error_stats = Info("i2c_error_stats", "I2C Error Statistics", labelnames=["device_ip"], registry=registry)


def insert_platform_info_in_prometheus(device_ip: str, platform_data: dict):
    
    """
    Inserts platform information into Prometheus for a given device.

    This function processes platform data including PSU, FAN, and TEMPERATURE
    information for a device, labels them using Prometheus `Info` metrics, 
    and then pushes these metrics to the Prometheus Pushgateway.

    Args:
        device_ip (str): The IP address of the device.
        platform_data (dict): A dictionary containing platform information 
                              including PSU, FAN, and TEMPERATURE data.

    Raises:
        None, but logs an error if there is an exception during metric processing
        or when sending metrics to Prometheus.
    """
    try:
        # Push PSU Info to Prometheus
        for psu in platform_data.get("PSU_INFO", []):
            #print("psu", psu)
            psu_info.labels(device_ip=device_ip).info({
                "index": psu.get("index"),
                "input_current": psu.get("input_current"),
                "input_power": psu.get("input_power"),
                "input_voltage": psu.get("input_voltage"),
                "is_replaceable": str(psu.get("is_replaceable")),
                "led_status": psu.get("led_status"),
                "mfr_id": psu.get("mfr_id"),
                "model": psu.get("model"),
                "name": psu.get("name"),
                "num_fans": psu.get("num_fans"),
                "output_current": psu.get("output_current"),
                "output_power": psu.get("output_power"),
                "output_voltage": psu.get("output_voltage"),
                "presence": str(psu.get("presence")),
                "serial": psu.get("serial"),
                "status": str(psu.get("status")),
                "type": psu.get("type")
            })
        logger.info("PSU info pushed to Pushgateway successfully.")
    
        # Push FAN Info to Prometheus
        for fan in platform_data.get("FAN_INFO", []):
            fan_info.labels(device_ip=device_ip).info({
                "index": fan.get("index"),
                "direction": fan.get("direction"),
                "drawer_name": fan.get("drawer_name"),
                "is_replaceable": str(fan.get("is_replaceable")),
                "led_status": fan.get("led_status"),
                "model": fan.get("model"),
                "name": fan.get("name"),
                "presence": str(fan.get("presence")),
                "serial": fan.get("serial"),
                "speed": fan.get("speed"),
                "speed_target": fan.get("speed_target"),
                "speed_tolerance": fan.get("speed_tolerance"),
                "status": str(fan.get("status"))
            })
        logger.info("Fan info pushed to Pushgateway successfully.")
    
        # Push TEMPERATURE Info to Prometheus
        for temp in platform_data.get("TEMPERATURE_INFO", []):
            temp_info.labels(device_ip=device_ip).info({
                "index": temp.get("index"),
                "critical_high_threshold": temp.get("critical_high_threshold"),
                "critical_low_threshold": temp.get("critical_low_threshold"),
                "high_threshold": temp.get("high_threshold"),
                "is_replaceable": str(temp.get("is_replaceable")),
                "low_threshold": temp.get("low_threshold"),
                "maximum_temperature": temp.get("maximum_temperature"),
                "minimum_temperature": temp.get("minimum_temperature"),
                "name": temp.get("name"),
                "temperature": temp.get("temperature")
            })
        logger.info("Temperature info pushed to Pushgateway successfully.")
        # Push to Prometheus Pushgateway
        write_to_prometheus(registry=registry)
        logger.info("Metrics pushed to Pushgateway successfully for IP: %s", device_ip)
    except Exception as e:
        logger.error(f"Error sending metrics to Pushgateway: {e}")
