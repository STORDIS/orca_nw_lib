from orca_nw_lib.platform_gnmi import get_platform_info_from_device
from orca_nw_lib.platform_influxdb import insert_platform_info_in_influxdb
#from orca_nw_lib.platform_promdb import insert_platform_info_in_prometheus
from orca_nw_lib.utils import get_logging, get_telemetry_db
from .device_db import get_device_db_obj

_logger = get_logging().getLogger(__name__)

def get_platform_details(ip_addr: str) -> dict:
    """
    Retrieves platform information from a device and parses it into a structured
    dictionary containing PSU_INFO, FAN_INFO, and TEMPERATURE_INFO.

    Args:
        ip_addr (str): The IP address of the device from which to retrieve the
            platform information.

    Returns:
        dict: A dictionary containing the platform information, with the following
            structure:

            {
                "PSU_INFO": [
                    {
                        "index": int,
                        "input_current": float,
                        "input_power": float,
                        "input_voltage": float,
                        "is_replaceable": bool,
                        "led_status": str,
                        "mfr_id": str,
                        "model": str,
                        "name": str,
                        "num_fans": int,
                        "output_current": float,
                        "output_power": float,
                        "output_voltage": float,
                        "presence": bool,
                        "serial": str,
                        "status": str,
                        "type": str,
                    }
                ],
                "FAN_INFO": [
                    {
                        "index": int,
                        "direction": str,
                        "drawer_name": str,
                        "is_replaceable": bool,
                        "led_status": str,
                        "model": str,
                        "name": str,
                        "presence": bool,
                        "serial": str,
                        "speed": float,
                        "speed_target": float,
                        "speed_tolerance": float,
                        "status": str,
                    }
                ],
                "TEMPERATURE_INFO": [
                    {
                        "index": int,
                        "critical_high_threshold": float,
                        "critical_low_threshold": float,
                        "high_threshold": float,
                        "is_replaceable": bool,
                        "low_threshold": float,
                        "maximum_temperature": float,
                        "minimum_temperature": float,
                        "name": str,
                        "temperature": float,
                    }
                ],
            }
    """
    pt_data = get_platform_info_from_device(ip_addr)
    platform_details = {}

    # Parse PSU_INFO
    psu_info = pt_data.get("sonic-platform:sonic-platform", {}).get("PSU_INFO", {}).get("PSU_INFO_LIST", [])
    platform_details["PSU_INFO"] = [
        {
            "index": psu.get("index"),
            "input_current": psu.get("input_current"),
            "input_power": psu.get("input_power"),
            "input_voltage": psu.get("input_voltage"),
            "is_replaceable": psu.get("is_replaceable"),
            "led_status": psu.get("led_status"),
            "mfr_id": psu.get("mfr_id"),
            "model": psu.get("model"),
            "name": psu.get("name"),
            "num_fans": psu.get("num_fans"),
            "output_current": psu.get("output_current"),
            "output_power": psu.get("output_power"),
            "output_voltage": psu.get("output_voltage"),
            "presence": psu.get("presence"),
            "serial": psu.get("serial"),
            "status": psu.get("status"),
            "type": psu.get("type"),
        }
        for psu in psu_info
    ]

    # Parse FAN_INFO
    fan_info = pt_data.get("sonic-platform:sonic-platform", {}).get("FAN_INFO", {}).get("FAN_INFO_LIST", [])
    platform_details["FAN_INFO"] = [
        {
            "index": fan.get("index"),
            "direction": fan.get("direction"),
            "drawer_name": fan.get("drawer_name"),
            "is_replaceable": fan.get("is_replaceable"),
            "led_status": fan.get("led_status"),
            "model": fan.get("model"),
            "name": fan.get("name"),
            "presence": fan.get("presence"),
            "serial": fan.get("serial"),
            "speed": fan.get("speed"),
            "speed_target": fan.get("speed_target"),
            "speed_tolerance": fan.get("speed_tolerance"),
            "status": fan.get("status"),
        }
        for fan in fan_info
    ]

    # Parse TEMPERATURE_INFO
    temperature_info = pt_data.get("sonic-platform:sonic-platform", {}).get("TEMPERATURE_INFO", {}).get("TEMPERATURE_INFO_LIST", [])
    platform_details["TEMPERATURE_INFO"] = [
        {
            "index": temp.get("index"),
            "critical_high_threshold": temp.get("critical_high_threshold"),
            "critical_low_threshold": temp.get("critical_low_threshold"),
            "high_threshold": temp.get("high_threshold"),
            "is_replaceable": temp.get("is_replaceable"),
            "low_threshold": temp.get("low_threshold"),
            "maximum_temperature": temp.get("maximum_temperature"),
            "minimum_temperature": temp.get("minimum_temperature"),
            "name": temp.get("name"),
            "temperature": temp.get("temperature"),
        }
        for temp in temperature_info
    ]
    return platform_details



def discover_platform(device_ip: str = None):
    """
    Discovers the platform details of a device or all devices.

    Args:
        device_ip (str): The IP address of the device to discover platform details for.
            If None, platform details for all devices will be discovered. Default is None.

    Returns:
        None

    """
    _logger.info("Platform Discovery Started.")
    devices = [get_device_db_obj(device_ip)] if device_ip else get_device_db_obj()
    for device in devices:
        try:
            _logger.info(f"Discovering platform on device {device}.")
            platform_data = get_platform_details(device_ip)
            #print("Platform Data: ", platform_data)
            ## Check if the telemetry DB is influxdb or prometheus for inserting device info.
            if platform_data and get_telemetry_db() == "influxdb":
                insert_platform_info_in_influxdb(device_ip, platform_data)
            elif platform_data and get_telemetry_db() == "prometheus":
                #insert_platform_info_in_prometheus(device_ip, platform_data)
                pass
            else:
                _logger.info("Empty platform data received")
        except Exception as e:
            _logger.error(f"MCLAG Discovery Failed on device {device_ip}, Reason: {e}")
            raise