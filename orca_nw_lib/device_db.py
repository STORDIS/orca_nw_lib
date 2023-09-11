from orca_nw_lib.graph_db_models import Device


def get_all_devices_ip_from_db():
    return [device.mgt_ip for device in Device.nodes.all()]


def get_device_db_obj(mgt_ip: str = None):
    if mgt_ip:
        return Device.nodes.get_or_none(mgt_ip=mgt_ip)
    return Device.nodes.all()