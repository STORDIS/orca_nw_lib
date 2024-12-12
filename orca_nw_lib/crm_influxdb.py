import datetime

from orca_nw_lib.influxdb_utils import create_point, write_to_influx
from .gnmi_pb2 import SubscribeResponse
from .gnmi_util import get_logging


_logger = get_logging().getLogger(__name__)


def handle_crm_stats_influxdb(device_ip: str, resp: SubscribeResponse):
    """
    Sends the subscription crm statistics received from a device to the InfluxDB.
    
    Args:
        device_ip (str): The IP address of the device
        resp (SubscribeResponse): The subscription response containing metrics

    Returns: 
        None
    """

    crm_metric = ""
    point = create_point("crm_stats")
    device_pnt = point.tag("device_ip", device_ip)
    for ele in resp.update.prefix.elem:
        if ele.name == "statistics":
           crm_metric = "statistics"
           break

    if not crm_metric:
        _logger.debug("CRM Statistics not found in gNMI subscription response from %s",device_ip,)
        return
    
    if crm_metric == 'statistics':
        for u in resp.update.update:
            for ele in u.path.elem:
                device_pnt.field(ele.name, int(u.val.uint_val))

    point.time(datetime.datetime.now(datetime.timezone.utc))
    write_to_influx(point=point)




# GET function that inserts the crm acl stats into inflixdb
def insert_crm_acl_stats_in_influxdb(device_ip: str, crm_data: dict):
    """
    Retrieves crm acl statistics and inserts into influx DB.
    
    Args:
        device_ip (str): Device ip of the system.
        crm_data (dict): Dictionary pf key value pairs.
    """

    if not device_ip:
        _logger.error("Device ip is required.")
        return
    
    if not crm_data:
        _logger.error("CRM ACL Stats dictionary is required.")
        return
    
    
    try:
        point = create_point("crm_acl_stats") 
        device_ip_pnt = point.tag("device_ip", device_ip)

        device_ip_pnt.field("ingress_switch_group_used", int(crm_data.get("ingress_switch_group_used")))
        device_ip_pnt.field("ingress_switch_group_available", int(crm_data.get("ingress_switch_group_available")))
        device_ip_pnt.field("ingress_switch_tables_used", int(crm_data.get("ingress_switch_tables_used")))
        device_ip_pnt.field("ingress_switch_tables_available", int(crm_data.get("ingress_switch_tables_available")))
        device_ip_pnt.field("ingress_vlan_group_used", int(crm_data.get("ingress_vlan_group_used")))
        device_ip_pnt.field("ingress_vlan_group_available", int(crm_data.get("ingress_vlan_group_available")))
        device_ip_pnt.field("ingress_vlan_tables_used", int(crm_data.get("ingress_vlan_tables_used")))
        device_ip_pnt.field("ingress_vlan_tables_available", int(crm_data.get("ingress_vlan_tables_available")))
        device_ip_pnt.field("ingress_port_group_used", int(crm_data.get("ingress_port_group_used")))
        device_ip_pnt.field("ingress_port_group_available", int(crm_data.get("ingress_port_group_available")))
        device_ip_pnt.field("ingress_port_tables_used", int(crm_data.get("ingress_port_tables_used")))
        device_ip_pnt.field("ingress_port_tables_available", int(crm_data.get("ingress_port_tables_available")))
        device_ip_pnt.field("ingress_rif_group_used", int(crm_data.get("ingress_rif_group_used")))
        device_ip_pnt.field("ingress_rif_group_available", int(crm_data.get("ingress_rif_group_available")))
        device_ip_pnt.field("ingress_rif_tables_used", int(crm_data.get("ingress_rif_tables_used")))
        device_ip_pnt.field("ingress_rif_tables_available", int(crm_data.get("ingress_rif_tables_available")))
        device_ip_pnt.field("ingress_lag_group_used", int(crm_data.get("ingress_lag_group_used")))
        device_ip_pnt.field("ingress_lag_group_available", int(crm_data.get("ingress_lag_group_available")))
        device_ip_pnt.field("ingress_lag_tables_used", int(crm_data.get("ingress_lag_tables_used")))
        device_ip_pnt.field("ingress_lag_tables_available", int(crm_data.get("ingress_lag_tables_available")))

        device_ip_pnt.field("egress_switch_group_used", int(crm_data.get("egress_switch_group_used")))
        device_ip_pnt.field("egress_switch_group_available", int(crm_data.get("egress_switch_group_available")))
        device_ip_pnt.field("egress_switch_tables_used", int(crm_data.get("egress_switch_tables_used")))
        device_ip_pnt.field("egress_switch_tables_available", int(crm_data.get("egress_switch_tables_available")))
        device_ip_pnt.field("egress_vlan_group_used", int(crm_data.get("egress_vlan_group_used")))
        device_ip_pnt.field("egress_vlan_group_available", int(crm_data.get("egress_vlan_group_available")))
        device_ip_pnt.field("egress_vlan_tables_used", int(crm_data.get("egress_vlan_tables_used")))
        device_ip_pnt.field("egress_vlan_tables_available", int(crm_data.get("egress_vlan_tables_available")))
        device_ip_pnt.field("egress_port_group_used", int(crm_data.get("egress_port_group_used")))
        device_ip_pnt.field("egress_port_group_available", int(crm_data.get("egress_port_group_available")))
        device_ip_pnt.field("egress_port_tables_used", int(crm_data.get("egress_port_tables_used")))
        device_ip_pnt.field("egress_port_tables_available", int(crm_data.get("egress_port_tables_available")))
        device_ip_pnt.field("egress_rif_group_used", int(crm_data.get("egress_rif_group_used")))
        device_ip_pnt.field("egress_rif_group_available", int(crm_data.get("egress_rif_group_available")))
        device_ip_pnt.field("egress_rif_tables_used",int( crm_data.get("egress_rif_tables_used")))
        device_ip_pnt.field("egress_rif_tables_available",int(crm_data.get("egress_rif_tables_available")))
        device_ip_pnt.field("egress_lag_group_used", int(crm_data.get("egress_lag_group_used")))
        device_ip_pnt.field("egress_lag_group_available", int(crm_data.get("egress_lag_group_available")))
        device_ip_pnt.field("egress_lag_tables_used",int( crm_data.get("egress_lag_tables_used")))
        device_ip_pnt.field("egress_lag_tables_available",int(crm_data.get("egress_lag_tables_available")))
        
            
        write_to_influx(point=point)
    except Exception as e:
        _logger.error(f"Error instering in influxdb: {e}")