from typing import List
from orca_nw_lib.device import getDeviceFromDB

from orca_nw_lib.gnmi_pb2 import Path, PathElem
from orca_nw_lib.gnmi_util import (
    create_gnmi_update,
    create_req_for_update,
    get_gnmi_del_req,
    send_gnmi_get,
    send_gnmi_set,
)
from orca_nw_lib.graph_db_models import BGP, Device
from orca_nw_lib.interfaces import getSubInterfaceFromDB
from orca_nw_lib.mclag import get_mclag_gateway_mac_path
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
        for nbr in nbr_list.get("sonic-bgp-neighbor:BGP_NEIGHBOR_LIST") or []:
            if bgp.vrf_name == nbr.get("vrf_name"):
                remote_asn_list.append(nbr.get("asn"))
                nbr_ips.append(nbr.get("neighbor"))

        bgp.remote_asn = remote_asn_list
        bgp.nbr_ips = nbr_ips
        bgp_global_list.append(bgp)

    return bgp_global_list


def connect_bgp_peers():
    # connect bgp node to subinterfaces
    for device in getDeviceFromDB():
        for bgp in device.bgp.all() or []:
            for nbr_ip in bgp.nbr_ips:
                bgp.neighbors.connect(si) if (
                    si := getSubInterfaceFromDB(nbr_ip)
                ) else None
            for remote_as in bgp.remote_asn:
                [
                    bgp.remote_asn_node.connect(rem_bgp)
                    for rem_bgp in getBGPFromDB(remote_as)
                ]


def getBGPGlobalJsonFromDB(device_ip):
    op_dict = []
    bgp_global = getBgpGlobalListOfDeviceFromDB(device_ip)
    if bgp_global:
        op_dict.append(bgp_global.__properties__)
    return op_dict


def getBgpGlobalListOfDeviceFromDB(device_ip) -> List[BGP]:
    device = getDeviceFromDB(device_ip)
    bgp_global_list = device.bgp.get_or_none() if device else None
    return bgp_global_list


def getBGPFromDB(asn: int) -> List[BGP]:
    bgp = []
    for device in getDeviceFromDB():
        for b in device.bgp.all() or []:
            if b.local_asn == asn:
                bgp.append(b)
    return bgp


def copy_bgp_object_prop(target_obj: BGP, src_obj: BGP):
    target_obj.local_asn = src_obj.local_asn
    target_obj.vrf_name = src_obj.vrf_name
    target_obj.router_id = src_obj.router_id
    target_obj.remote_asn = src_obj.remote_asn
    target_obj.nbr_ips = src_obj.nbr_ips


def insert_device_bgp_in_db(device: Device, bgp_global_list: List[BGP]):
    for bgp in bgp_global_list:
        if b := getBGPFromDB(bgp.local_asn):
            copy_bgp_object_prop(b[0], bgp)
            b[0].save()
            device.bgp.connect(b[0])
        else:
            bgp.save()
            device.bgp.connect(bgp)


def get_bgp_neighbor_base_path():
    return Path(
        target="openconfig",
        elem=[
            PathElem(
                name="sonic-bgp-neighbor:sonic-bgp-neighbor",
            )
        ],
    )


def get_bgp_neighbor_list_path():
    path = get_bgp_neighbor_base_path()
    path.elem.append(
        PathElem(
            name="BGP_NEIGHBOR",
        )
    )
    path.elem.append(
        PathElem(
            name="BGP_NEIGHBOR_LIST",
        )
    )
    return path


def get_bgp_neighbor_af_list_path():
    path = get_bgp_neighbor_base_path()
    path.elem.append(
        PathElem(
            name="BGP_NEIGHBOR_AF",
        )
    )
    path.elem.append(
        PathElem(
            name="BGP_NEIGHBOR_AF_LIST",
        )
    )
    return path


def get_base_bgp_global_path():
    return Path(
        target="openconfig",
        elem=[
            PathElem(
                name="sonic-bgp-global:sonic-bgp-global",
            )
        ],
    )


def get_bgp_global_path():
    path = get_base_bgp_global_path()
    path.elem.append(
        PathElem(
            name="BGP_GLOBALS",
        )
    )
    return path


def get_bgp_global_list_path():
    path = get_bgp_global_path()
    path.elem.append(
        PathElem(
            name="BGP_GLOBALS_LIST",
        )
    )
    return path


