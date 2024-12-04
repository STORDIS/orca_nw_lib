
from prometheus_client import CollectorRegistry, Gauge, Info

from orca_nw_lib.promdb_utils import write_to_prometheus
from .gnmi_pb2 import SubscribeResponse
from .gnmi_util import get_logging

_logger = get_logging().getLogger(__name__)

crm_registry = CollectorRegistry()

crm_stats = Info('crm_stats', 'CRM Statistics from subscription', labelnames=["device_ip"], registry=crm_registry)


def handle_crm_stats_promdb(device_ip: str, resp: SubscribeResponse):
    """
    Sends the subscription crm statistics received from a device to the Prometheus.
    
    Args:
        device_ip (str): The IP address of the device
        resp (SubscribeResponse): The subscription response containing metrics

    Returns: 
        None
    """
    crm_metric = ""
    crm_dict = {}

    for ele in resp.update.prefix.elem:
        if ele.name == "statistics":
           crm_metric = "statistics"
           break

    if not crm_metric:
        _logger.debug("CRM Statistics not found in gNMI subscription response from %s",device_ip,)
        return

    for u in resp.update.update:
        for ele in u.path.elem:
            if ele.name == "dnat-entries-used":
                crm_dict["dnat_entries_used"] = str(u.val.uint_val)
            if ele.name == "fdb-entries-used":
                crm_dict["fdb_entries_used"] = str(u.val.uint_val)
            if ele.name == "ipv4-neighbors-used":
                crm_dict["ipv4_neighbors_used"] = str(u.val.uint_val)
            if ele.name == "ipv4-nexthops-used":
                crm_dict["ipv4_nexthops_used"] = str(u.val.uint_val)
            if ele.name == "ipv4-routes-used":
                crm_dict["ipv4_routes_used"] = str(u.val.uint_val)
            if ele.name == "ipv6-neighbors-used":
                crm_dict["ipv6_neighbors_used"] = str(u.val.uint_val)
            if ele.name == "ipv6-nexthops-used":
                crm_dict["ipv6_nexthops_used"] = str(u.val.uint_val)
            if ele.name == "ipv6-routes-used":
                crm_dict["ipv6_routes_used"] = str(u.val.uint_val)
            if ele.name == "nexthop-group-members-used":
                crm_dict["nexthop_group_members_used"] = str(u.val.uint_val)
            if ele.name == "nexthop-groups-used":
                crm_dict["nexthop_groups_used"] = str(u.val.uint_val)
            if ele.name == "snat-entries-used":
                crm_dict["snat_entries_used"] = str(u.val.uint_val)

    crm_stats.labels(device_ip=device_ip).info(crm_dict)
    write_to_prometheus(registry=crm_registry)
    




system_info = Info('crm_acl_stats', 'CRM ACL Statistics from GET', labelnames=["device_ip"], registry=crm_registry)

# GET function that inserts the crm acl stats into inflixdb
def insert_crm_acl_stats_in_prometheus(device_ip: str, crm_data: dict):
    """
    Retrieves system uptime data and NTP inserts into prometheus pushgateway.
    
    Args:
        device_ip (str): Object of type Device.
        crm_data (dict): Dictionary pf key value pairs.
    """
    if not device_ip:
        _logger.error("Device ip is required.")
        return
    
    if not crm_data:
        _logger.error("CRM dictionary is required.")
        return

    try:
        system_info.labels(device_ip=device_ip).info({
            "ingress_switch_group_used": str(crm_data.get('ingress_switch_group_used')),
            "ingress_switch_tables_used": str(crm_data.get('ingress_switch_tables_used')),
            "ingress_vlan_group_used": str(crm_data.get('ingress_vlan_group_used')),
            "ingress_vlan_tables_used": str(crm_data.get('ingress_vlan_tables_used')),
            "ingress_port_group_used": str(crm_data.get('ingress_port_group_used')),
            "ingress_port_tables_used": str(crm_data.get('ingress_port_tables_used')),
            "ingress_rif_group_used": str(crm_data.get('ingress_rif_group_used')),
            "ingress_rif_tables_used": str(crm_data.get('ingress_rif_tables_used')),
            "ingress_lag_group_used": str(crm_data.get('ingress_lag_group_used')),
            "ingress_lag_tables_used": str(crm_data.get('ingress_lag_tables_used')),
            "egress_switch_group_used": str(crm_data.get('egress_switch_group_used')),
            "egress_switch_tables_used": str(crm_data.get('egress_switch_tables_used')),
            "egress_vlan_group_used": str(crm_data.get('egress_vlan_group_used')),
            "egress_vlan_tables_used": str(crm_data.get('egress_vlan_tables_used')),
            "egress_port_group_used": str(crm_data.get('egress_port_group_used')),
            "egress_port_tables_used": str(crm_data.get('egress_port_tables_used')),
            "egress_rif_group_used": str(crm_data.get('egress_rif_group_used')),
            "egress_rif_tables_used": str(crm_data.get('egress_rif_tables_used')),
            "egress_lag_group_used": str(crm_data.get('egress_lag_group_used')),
            "egress_lag_tables_used": str(crm_data.get('egress_lag_tables_used'))
        })

        write_to_prometheus(registry=crm_registry)
    except Exception as e:
        _logger.error(f"Error instering in influxdb: {e}")