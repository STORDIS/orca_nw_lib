from typing import List
from orca_nw_lib.device import getAllDevicesFromDB, getDeviceFromDB

from orca_nw_lib.gnmi_pb2 import Path, PathElem
from orca_nw_lib.gnmi_util import (
    send_gnmi_get,
)
from orca_nw_lib.graph_db_models import BGP, Device
from orca_nw_lib.interfaces import getSubInterfaceFromDB
from orca_nw_lib.utils import get_logging


def createBGPGraphObjects(device_ip: str) -> List[BGP]:
    global_list = get_bgp_global_list_from_device(device_ip)
    bgp_global_list = []
    for bgp_config in global_list.get("sonic-bgp-global:BGP_GLOBALS_LIST") or []:
        bgp = BGP(
            local_asn=bgp_config.get("local_asn"),
            router_id=bgp_config.get("router_id"),
            vrf_name=bgp_config.get("vrf_name"),
        )

        remote_asn_list = []
        nbr_ips = []
        nbr_list = get_bgp_neighbor_from_device(device_ip)
        for nbr in nbr_list.get("sonic-bgp-neighbor:BGP_NEIGHBOR_LIST"):
            if bgp.vrf_name == nbr.get("vrf_name"):
                remote_asn_list.append(nbr.get("asn"))
                nbr_ips.append(nbr.get("neighbor"))

        bgp.remote_asn = remote_asn_list
        bgp.nbr_ips = nbr_ips
        bgp_global_list.append(bgp)

    return bgp_global_list


def connect_bgp_peers():
    # connect bgp node to subinterfaces
    for device in getAllDevicesFromDB():
        for bgp in device.bgp.all() or []:
            for nbr_ip in bgp.nbr_ips:
                bgp.neighbors.connect(getSubInterfaceFromDB(nbr_ip))


def getBgpGlobalListOfDeviceFromDB(device_ip) -> List[BGP]:
    device = getDeviceFromDB(device_ip)
    bgp_global_list = device.bgp.get_or_none() if device else None
    return bgp_global_list


def insert_device_bgp_in_db(device: Device, bgp_global_list: List[BGP]):
    for bgp in bgp_global_list:
        bgp.save()
        device.bgp.connect(bgp)


def get_bgp_neighbor_path():
    return Path(
        target="openconfig",
        elem=[
            PathElem(
                name="sonic-bgp-neighbor:sonic-bgp-neighbor",
            ),
            PathElem(
                name="BGP_NEIGHBOR",
            ),
            PathElem(
                name="BGP_NEIGHBOR_LIST",
            ),
        ],
    )


def get_bgp_global_list_path():
    return Path(
        target="openconfig",
        elem=[
            PathElem(
                name="sonic-bgp-global:sonic-bgp-global",
            ),
            PathElem(
                name="BGP_GLOBALS",
            ),
            PathElem(
                name="BGP_GLOBALS_LIST",
            ),
        ],
    )


def get_bgp_global_list_from_device(device_ip: str):
    return send_gnmi_get(device_ip, [get_bgp_global_list_path()])


def get_bgp_neighbor_from_device(device_ip: str):
    return send_gnmi_get(device_ip, [get_bgp_neighbor_path()])

def configBgpGlobal(local_asn:int,router_id:str,remote_asn:int,vrf_name="default"):
    
    bgp_global_payload={
                            "sonic-bgp-global:BGP_GLOBALS_LIST": [
                                {"local_asn": local_asn,
                                "router_id": router_id,
                                "vrf_name": vrf_name
                                }
                            ]
                        }