from typing import List, Optional
from orca_nw_lib.device_db import get_device_db_obj
from orca_nw_lib.device_gnmi import get_device_details
from orca_nw_lib.graph_db_models import Device


def create_device_graph_object(ip_addr: str) -> Device:
    """
    Create a Device object based on the given IP address.

    Args:
        ip_addr (str): The IP address of the device.

    Returns:
        Device: The Device object created with the device details.

    """
    device_detail = get_device_details(ip_addr)
    return Device(
        img_name=device_detail.get("img_name"),
        mgt_intf=device_detail.get("mgt_intf"),
        mgt_ip=device_detail.get("mgt_ip").split("/")[0],
        hwsku=device_detail.get("hwsku"),
        mac=device_detail.get("mac"),
        platform=device_detail.get("platform"),
        type=device_detail.get("type"),
    )


def get_device_details(mgt_ip: Optional[str] = None) -> List[dict]:
    """
    Get the device details from the database.

    Parameters:
        mgt_ip (Optional[str]): The management IP address of the device. Defaults to None.

    Returns:
        List[dict]: A list of dictionaries containing the device details.
    """
    op_dict: List[dict] = []

    if mgt_ip:
        device = get_device_db_obj(mgt_ip)
        if device:
            op_dict.append(device.__properties__)
    else:
        device_dict = get_device_db_obj()
        for device in device_dict or []:
            op_dict.append(device.__properties__)

    return op_dict










