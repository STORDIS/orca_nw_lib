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


def delete_device(mgt_ip: str = None):
    """
    Delete all the has relationship of given device
    Delete the given devices from the database.
    """
    if mgt_ip:

        devices = get_device_db_obj(mgt_ip)

        for chnl in devices.port_chnl.all() or []:
            chnl.delete()

        for mclag in devices.mclags.all() or []:
            mclag.delete()

        for port_group in devices.port_groups.all() or []:
            port_group.delete()

        for vlan in devices.vlans.all() or []:
            vlan.delete()

        for mclag_gw_mac in devices.mclag_gw_macs.all() or []:
            mclag_gw_mac.delete()

        for interface in devices.interfaces.all() or []:
            for sub in interface.subInterfaces.all() or []:
                sub.delete()
            interface.delete()

        devices.delete()

        return True

    else:
        return False

