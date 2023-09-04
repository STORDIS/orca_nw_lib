from time import sleep
from .port_chnl_db import (
    getAllPortChnlOfDeviceFromDB,
    getPortChnlOfDeviceFromDB,
)
from .device import getDeviceFromDB
from .graph_db_models import PortChannel
from .port_chnl_db import (
    get_port_chnl_members_from_db,
    insert_device_port_chnl_in_db,
)

from .port_chnl_gnmi import (
    add_port_chnl_member,
    add_port_chnl_on_device,
    del_port_chnl_from_device,
    get_port_chnls_info_from_device,
    remove_port_chnl_member,
)
from .utils import get_logging

_logger = get_logging().getLogger(__name__)


def createPortChnlGraphObject(device_ip: str, port_chnl_name: str = None):
    port_chnl_json = get_port_chnls_info_from_device(device_ip, port_chnl_name)
    port_chnl_obj_list = {}
    if port_chnl_json:
        lag_table_json_list = port_chnl_json.get("sonic-portchannel:LAG_TABLE_LIST", {})
        lag_mem_table_json_list = port_chnl_json.get(
            "sonic-portchannel:LAG_MEMBER_TABLE_LIST", {}
        )
        for lag in lag_table_json_list or []:
            ifname_list = []
            for mem in lag_mem_table_json_list or []:
                if lag.get("lagname") == mem.get("name"):
                    ifname_list.append(mem.get("ifname"))
            port_chnl_obj_list[
                PortChannel(
                    active=lag.get("active"),
                    lag_name=lag.get("lagname"),
                    admin_sts=lag.get("admin_status"),
                    mtu=lag.get("mtu"),
                    name=lag.get("name"),
                    fallback_operational=lag.get("fallback_operational"),
                    oper_sts=lag.get("oper_status"),
                    speed=lag.get("speed"),
                    oper_sts_reason=lag.get("reason"),
                )
            ] = ifname_list
    return port_chnl_obj_list


def discover_port_chnl(device_ip: str = None, port_chnl_name: str = None):
    _logger.info("Port Channel Discovery Started.")
    devices = [getDeviceFromDB(device_ip)] if device_ip else getDeviceFromDB()
    for device in devices:
        _logger.info(f"Discovering Port Channels of device {device}.")
        insert_device_port_chnl_in_db(
            device, createPortChnlGraphObject(device.mgt_ip, port_chnl_name)
        )


def get_port_chnl(device_ip: str, port_chnl_name=None):
    op_dict = []
    if port_chnl_name:
        op_dict.append(port_chnl.__properties__) if (
            port_chnl := getPortChnlOfDeviceFromDB(device_ip, port_chnl_name)
        ) else None
    else:
        port_chnl = getAllPortChnlOfDeviceFromDB(device_ip)
        for chnl in port_chnl or []:
            op_dict.append(chnl.__properties__)
    return op_dict


def add_port_chnl(
    device_ip: str, chnl_name: str, admin_status: str = None, mtu: int = None
):
    add_port_chnl_on_device(device_ip, chnl_name, admin_status, mtu)
    discover_port_chnl(device_ip)


def del_port_chnl(device_ip: str, chnl_name: str):
    del_port_chnl_from_device(device_ip, chnl_name)
    discover_port_chnl(device_ip)


def add_port_chnl_mem(device_ip: str, chnl_name: str, ifnames: list[str]):
    add_port_chnl_member(device_ip, chnl_name, ifnames)
    ## Note - A bit strange but despite of being single threaded process,
    ## Need to keep a delay between creating channel members and getting them.
    sleep(1)
    discover_port_chnl(device_ip)


def del_port_chnl_mem(device_ip: str, chnl_name: str, ifname: str):
    remove_port_chnl_member(device_ip, chnl_name, ifname)
    discover_port_chnl(device_ip)


def get_port_chnl_members(device_ip: str, port_chnl_name: str, ifname: str = None):
    if ifname:
        return (
            port_chnl_mem.__properties__
            if (
                port_chnl_mem := get_port_chnl_members_from_db(
                    device_ip, port_chnl_name, ifname
                )
            )
            else None
        )
    else:
        op_dict = []
        port_chnl_mems = get_port_chnl_members_from_db(device_ip, port_chnl_name)
        for mem in port_chnl_mems or []:
            op_dict.append(mem.__properties__)
        return op_dict
