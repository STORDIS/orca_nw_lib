from threading import Thread
from orca_nw_lib.gnmi_sub import gnmi_subscribe
from orca_nw_lib.interface_db import get_all_interfaces_name_of_device_from_db
from orca_nw_lib.interface_gnmi import get_intfc_config_path


def subscribe_for_infc_chngs(device_ip: str):
    thread = Thread(
        target=gnmi_subscribe,
        args=(
            device_ip,
            [
                get_intfc_config_path(intfc_name)
                for intfc_name in get_all_interfaces_name_of_device_from_db(device_ip)
            ],
        ),
    )
