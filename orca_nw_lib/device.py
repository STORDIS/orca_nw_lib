from typing import List, Optional, Union
from orca_nw_lib.device_db import get_device_db_obj, insert_devices_in_db
from orca_nw_lib.device_gnmi import (get_device_details_from_device,
                                     get_device_status_from_device)
from orca_nw_lib.graph_db_models import Device
from orca_nw_lib.utils import get_logging

from orca_nw_lib.device_gnmi import get_image_list_from_device

_logger=logger = get_logging().getLogger(__name__)


def _create_device_graph_object(ip_addr: str) -> Device | None:
    """
    Create a Device object based on the given IP address.

    Args:
        ip_addr (str): The IP address of the device.

    Returns:
        Device: The Device object created with the device details.

    """
    device_detail = get_device_details_from_device(ip_addr)
    device_status = get_device_status_from_device(ip_addr).get("openconfig-events:events", {})
    device_status_event = device_status.get("event", [])
    system_status = None
    images_list_details = get_image_list_from_device(device_ip=ip_addr).get(
        "sonic-image-management:IMAGE_TABLE_LIST", []
    )
    images_list = []
    for i in images_list_details:
        images_list.append(i.get("image"))
    for event in reversed(device_status_event):
        state = event.get("state", {})
        if state.get("resource") == "system_status":
            system_status = state.get("text")
            break
    return Device(
        img_name=device_detail.get("img_name"),
        mgt_intf=device_detail.get("mgt_intf"),
        mgt_ip=mgt_ip.split("/")[0].strip() if (mgt_ip:=device_detail.get("mgt_ip")) else None,
        hwsku=device_detail.get("hwsku"),
        mac=device_detail.get("mac"),
        platform=device_detail.get("platform"),
        type=device_detail.get("type"),
        system_status=system_status,
        image_list=images_list
    ) if device_detail else None


def get_device_details(mgt_ip: Optional[str] = None) -> Union[dict, List[dict]]:
    """
    Retrieves the details of a device based on its management IP address.
    If no management IP address is provided, it returns a list of dictionaries containing the details of all devices.

    .. code-block:: python

        get_device_details(mgt_ip="10.10.10.10")
        get_device_details()
        
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


def discover_device(device_ip:str):
    """
    Discover a device by its IP address and insert the device details into the database.

    Args:
        device_ip (str): The IP address of the device to be discovered.

    Raises:
        Exception: If an error occurs during the discovery process.
    """
    _logger.debug("Discovering device with IP: %s", device_ip)
    try:
        _logger.info("Discovering device with IP: %s", device_ip)
        insert_devices_in_db(_create_device_graph_object(device_ip))
    except Exception as e:
        _logger.error("Error discovering device with IP %s: %s", device_ip, str(e))
        raise
