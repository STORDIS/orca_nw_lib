from typing import List, Optional, Union
from orca_nw_lib.device_db import get_device_db_obj
from orca_nw_lib.device_gnmi import get_device_details_from_device
from orca_nw_lib.graph_db_models import Device


def create_device_graph_object(ip_addr: str) -> Device:
    """
    Create a Device object based on the given IP address.

    Args:
        ip_addr (str): The IP address of the device.

    Returns:
        Device: The Device object created with the device details.

    """
    device_detail = get_device_details_from_device(ip_addr)
    return Device(
        img_name=device_detail.get("img_name"),
        mgt_intf=device_detail.get("mgt_intf"),
        mgt_ip=mgt_ip.split("/")[0].strip() if (mgt_ip:=device_detail.get("mgt_ip")) else None,
        hwsku=device_detail.get("hwsku"),
        mac=device_detail.get("mac"),
        platform=device_detail.get("platform"),
        type=device_detail.get("type"),
    ) if device_detail else None


def get_device_details(mgt_ip: Optional[str] = None) -> Union[dict, List[dict]]:
    """
    Retrieves the details of a device based on its management IP address.

    Args:
        mgt_ip (Optional[str]): The management IP address of the device. Defaults to None.

    Returns:
        Union[dict, List[dict]]: If a management IP address is provided,
        the function returns a dictionary object containing the properties of the device.
        If no management IP address is provided,
        the function returns a list of dictionaries,
        each containing the properties of a device. If no device is found,
        an empty list is returned.
    """
    if mgt_ip:
        device = get_device_db_obj(mgt_ip)
        if device:
            return device.__properties__
    else:
        op_dict: List[dict] = []
        device_dict = get_device_db_obj()
        for device in device_dict or []:
            op_dict.append(device.__properties__)
        return op_dict
