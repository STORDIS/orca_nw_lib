from typing import List, Optional
from orca_nw_lib.gnmi_pb2 import Path, PathElem
from orca_nw_lib.gnmi_util import send_gnmi_get
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


def get_device_from_db(mgt_ip: str = None):
    if mgt_ip:
        return Device.nodes.get_or_none(mgt_ip=mgt_ip)
    return Device.nodes.all()


def get_device_details_from_db(mgt_ip: Optional[str] = None) -> List[dict]:
    """
    Get the device details from the database.

    Parameters:
        mgt_ip (Optional[str]): The management IP address of the device. Defaults to None.

    Returns:
        List[dict]: A list of dictionaries containing the device details.
    """
    op_dict: List[dict] = []

    if mgt_ip:
        device = get_device_from_db(mgt_ip)
        if device:
            op_dict.append(device.__properties__)
    else:
        device_dict = get_device_from_db()
        for device in device_dict or []:
            op_dict.append(device.__properties__)

    return op_dict


def get_device_details(device_ip: str):
    """
    Retrieves the details of a device based on its IP address.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        dict: A dictionary containing the following device details:
              - "img_name" (str): The name of the device's image.
              - "mgt_intf" (str): The management interface of the device.
              - "mgt_ip" (str): The IP address of the management interface.
              - "hwsku" (str): The hardware SKU of the device.
              - "mac" (str): The MAC address of the device.
              - "platform" (str): The platform of the device.
              - "type" (str): The type of the device.

    """

    op_dict = {
        "img_name": "",
        "mgt_intf": "",
        "mgt_ip": "",
        "hwsku": "",
        "mac": "",
        "platform": "",
        "type": "",
    }

    op1 = get_device_img_name(device_ip)
    op2 = get_device_mgmt_intfc_info(device_ip)
    op3 = get_device_meta_data(device_ip)

    if op1 is not None and op1:
        op_dict["img_name"] = op1.get("openconfig-image-management:current")
    if op2 is not None and op2:
        mgt_intfc_table_dict = op2.get(
            "sonic-mgmt-interface:sonic-mgmt-interface", {}
        ).get("MGMT_INTF_TABLE", {})
        op_dict["mgt_intf"] = mgt_intfc_table_dict.get("MGMT_INTF_TABLE_IPADDR_LIST")[
            0
        ].get("ifName")
        op_dict["mgt_ip"] = mgt_intfc_table_dict.get("MGMT_INTF_TABLE_IPADDR_LIST")[
            0
        ].get("ipPrefix")
    if op3 is not None and op3:
        metadata_dict = op3.get("sonic-device-metadata:DEVICE_METADATA", {})
        op_dict["hwsku"] = metadata_dict.get("DEVICE_METADATA_LIST")[0].get("hwsku")
        op_dict["mac"] = metadata_dict.get("DEVICE_METADATA_LIST")[0].get("mac")
        op_dict["platform"] = metadata_dict.get("DEVICE_METADATA_LIST")[0].get(
            "platform"
        )
        op_dict["type"] = metadata_dict.get("DEVICE_METADATA_LIST")[0].get("type")

    ## Replace None values with empty string
    for key, val in op_dict.items():
        op_dict[key] = "" if val is None else val
    return op_dict


def get_device_img_name(device_ip: str):
    """
    Sample output :
    {'openconfig-image-management:current': 'SONiC-OS-4.0.5-Enterprise_Advanced'}
    """

    return send_gnmi_get(
        device_ip=device_ip,
        path=[
            Path(
                target="openconfig",
                origin="openconfig-image-management",
                elem=[
                    PathElem(
                        name="image-management",
                    ),
                    PathElem(
                        name="global",
                    ),
                    PathElem(
                        name="state",
                    ),
                    PathElem(
                        name="current",
                    ),
                ],
            )
        ],
    )


def get_device_mgmt_intfc_info(device_ip: str):
    """
    Sample Output :
    {'sonic-mgmt-interface:sonic-mgmt-interface': {'MGMT_INTF_TABLE': {'MGMT_INTF_TABLE_IPADDR_LIST': [
        {'ifName': 'eth0', 'ipPrefix': '10.10.131.111/23'}, {'ifName': 'eth0', 'ipPrefix': 'fe80::6a21:5fff:fe46:cf6e/64'}]}}}
    """

    return send_gnmi_get(
        device_ip=device_ip,
        path=[
            Path(
                target="openconfig",
                origin="sonic-mgmt-interface",
                elem=[
                    PathElem(
                        name="sonic-mgmt-interface",
                    ),
                ],
            )
        ],
    )


def get_device_meta_data(device_ip: str):
    """
    Sample Output :
    {'sonic-device-metadata:DEVICE_METADATA': {'DEVICE_METADATA_LIST': [{'default_config_profile': 'l3', 'hostname': 'sonic',
                                                                         'hwsku': 'Accton-AS7726-32X', 'mac': '68:21:5f:46:cf:71', 'name': 'localhost', 'platform': 'x86_64-accton_as7726_32x-r0', 'type': 'LeafRouter'}]}}
    """

    return send_gnmi_get(
        device_ip=device_ip,
        path=[
            Path(
                target="openconfig",
                origin="sonic-device-metadata",
                elem=[
                    PathElem(
                        name="sonic-device-metadata",
                    ),
                    PathElem(
                        name="DEVICE_METADATA",
                    ),
                ],
            )
        ],
    )


def get_all_devices_ip_from_db():
    return [device.mgt_ip for device in Device.nodes.all()]
