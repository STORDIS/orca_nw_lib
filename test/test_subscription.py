from orca_nw_lib.gnmi_sub import gnmi_subscribe_for_all_devices_in_db
from orca_nw_lib.utils import load_orca_config


def simple_subscription_test():
    load_orca_config()
    gnmi_subscribe_for_all_devices_in_db()
    
simple_subscription_test()