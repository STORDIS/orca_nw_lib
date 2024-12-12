import logging
import traceback
from orca_nw_lib.influxdb_utils import create_point, write_to_influx

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def insert_platform_info_in_influxdb(device_ip: str, platform_data: dict):
    try:
        point1 = create_point("PSU_INFO")
        device_point = point1.tag("device_ip", device_ip)
        for psu in platform_data.get("PSU_INFO", []):
            psu_point = device_point.tag("PSU", psu.get("index", ""))
            psu_point.field("index", psu.get("index"))
            psu_point.field("input_current", psu.get("input_current"))
            psu_point.field("input_power", psu.get("input_power"))
            psu_point.field("input_voltage", psu.get("input_voltage"))
            psu_point.field("is_replaceable", psu.get("is_replaceable"))
            psu_point.field("led_status", psu.get("led_status"))
            psu_point.field("mfr_id", psu.get("mfr_id"))
            psu_point.field("model", psu.get("model"))
            psu_point.field("name", psu.get("name"))
            psu_point.field("num_fans", psu.get("num_fans"))
            psu_point.field("output_current", psu.get("output_current"))
            psu_point.field("output_power", psu.get("output_power"))
            psu_point.field("output_voltage", psu.get("output_voltage"))
            psu_point.field("presence", psu.get("presence"))
            psu_point.field("serial", psu.get("serial"))
            psu_point.field("type", psu.get("type"))
            psu_point.field("status", psu.get("status"))
            write_to_influx(point=point1)
        #logger.info("PSU info successfully sent to InfluxDB.")
    except Exception as e:
        logger.error(f"Error processing PSU metrics: {e}")


    
    try:
        point2 = create_point("FAN_INFO")
        device_point = point2.tag("device_ip", device_ip)
        for fan in platform_data.get("FAN_INFO", []):
            fan_point = device_point.tag("FAN", fan.get("index", ""))  
            fan_point.field("index", fan.get("index")) 
            fan_point.field("direction", fan.get("direction"))
            fan_point.field("drawer_name", fan.get("drawer_name"))
            fan_point.field("is_replaceable", fan.get("is_replaceable"))
            fan_point.field("led_status", fan.get("led_status"))
            fan_point.field("model", fan.get("model"))
            fan_point.field("name", fan.get("name"))
            fan_point.field("presence", fan.get("presence"))
            fan_point.field("serial", fan.get("serial"))
            fan_point.field("speed", fan.get("speed"))
            fan_point.field("speed_target", fan.get("speed_target"))
            fan_point.field("speed_tolerance", fan.get("speed_tolerance"))
            fan_point.field("status", fan.get("status"))
            write_to_influx(point=point2)
        #logger.info("Fan info successfully sent to InfluxDB.")
    except Exception as e:
        logger.error(f"Error processing FAN metrics: {e}")
    
    try:
        point3 = create_point("TEMPERATURE_INFO")
        device_point = point3.tag("device_ip", device_ip)
        for temp in platform_data.get("TEMPERATURE_INFO", []):
            temp_point = device_point.tag("TEMP", temp.get("index", ""))  
            temp_point.field("index", temp.get("index"))
            temp_point.field("critical_high_threshold", temp.get("critical_high_threshold"))
            temp_point.field("critical_low_threshold", temp.get("critical_low_threshold"))
            temp_point.field("high_threshold", temp.get("high_threshold"))
            temp_point.field("is_replaceable", temp.get("is_replaceable"))
            temp_point.field("low_threshold", temp.get("low_threshold"))
            temp_point.field("maximum_temperature", temp.get("maximum_temperature"))
            temp_point.field("minimum_temperature", temp.get("minimum_temperature"))
            temp_point.field("name", temp.get("name"))
            temp_point.field("temperature", temp.get("temperature"))
            write_to_influx(point=point3)
        #logger.info("Temp info successfully sent to InfluxDB.")
    except Exception as e:
        logger.error(f"Error processing TEMP metrics: {e}")


