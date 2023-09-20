from orca_nw_lib.graph_db_models import Device


def get_all_devices_ip_from_db():
    """
    Get all the IP addresses of devices from the database.

    Returns:
        list: A list of IP addresses of devices.
    """
    return [device.mgt_ip for device in Device.nodes.all()]


def get_device_db_obj(mgt_ip: str = None):
    """
    Retrieves the device database object based on the management IP.

    Parameters:
        mgt_ip (str): The management IP of the device. Defaults to None.

    Returns:
        Device: The device database object if the management IP is provided, 
        else returns all device database objects.

    """
    if mgt_ip:
        return Device.nodes.get_or_none(mgt_ip=mgt_ip)
    return Device.nodes.all()