def get_bgp_global_list_of_vrf_path(vrf_name):
    path = get_bgp_global_path()
    path.elem.append(PathElem(name="BGP_GLOBALS_LIST", key={"vrf_name": vrf_name}))
    return path


def get_bgp_global_af_list_path():
    path = get_base_bgp_global_path()
    path.elem.append(PathElem(name="BGP_GLOBALS_AF"))
    path.elem.append(PathElem(name="BGP_GLOBALS_AF_LIST"))
    return path


def get_bgp_global_list_from_device(device_ip: str):
    return send_gnmi_get(device_ip, [get_bgp_global_list_path()])


def get_bgp_global_of_vrf_from_device(device_ip: str, vrf_name: str):
    return send_gnmi_get(device_ip, [get_bgp_global_list_of_vrf_path(vrf_name)])


def get_bgp_neighbor_from_device(device_ip: str):
    return send_gnmi_get(device_ip, [get_bgp_neighbor_list_path()])


def configBgpGlobalOnDevice(
    device_ip: str, local_asn: int, router_id: str, vrf_name="default"
):
    bgp_global_payload = {
        "sonic-bgp-global:BGP_GLOBALS_LIST": [
            {"local_asn": local_asn, "router_id": router_id, "vrf_name": vrf_name}
        ]
    }

    return send_gnmi_set(
        create_req_for_update(
            [create_gnmi_update(get_bgp_global_list_path(), bgp_global_payload)]
        ),
        device_ip,
    )


def configBgpGlobalAFOnDevice(device_ip: str, afi_safi: str, vrf_name="default"):
    bgp_global_af_payload = {
        "sonic-bgp-global:BGP_GLOBALS_AF_LIST": [
            {"afi_safi": afi_safi, "vrf_name": vrf_name}
        ]
    }

    return send_gnmi_set(
        create_req_for_update(
            [create_gnmi_update(get_bgp_global_af_list_path(), bgp_global_af_payload)]
        ),
        device_ip,
    )


def getAllBgpAfListFromDevice(device_ip):
    return send_gnmi_get(device_ip, [get_bgp_global_af_list_path()])


def delAllBgpGlobalAFFromDevice(device_ip: str):
    return send_gnmi_set(get_gnmi_del_req(get_bgp_global_af_list_path()), device_ip)


def configBGPNeighborsOnDevice(
    device_ip: str,
    remote_asn: int,
    neighbor_ip: str,
    remote_vrf: str,
    admin_status: bool = True,
):
    bgp_nbr_payload = {
        "sonic-bgp-neighbor:BGP_NEIGHBOR_LIST": [
            {
                "asn": remote_asn,
                "neighbor": neighbor_ip,
                "vrf_name": remote_vrf,
                # "admin_status": admin_status,
            }
        ]
    }

    return send_gnmi_set(
        create_req_for_update(
            [create_gnmi_update(get_bgp_neighbor_list_path(), bgp_nbr_payload)]
        ),
        device_ip,
    )


def configBGPNeighborAFOnDevice(
    device_ip: str,
    afi_safi: str,
    neighbor_ip: str,
    vrf: str,
    admin_status: bool = True,
):
    bgp_nbr_payload = {
        "sonic-bgp-neighbor:BGP_NEIGHBOR_AF_LIST": [
            {
                "admin_status": admin_status,
                "afi_safi": afi_safi,
                "neighbor": neighbor_ip,
                "vrf_name": vrf,
            }
        ]
    }

    return send_gnmi_set(
        create_req_for_update(
            [create_gnmi_update(get_bgp_neighbor_af_list_path(), bgp_nbr_payload)]
        ),
        device_ip,
    )


def getAllNeighborAfListFromDevice(device_ip):
    return send_gnmi_get(device_ip, [get_bgp_neighbor_af_list_path()])


def delAllNeighborAFFromDevice(device_ip: str):
    return send_gnmi_set(get_gnmi_del_req(get_bgp_neighbor_af_list_path()), device_ip)


def delAllBgpNeighborsFromDevice(device_ip: str):
    return send_gnmi_set(get_gnmi_del_req(get_bgp_neighbor_list_path()), device_ip)


def del_bgp_global_from_device(device_ip: str, vrf_name: str):
    return send_gnmi_set(
        get_gnmi_del_req(get_bgp_global_list_of_vrf_path(vrf_name)), device_ip
    )
