import logging
from prometheus_client import CollectorRegistry, Info

from orca_nw_lib.promdb_utils import write_to_prometheus

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

registry = CollectorRegistry()


sag_info = Info("sag_info", "SAG Information", labelnames=["device_ip"], registry=registry)


def insert_sag_info_in_promdb(device_ip: str, sag_data: dict):
    """
    Inserts the SAG info data into Prometheus DB.

    Args:
        device_ip (str): The IP address of the device.
        sag_data (dict): The SAG info data in dictionary format.

    Raises:
        Exception: If an error occurs while sending data to Pushgateway.
    """
    try:
        sag_info.labels(device_ip=device_ip).info({
                "ifname": str(sag_data.get("ifname")),
                "mode": str(sag_data.get("mode")),
                "oper": str(sag_data.get("oper")),
                "v4GwIp": str(sag_data.get("v4GwIp")),
                "v6GwIp": str(sag_data.get("v6GwIp")),
                "vmac": str(sag_data.get("vmac")),
                "vrf": str(sag_data.get("vrf"))
            })
        # Push to Prometheus Pushgateway
        write_to_prometheus(registry=registry)
        #logger.info("Metrics pushed to Pushgateway successfully for IP: %s", device_ip)
    except Exception as e:
        logger.error(f"Error sending metrics to Pushgateway: {e}")
