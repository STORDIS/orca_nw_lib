from typing import List
from .gnmi_pb2 import Path, PathElem, Subscription, SubscriptionMode
from .gnmi_util import get_gnmi_path, send_gnmi_get


def get_system_base_path() -> Path:
    """
    Returns the base path for system configuration in OpenConfig.

    Returns:
        Path: Base path for system configuration
    """
    return Path(
        target="openconfig",
        # origin="openconfig-system",
        elem=[
            PathElem(name="openconfig-system:system")
        ]
    )


# CRM Statistics Path
def get_crm_stats_path():
    return get_gnmi_path("openconfig-system:system/openconfig-system-crm:crm/statistics/state")

# CRM ACL Statistics Path
def get_crm_acl_stats_path():
    return get_gnmi_path("openconfig-system:system/openconfig-system-crm:crm/acl-statistics")



def get_system_info_from_device(device_ip: str):
    uptime_path = get_gnmi_path("openconfig-system:system/openconfig-system-ext:infra/state")
    ntp_path = get_gnmi_path(f"openconfig-system:system/ntp/servers/server")
    return send_gnmi_get(
        path=[uptime_path, ntp_path],
        device_ip=device_ip,
    )


def get_crm_stats_from_device(device_ip: str):
    # crm_acl_stats = get_gnmi_path("openconfig-system:system/openconfig-system-crm:crm/acl-statistics")
    crm_acl_stats = get_crm_acl_stats_path()
    return send_gnmi_get(
        path=[crm_acl_stats],
        device_ip=device_ip,
    )



def get_subscription_path_for_system() -> List[Subscription]:
    """
    Creates subscription paths for system monitoring        
    Returns:
        List[Subscription]: List of subscriptions for system paths
    """
    subscriptions = []

    # DNS Path /openconfig-system:system/dns/servers/server
    dns_path = get_gnmi_path("openconfig-system:system/dns/servers/server")
    subscriptions.append(
        Subscription(
            path=dns_path,
            mode=SubscriptionMode.TARGET_DEFINED
        )
    )

    # Events Path /openconfig-system:system/openconfig-events:events/event
    events_path = get_gnmi_path("openconfig-system:system/openconfig-events:events/event")
    subscriptions.append(
        Subscription(
            path=events_path,
            mode=SubscriptionMode.TARGET_DEFINED
        )
    )

    # Memory State Path /openconfig-system:system/memory/state
    memory_path = get_gnmi_path("/openconfig-system:system/memory/state")
    subscriptions.append(
        Subscription(
            path=memory_path,
            mode=SubscriptionMode.TARGET_DEFINED
        )
    )
    return subscriptions






def get_subscription_path_for_crm_stats() -> List[Subscription]:
    """
    Creates subscription paths for crm statistics        
    Returns:
        List[Subscription]: List of subscriptions for system paths
    """
    subscriptions = []

    crm_stats = get_crm_stats_path()
    subscriptions.append(
        Subscription(
            path=crm_stats,
            mode=SubscriptionMode.TARGET_DEFINED
        )
    )
    return subscriptions


