from .common import MclagFastConvergence
from .gnmi_pb2 import Path, PathElem
from .gnmi_util import (
    create_gnmi_update,
    create_req_for_update,
    get_gnmi_del_req,
    send_gnmi_get,
    send_gnmi_set,
    get_gnmi_path,
)


def get_mclag_path() -> Path:
    """
    Return an instance of `Path` representing the MCLAG path.

    :return: An instance of `Path` representing the MCLAG path.
    :rtype: Path
    """
    return Path(target="openconfig", elem=[PathElem(name="openconfig-mclag:mclag")])


def get_mclag_if_path(mclag_member=None) -> Path:
    """
    Retrieves the MCLAG interface path.

    Returns:
        if member
            Path: The MCLAG interface path for particular Member (PortChannel)
        Else
            Path: The MCLAG interface path.
    """
    path: Path = get_mclag_path()
    path.elem.append(PathElem(name="interfaces"))

    path.elem.append(
        PathElem(name="interface", key={"name": mclag_member})
        if mclag_member
        else PathElem(name="interface")
    )

    return path


def get_mclag_gateway_mac_path() -> Path:
    path: Path = get_mclag_path()
    path.elem.append(PathElem(name="mclag-gateway-macs"))
    return path


def get_mclag_domain_path() -> Path:
    path: Path = get_mclag_path()
    path.elem.append(PathElem(name="mclag-domains"))
    path.elem.append(PathElem(name="mclag-domain"))
    return path


def config_mclag_domain_on_device(
    device_ip: int,
    domain_id: int,
    source_addr: str = None,
    peer_addr: str = None,
    peer_link: str = None,
    mclag_sys_mac: str = None,
    keepalive_int: int = 1,
    session_timeout: int = 30,
    delay_restore: int = 300,
    session_vrf: str = None,
    fast_convergence: MclagFastConvergence = None,
):
    """
    Configure the MCLAG domain on a device.

    Args:
        device_ip (str): The IP address of the device.
        domain_id (int): The ID of the MCLAG domain.
        source_addr (str): The source address for the MCLAG domain.
        peer_addr (str): The peer address for the MCLAG domain.
        peer_link (str): The peer link for the MCLAG domain.
        mclag_sys_mac (str): The MCLAG system MAC address.
        keepalive_int (int, optional): The keepalive interval for the MCLAG domain.Defaults to None.
        session_timeout (int, optional): The session timeout for the MCLAG domain. Defaults to None.
        delay_restore (int, optional): The delay restore for the MCLAG domain. Defaults to None.
        session_vrf (str, optional): The session VRF for the MCLAG domain. Defaults to None.
        fast_convergence (MclagFastConvergence, optional): The fast convergence for the MCLAG domain. Defaults to None.

    Returns:
        The result of the GNMI set operation.
    """
    mclag_config_json = {
        "openconfig-mclag:mclag-domain": [
            {
                "domain-id": domain_id,
                "config": {
                    "domain-id": domain_id,
                },
            }
        ]
    }
    config_node = mclag_config_json["openconfig-mclag:mclag-domain"][0]["config"]
    updates = []
    if source_addr:
        config_node["source-address"] = source_addr
    if peer_addr:
        config_node["peer-address"] = peer_addr

    if peer_link:
        config_node["peer-link"] = peer_link

    if mclag_sys_mac:
        config_node["mclag-system-mac"] = mclag_sys_mac

    if keepalive_int:
        config_node["keepalive-interval"] = keepalive_int

    if session_timeout:
        config_node["session-timeout"] = session_timeout

    if delay_restore:
        config_node["delay-restore"] = delay_restore

    if session_vrf:
        config_node["session-vrf"] = session_vrf

    updates.append(create_gnmi_update(get_mclag_domain_path(), mclag_config_json))

    # fast convergence can only be enabled if its disable it needs to be deleted
    if fast_convergence == MclagFastConvergence.enable:
        updates.append(config_mclag_domain_fast_convergence_on_device(domain_id))
    if fast_convergence == MclagFastConvergence.disable:
        remove_mclag_domain_fast_convergence_on_device(
            device_ip=device_ip, domain_id=domain_id
        )
    return send_gnmi_set(
        create_req_for_update(updates),
        device_ip,
    )


def config_mclag_member_on_device(
    device_ip: str, mclag_domain_id: int, port_chnl_name: str
):
    """
    Configures the MCLAG member port channel on a specific device.

    Args:
        device_ip (str): The IP address of the device.
        mclag_domain_id (int): The ID of the MCLAG domain.
        port_chnl_name (str): The name of the member port channel.

    Returns:
        The result of the GNMI set request.
    """
    payload = {
        "openconfig-mclag:interface": [
            {
                "name": port_chnl_name,
                "config": {"name": port_chnl_name, "mclag-domain-id": mclag_domain_id},
            }
        ]
    }
    return send_gnmi_set(
        create_req_for_update([create_gnmi_update(get_mclag_if_path(), payload)]),
        device_ip,
    )


def get_mclag_mem_portchnl_on_device(device_ip: str):
    """
    Gets the MCLAG member port channel on a given device.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        The result of sending a GNMI get request to the device's IP address,
        using the MCLAG interface path.

    """
    return send_gnmi_get(device_ip=device_ip, path=[get_mclag_if_path()])


