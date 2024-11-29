import json
import logging

from prometheus_client import CollectorRegistry, Info

from orca_nw_lib.promdb_utils import write_to_prometheus

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

registry = CollectorRegistry()

def insert_mclag_info_in_prometheus(device_ip:str, mclag_to_intfc_list):
    """
    Converts the MCLAG object into Prometheus metrics and pushes them to the Pushgateway.
    
    Args:
        device_ip (str): The IP address of the device.
        mclag_to_intfc_list (dict): A dictionary mapping MCLAG objects to a list of interface names.
    
    Returns:
        None
    
    Raises:
        None
    """
    info_mclag_details = Info('mclag_domain_info', 'MCLAG domain information', labelnames=["device_ip"], registry=registry)
 
    try:
         # Debugging the keys in the dictionary
        logger.debug(f"mclag_to_intfc_list: {mclag_to_intfc_list}")
        logger.debug(f"Available keys in mclag_to_intfc_list: {list(mclag_to_intfc_list.keys())}")
        
        info_mclag_details.labels(device_ip=device_ip).info({
            "domain_id": str(mclag_to_intfc_list.get("domain_id", "")),
            "keepalive_interval": mclag_to_intfc_list.get("keepalive_interval", ""),
            "mclag_sys_mac": mclag_to_intfc_list.get("mclag_sys_mac", ""),
            "peer_addr": mclag_to_intfc_list.get("peer_addr", ""),
            "peer_link": mclag_to_intfc_list.get("peer_link", ""),
            "session_timeout": mclag_to_intfc_list.get("session_timeout", ""),
            "source_address": mclag_to_intfc_list.get("source_address", ""),
            "oper_status": mclag_to_intfc_list.get("oper_status", ""),
            "role": mclag_to_intfc_list.get("role", ""),
            "system_mac": mclag_to_intfc_list.get("system_mac", ""),
            "delay_restore": mclag_to_intfc_list.get("delay_restore", ""),
            "session_vrf": mclag_to_intfc_list.get("session_vrf", ""),
            "fast_convergence": mclag_to_intfc_list.get("fast_convergence", "")
        })

        # Push to Prometheus Pushgateway
        write_to_prometheus(registry=registry)
        print(f"Metrics pushed to Pushgateway successfully.")

    except Exception as e:
        logger.error(f"Error sending metrics to Pushgateway: {e}")