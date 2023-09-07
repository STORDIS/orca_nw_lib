from .gnmi_pb2 import Path, PathElem
from .gnmi_util import (
    create_gnmi_update,
    create_req_for_update,
    get_gnmi_del_req,
    send_gnmi_get,
    send_gnmi_set,
)


def get_mclag_path() -> Path:
    """
    Return an instance of `Path` representing the MCLAG path.

    :return: An instance of `Path` representing the MCLAG path.
    :rtype: Path
    """
    return Path(target="openconfig", elem=[PathElem(name="openconfig-mclag:mclag")])


def get_mclag_if_path() -> Path:
    """
    Retrieves the MCLAG interface path.

    Returns:
        Path: The MCLAG interface path.
    """
    path: Path = get_mclag_path()
    path.elem.append(PathElem(name="interfaces"))
    path.elem.append(PathElem(name="interface"))
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
    device_ip: str,
    domain_id: int,
    source_addr: str,
    peer_addr: str,
    peer_link: str,
    mclag_sys_mac: str,
    keepalive_int: int = None,
    session_timeout: int = None,
    delay_restore: int = None,
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

    Returns:
        The result of the GNMI set operation.
    """
    mclag_config_json = {
        "openconfig-mclag:mclag-domain": [
            {
                "domain-id": 0,
                "config": {
                    "domain-id": 0,
                    "source-address": "string",
                    "peer-address": "string",
                    "peer-link": "string",
                    "mclag-system-mac": "string",
                },
            }
        ]
    }

    for mc_lag in mclag_config_json.get("openconfig-mclag:mclag-domain"):
        mc_lag.update({"domain-id": domain_id})
        mc_lag.get("config").update({"domain-id": domain_id})
        mc_lag.get("config").update({"source-address": source_addr})
        mc_lag.get("config").update({"peer-address": peer_addr})
        mc_lag.get("config").update({"peer-link": peer_link})
        mc_lag.get("config").update({"mclag-system-mac": mclag_sys_mac})
        if keepalive_int:
            mc_lag.get("config").update({"keepalive-interval": keepalive_int})
        if session_timeout:
            mc_lag.get("config").update({"session-timeout": session_timeout})
        if delay_restore:
            mc_lag.get("config").update({"delay-restore": delay_restore})

    return send_gnmi_set(
        create_req_for_update(
            [create_gnmi_update(get_mclag_domain_path(), mclag_config_json)]
        ),
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


def del_mclag_member_on_device(device_ip: str):
    """
    Deletes the MCLAG member port channel on the specified device.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        The response from sending the GNMI delete request.
    """
    return send_gnmi_set(get_gnmi_del_req(get_mclag_if_path()), device_ip)


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