def del_mclag_member_on_device(device_ip: str, mclag_member: str = None):
    """
    Deletes the MCLAG member port channel on the specified device.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        The response from sending the GNMI delete request.
    """
    return send_gnmi_set(get_gnmi_del_req(get_mclag_if_path(mclag_member)), device_ip)


def config_mclag_gateway_mac_on_device(device_ip: str, mclag_gateway_mac: str):
    """
    Configures the MCLAG gateway MAC address on the specified device.

    Args:
        device_ip (str): The IP address of the device.
        mclag_gateway_mac (str): The MAC address of the MCLAG gateway.

    Returns:
        The result of the GNMI set operation.

    Raises:
        None
    """
    mclag_gateway_mac_json = {
        "openconfig-mclag:mclag-gateway-macs": {
            "mclag-gateway-mac": [
                {
                    "gateway-mac": mclag_gateway_mac,
                    "config": {"gateway-mac": mclag_gateway_mac},
                }
            ]
        }
    }

    return send_gnmi_set(
        create_req_for_update(
            [create_gnmi_update(get_mclag_gateway_mac_path(), mclag_gateway_mac_json)]
        ),
        device_ip,
    )


def get_mclag_gateway_mac_from_device(device_ip: str):
    """
    Get the MAC address of the MCLAG gateway from a device.

    Parameters:
        device_ip (str): The IP address of the device.

    Returns:
        The MAC address of the MCLAG gateway.
    """
    return send_gnmi_get(device_ip=device_ip, path=[get_mclag_gateway_mac_path()])


def del_mclag_gateway_mac_from_device(device_ip: str):
    """
    Deletes the MCLAG gateway MAC address from the specified device.

    Args:
        device_ip (str): The IP address of the device from which to delete the MCLAG gateway MAC address.

    Returns:
        None: This function does not return any value.
    """
    return send_gnmi_set(get_gnmi_del_req(get_mclag_gateway_mac_path()), device_ip)


def get_mclag_domain_from_device(device_ip: str):
    """
    Get the MCLAG domain from a device.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        The MCLAG domain retrieved from the device.
    """
    return send_gnmi_get(device_ip=device_ip, path=[get_mclag_domain_path()])


def get_mclag_config_from_device(device_ip: str):
    """
    Retrieves the MCLAG configuration from the specified device.

    Args:
        device_ip (str): The IP address of the device to retrieve the configuration from.

    Returns:
        The MCLAG configuration as returned by the `send_gnmi_get` function with the
        specified device IP and MCLAG path.

    Raises:
        None.
    """
    return send_gnmi_get(device_ip=device_ip, path=[get_mclag_path()])


def del_mclag_from_device(device_ip: str):
    """
    Deletes the MCLAG configuration from the specified device.

    Args:
        device_ip (str): The IP address of the device to delete the MCLAG configuration from.

    Returns:
        None: This function does not return anything.
    """
    return send_gnmi_set(get_gnmi_del_req(get_mclag_path()), device_ip)


def get_sonic_mclag_domain_list_path(domain_id: int):
    return get_gnmi_path(
        f"/sonic-mclag:sonic-mclag/MCLAG_DOMAIN/MCLAG_DOMAIN_LIST[domain_id={domain_id}]"
    )


def config_mclag_domain_fast_convergence_on_device(domain_id: int):
    """
    Configures the MCLAG domain fast convergence.

    Args:
        domain_id (int): The ID of the MCLAG domain.

    Returns:
        The result of the GNMI set operation.

    Raises:
        None
    """
    path = get_sonic_mclag_domain_list_path(domain_id)
    req_body = {
        "sonic-mclag:MCLAG_DOMAIN_LIST": [
            {"domain_id": domain_id, "fast_convergence": "enable"}
        ]
    }
    return create_gnmi_update(path=path, val=req_body)


def get_mclag_domain_fast_convergence_from_device(device_ip: str, domain_id: int):
    """
    Get the MCLAG domain fast convergence from a device.

    Args:
        device_ip (str): The IP address of the device.
        domain_id (int): The ID of the MCLAG domain.

    Returns:
        The MCLAG domain fast convergence retrieved from the device.
    """
    return send_gnmi_get(
        device_ip=device_ip,
        path=[get_sonic_mclag_domain_list_path(domain_id=domain_id)],
    )


def remove_mclag_domain_fast_convergence_on_device(device_ip: str, domain_id: int):
    """
    Deletes the MCLAG domain fast convergence.

    Args:
        device_ip (str): The IP address of the device.
        domain_id (int): The ID of the MCLAG domain.

    Returns:
        The result of the GNMI set operation.

    Raises:
        None
    """
    path = get_sonic_mclag_domain_list_path(domain_id)
    path.elem.append(PathElem(name="fast_convergence"))
    return send_gnmi_set(req=get_gnmi_del_req(path=path), device_ip=device_ip)


def add_mclag_domain_fast_convergence_on_device(device_ip: str, domain_id: int):
    """
    Adds the MCLAG domain fast convergence.

    Args:
        device_ip (str): The IP address of the device.
        domain_id (int): The ID of the MCLAG domain.

    Returns:
        The result of the GNMI set operation.

    Raises:
        None
    """
    path = get_sonic_mclag_domain_list_path(domain_id)
    path.elem.append(PathElem(name="fast_convergence"))
    return send_gnmi_set(
        req=create_req_for_update(
            [config_mclag_domain_fast_convergence_on_device(domain_id)]
        ),
        device_ip=device_ip,
    )
