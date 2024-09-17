from orca_nw_lib.graph_db_models import Device
from orca_nw_lib.utils import clean_db, get_logging
_logger = get_logging().getLogger(__name__)

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
    Deletes the device from the database.

    Parameters:
        mgt_ip (str): The management IP of the device. Defaults to None.

    """
    try:
        if mgt_ip:
            ## Delete Specific Device and its components, when mgt_ip is provided.
            device = get_device_db_obj(mgt_ip)

            for chnl in device.port_chnl.all() or []:
                chnl.delete()

            for mclag in device.mclags.all() or []:
                mclag.delete()

            for port_group in device.port_groups.all() or []:
                port_group.delete()

            for vlan in device.vlans.all() or []:
                vlan.delete()

            for mclag_gw_mac in device.mclag_gw_macs.all() or []:
                mclag_gw_mac.delete()

            for interface in device.interfaces.all() or []:
                for sub in interface.subInterfaces.all() or []:
                    sub.delete()
                interface.delete()
                            
            device.delete()
        else:
            ## Delete all devices and their components. When mgt_ip is not provided.
            clean_db()
        return True
    except Exception as e:
        _logger.error(f"Error: {e}")
        return False


def insert_devices_in_db(device:Device):
    if dev:=get_device_db_obj(device.mgt_ip):
        _logger.debug(f"Device with IP {device.mgt_ip} already exists in the database.")
        dev.copy_properties(device)
        dev.save()
    else:
        device.save()


def update_device_status(mgt_ip: str, status: str):
    device = get_device_db_obj(mgt_ip)
    if device:
        device.status = status
        device.save()