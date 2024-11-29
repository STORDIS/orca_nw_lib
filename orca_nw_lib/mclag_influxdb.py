import logging
from orca_nw_lib.graph_db_models import Device
from orca_nw_lib.influxdb_utils import create_point, write_to_influx

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def insert_mclag_info_in_influxdb(device: Device, mclag_to_intfc_list):
    """
    Retrieves discovered port chanel data and inserts into influx DB.
   
    Args:
        device (Device): Object to type Device.
        mclag_to_intfc_list (dict): Dictionary of key value pairs.
    """
    try:
        point = create_point("discovered_mclag")
        for mclag in mclag_to_intfc_list.items() or []:
            point_tag = point.tag("domain_id", mclag.domain_id)    
            point_tag.field("domain_id", mclag.domain_id)
            point_tag.field("keepalive_interval", mclag.keepalive_interval)
            point_tag.field("mclag_sys_mac", mclag.mclag_sys_mac)
            point_tag.field("peer_addr", mclag.peer_addr)
            point_tag.field("peer_link", mclag.peer_link)
            point_tag.field("session_timeout", mclag.session_timeout)
            point_tag.field("source_address", mclag.source_address)
            point_tag.field("oper_status", mclag.oper_status)
            point_tag.field("role", mclag.role)
            point_tag.field("system_mac", mclag.system_mac)
            point_tag.field("delay_restore", mclag.delay_restore)
            point_tag.field("session_vrf", mclag.session_vrf)
            point_tag.field("fast_convergence", mclag.fast_convergence)
           
            write_to_influx(point=point)
            logger.info("Metrics pushed to InfluxDB successfully.")
    except Exception as e:
        logger.error(f"Error instering in influxdb: {e}")