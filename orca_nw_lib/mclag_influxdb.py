import logging
from orca_nw_lib.graph_db_models import Device
from orca_nw_lib.influxdb_utils import create_point, write_to_influx

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def insert_mclag_info_in_influxdb(device_ip: str, mclag_to_intfc_list: dict):
    try:
        print("mclag_to_intfc_list", mclag_to_intfc_list.keys())
        for mclag_obj, interfaces in mclag_to_intfc_list.items() or []:
            print("mclag_obj", mclag_obj)
            point = create_point("discovered_mclag")
            mclag_point = point.tag("device_ip", device_ip)
            mclag_point.field("domain-id", mclag_obj.domain_id)
            mclag_point.field("keepalive_interval", mclag_obj.keepalive_interval)
            mclag_point.field("mclag_sys_mac", mclag_obj.mclag_sys_mac)
            mclag_point.field("peer_addr", mclag_obj.peer_addr)
            mclag_point.field("peer_link", mclag_obj.peer_link)
            mclag_point.field("session_timeout", mclag_obj.session_timeout)
            mclag_point.field("source_address", mclag_obj.source_address)
            mclag_point.field("oper_status", mclag_obj.oper_status)
            mclag_point.field("role", mclag_obj.role)
            mclag_point.field("system_mac", mclag_obj.system_mac)
            mclag_point.field("delay_restore", mclag_obj.delay_restore)
            mclag_point.field("session_vrf", mclag_obj.session_vrf)
            mclag_point.field("fast_convergence", mclag_obj.fast_convergence)
            logger.debug(f"Point to write: {point}")
            write_to_influx(point=point)
        logger.info("Metrics pushed to InfluxDB successfully.")
    except Exception as e:
        logger.error(f"Error inserting in InfluxDB: {e}", exc_info=True)