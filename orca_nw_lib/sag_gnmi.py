from orca_nw_lib.gnmi_util import get_gnmi_path, send_gnmi_get

def get_sag_info_from_device(device_ip: str):
    """
    Retrieves the SAG information from the specified device.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        The result of the GNMI get request for the SAG information.
    """
    platform_path = get_gnmi_path("sonic-sag:sonic-sag")
    return send_gnmi_get(
        path=[platform_path],
        device_ip=device_ip,
    )