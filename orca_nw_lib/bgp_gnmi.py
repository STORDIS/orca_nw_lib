from .gnmi_pb2 import Path, PathElem
from .gnmi_util import (
    create_gnmi_update,
    create_req_for_update,
    get_gnmi_del_req,
    send_gnmi_get,
    send_gnmi_set,
)
from .gnmi_pb2 import Path, PathElem


def get_bgp_neighbor_base_path() -> Path:
    """
    Generates the base path for the BGP neighbor in the OpenConfig model.

    Returns:
        Path: The base path for the BGP neighbor.
    """
    return Path(
        target="openconfig",
        elem=[
            PathElem(
                name="sonic-bgp-neighbor:sonic-bgp-neighbor",
            )
        ],
    )


def get_bgp_neighbor_list_path() -> Path:
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


def get_bgp_neighbor_af_list_path() -> Path:
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


def get_base_bgp_global_path() -> Path:
    """
    Get the base BGP global path.

    Returns:
        Path: The base BGP global path.
    """
    return Path(
        target="openconfig",
        elem=[
            PathElem(
                name="sonic-bgp-global:sonic-bgp-global",
            )
        ],
    )


def get_bgp_global_path() -> Path:
    path = get_base_bgp_global_path()
    path.elem.append(
        PathElem(
            name="BGP_GLOBALS",
        )
    )
    return path


def get_bgp_global_list_path() -> Path:
    path = get_bgp_global_path()
    path.elem.append(
        PathElem(
            name="BGP_GLOBALS_LIST",
        )
    )
    return path


def get_bgp_global_list_of_vrf_path(vrf_name) -> Path:
    path = get_bgp_global_path()
    path.elem.append(PathElem(name="BGP_GLOBALS_LIST", key={"vrf_name": vrf_name}))
    return path


def get_bgp_global_af_list_path() -> Path:
    path = get_base_bgp_global_path()
    path.elem.append(PathElem(name="BGP_GLOBALS_AF"))
    path.elem.append(PathElem(name="BGP_GLOBALS_AF_LIST"))
    return path


def get_bgp_global_list_from_device(device_ip: str):
    return send_gnmi_get(device_ip, [get_bgp_global_list_path()])


def get_bgp_global_of_vrf_from_device(device_ip: str, vrf_name: str):
    return send_gnmi_get(device_ip, [get_bgp_global_list_of_vrf_path(vrf_name)])


def config_bgp_global_on_device(
    device_ip: str, local_asn: int, router_id: str, vrf_name: str = "default"
):
    """
    Configure BGP global settings on a device.

    Args:
        device_ip (str): The IP address of the device.
        local_asn (int): The local ASN (Autonomous System Number) of the device.
        router_id (str): The router ID of the device.
        vrf_name (str, optional): The name of the VRF (Virtual Routing and Forwarding)
            instance. Defaults to "default".

    Returns:
        dict: The response from the GNMI (gRPC Network Management Interface) set operation.

    Raises:
        None
    """
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


def config_bgp_global_af_on_device(
    device_ip: str, afi_safi: str, vrf_name: str = "default"
):
    """
    Configures the Border Gateway Protocol (BGP) Global Address Family (AF) on a specific device.

    Args:
        device_ip (str): The IP address of the device.
        afi_safi (str): The Address Family Identifier (AFI)
        and Subsequent Address Family Identifier (SAFI) to be configured.
        vrf_name (str, optional): The Virtual Routing and Forwarding (VRF) name.
        Defaults to "default".

    Returns:
        str: The response from the send_gnmi_set function.

    Raises:
        None

    Example Usage:
        config_bgp_global_af_on_device("192.168.1.1", "ipv4-unicast", "VRF1")
    """
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


def get_bgp_neighbor_from_device(device_ip: str):
    return send_gnmi_get(device_ip, [get_bgp_neighbor_list_path()])


def get_all_bgp_af_list_from_device(device_ip):
    return send_gnmi_get(device_ip, [get_bgp_global_af_list_path()])


def del_all_bgp_global_af_from_device(device_ip: str):
    return send_gnmi_set(get_gnmi_del_req(get_bgp_global_af_list_path()), device_ip)


def config_bgp_neighbors_on_device(
    device_ip: str,
    remote_asn: int,
    neighbor_ip: str,
    remote_vrf: str,
    admin_status: bool = True,
):
    """
    Configures BGP neighbors on a device.

    Args:
        device_ip (str): The IP address of the device.
        remote_asn (int): The remote ASN (Autonomous System Number).
        neighbor_ip (str): The IP address of the BGP neighbor.
        remote_vrf (str): The remote VRF (Virtual Routing and Forwarding) name.
        admin_status (bool, optional): The administrative status of the BGP neighbor.
        Defaults to True.

    Returns:
        The result of the GNMI set operation.

    Raises:
        None
    """
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


def config_bgp_neighbor_af_on_device(
    device_ip: str,
    afi_safi: str,
    neighbor_ip: str,
    vrf: str,
    admin_status: bool = True,
):
    """
    Configures the BGP neighbor address family on a device.

    Parameters:
        device_ip (str): The IP address of the device.
        afi_safi (str): The address family identifier.
        neighbor_ip (str): The IP address of the BGP neighbor.
        vrf (str): The VRF (Virtual Routing and Forwarding) name.
        admin_status (bool, optional): The administrative status of the neighbor. Defaults to True.

    Returns:
        None
    """
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


def get_all_neighbor_af_list_from_device(device_ip):
    return send_gnmi_get(device_ip, [get_bgp_neighbor_af_list_path()])


def del_all_neighbor_af_from_device(device_ip: str):
    return send_gnmi_set(get_gnmi_del_req(get_bgp_neighbor_af_list_path()), device_ip)


def del_all_bgp_neighbors_from_device(device_ip: str):
    return send_gnmi_set(get_gnmi_del_req(get_bgp_neighbor_list_path()), device_ip)


def del_bgp_global_from_device(device_ip: str, vrf_name: str):
    return send_gnmi_set(
        get_gnmi_del_req(get_bgp_global_list_of_vrf_path(vrf_name)), device_ip
    )
