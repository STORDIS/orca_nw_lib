from .gnmi_pb2 import Path, PathElem
from .gnmi_util import send_gnmi_get, get_gnmi_path


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


def get_device_details_from_device(device_ip: str):
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


def get_device_state_url():
    return get_gnmi_path("openconfig-system:system/openconfig-events:events")


def get_device_status_from_device(device_ip: str):
    return send_gnmi_get(
        path=[get_device_state_url()],
        device_ip=device_ip,
    )


def get_image_list_from_device(device_ip: str):
    path = get_gnmi_path(
        "sonic-image-management:sonic-image-management/IMAGE_TABLE/IMAGE_TABLE_LIST"
    )
    return send_gnmi_get(
        path=[path],
        device_ip=device_ip,
    )
