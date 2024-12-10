import logging
from orca_nw_lib.graph_db_models import Device
from orca_nw_lib.influxdb_utils import create_point, write_to_influx

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def insert_mclag_info_in_influxdb(device_ip: str, mclag_to_intfc_list: dict):
    """
    Inserts MCLAG information into InfluxDB for a given device.

    Args:
        device_ip (str): The IP address of the device.
        mclag_to_intfc_list (dict): A dictionary mapping MCLAG objects to their
                                    associated list of interface names.

    Raises:
        None, but logs an error if there is an exception during metric processing
        or when sending metrics to InfluxDB.
    """
    try:
        if not mclag_to_intfc_list:
            #logger.warning(f"No MCLAG data available for device IP: {device_ip}")
            return  # Exit early if there’s no data

        # Iterate over each MCLAG and associated interfaces
        for mclag_obj, interfaces in mclag_to_intfc_list.items():
            if not mclag_obj:
                #logger.warning(f"Skipping invalid MCLAG object for device IP: {device_ip}")
                continue  # Skip invalid MCLAG objects

            #logger.debug(f"Processing MCLAG object for IP: {device_ip} with interfaces: {interfaces}")

            # Create a point for InfluxDB
            point = create_point("discovered_mclag")
            mclag_point = point.tag("device_ip", device_ip)

            # Safely extract attributes from MCLAG object, using "N/A" as the default if they are not available
            mclag_point.field("domain-id", getattr(mclag_obj, "domain_id"))
            mclag_point.field("keepalive_interval", getattr(mclag_obj, "keepalive_interval"))
            mclag_point.field("mclag_sys_mac", getattr(mclag_obj, "mclag_sys_mac"))
            mclag_point.field("peer_addr", getattr(mclag_obj, "peer_addr"))
            mclag_point.field("peer_link", getattr(mclag_obj, "peer_link"))
            mclag_point.field("session_timeout", getattr(mclag_obj, "session_timeout"))
            mclag_point.field("source_address", getattr(mclag_obj, "source_address"))
            mclag_point.field("oper_status", getattr(mclag_obj, "oper_status"))
            mclag_point.field("role", getattr(mclag_obj, "role"))
            mclag_point.field("system_mac", getattr(mclag_obj, "system_mac"))
            mclag_point.field("delay_restore", getattr(mclag_obj, "delay_restore"))
            mclag_point.field("session_vrf", getattr(mclag_obj, "session_vrf"))
            mclag_point.field("fast_convergence", getattr(mclag_obj, "fast_convergence"))

            # Log the point data being written
            #logger.debug(f"Point to write: {point}")

            # Write the point to InfluxDB
            write_to_influx(point=point)

        #logger.info(f"Metrics pushed to InfluxDB successfully for device IP: {device_ip}")
    
    except Exception as e:
        logger.error(f"Error inserting MCLAG data into InfluxDB for device IP {device_ip}: {e}", exc_info=True)
