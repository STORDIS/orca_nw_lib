from typing import List
from .gnmi_pb2 import Subscription, SubscriptionMode
from .gnmi_util import get_gnmi_path, send_gnmi_get


# Digital Optical Monitoring (DOM) Path
def get_dom_path():
    return get_gnmi_path("openconfig-platform:components/component")


def get_subscription_path_for_dom() -> List[Subscription]:
    """
    Creates subscription paths for DOM   
    Returns:
        List[Subscription]: List of subscriptions for system paths
    """
    subscriptions = []

    dom_path = get_dom_path()
    subscriptions.append(
        Subscription(
            path=dom_path,
            mode=SubscriptionMode.TARGET_DEFINED
        )
    )
    return subscriptions


