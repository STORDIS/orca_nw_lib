import logging
from prometheus_client import CollectorRegistry, Info
from orca_nw_lib.promdb_utils import write_to_prometheus

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

registry = CollectorRegistry()
info_mclag_details = Info(
        'mclag_info', 
        'MCLAG data for devices', 
        labelnames=["device_ip"], 
        registry=registry
    )
def insert_mclag_info_in_prometheus(device_ip: str, mclag_to_intfc_list: dict):
    """
    Inserts MCLAG information into Prometheus for a given device.

    This function processes MCLAG data for a device, extracts relevant details,
    and sends them to Prometheus. It uses the Prometheus `Info` metric to label
    and store various attributes of MCLAG, and pushes these metrics to the
    Prometheus Pushgateway.

    Args:
        device_ip (str): The IP address of the device.
        mclag_to_intfc_list (dict): A dictionary mapping MCLAG objects to their
                                    associated list of interface names.

    Raises:
        None, but logs an error if there is an exception during metric processing
        or when sending metrics to Prometheus.
    """
    try:
        for mclag, interfaces in mclag_to_intfc_list.items():
            #print("mclag", mclag)
            #logger.info("Processing MCLAG object: %s with interfaces: %s", mclag, interfaces)
            # Ensure that no value is None, replace with "None" or another default value
            info_mclag_details.labels(device_ip=device_ip).info({
                "domain_id": str(getattr(mclag, "domain_id", "N/A")),
                "keepalive_interval": str(getattr(mclag, "keepalive_interval", "N/A")),
                "mclag_sys_mac": str(getattr(mclag, "mclag_sys_mac", "N/A")),
                "peer_addr": str(getattr(mclag, "peer_addr", "None")),
                "peer_link": str(getattr(mclag, "peer_link", "None")),
                "session_timeout": str(getattr(mclag, "session_timeout", "N/A")),
                "source_address": str(getattr(mclag, "source_address", "None")),  
                "oper_status": str(getattr(mclag, "oper_status", "N/A")),
                "role": str(getattr(mclag, "role", "N/A")),
                "system_mac": str(getattr(mclag, "system_mac", "None")),
                "delay_restore": str(getattr(mclag, "delay_restore", "N/A")),
                "session_vrf": str(getattr(mclag, "session_vrf", "N/A")),
                "fast_convergence": str(getattr(mclag, "fast_convergence", "N/A")),
                "interfaces": ", ".join(interfaces) if interfaces else "N/A",
            })

        # Push metrics to Prometheus Pushgateway
        write_to_prometheus(registry=registry)
        #logger.info("Metrics pushed to Prometheus Pushgateway successfully for IP: %s", device_ip)

    except Exception as e:
        logger.error("Error sending metrics to Prometheus Pushgateway for IP %s: %s", device_ip, e)
