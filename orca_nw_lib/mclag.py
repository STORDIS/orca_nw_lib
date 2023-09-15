from typing import List

from orca_nw_lib.utils import get_logging
from grpc._channel import _InactiveRpcError

from .device_db import get_device_db_obj
from .mclag_db import (
    create_mclag_peer_link_rel_in_db,
    get_mclag_gw_mac_of_device_from_db,
    get_mclag_of_device_from_db,
    insert_device_mclag_gw_macs_in_db,
    insert_device_mclag_in_db,
)


from .mclag_gnmi import (
    config_mclag_domain_on_device,
    config_mclag_gateway_mac_on_device,
    config_mclag_member_on_device,
    del_mclag_from_device,
    del_mclag_gateway_mac_from_device,
    del_mclag_member_on_device,
    get_mclag_config_from_device,
    get_mclag_gateway_mac_from_device,
)
from .graph_db_models import MCLAG_GW_MAC, MCLAG

_logger = get_logging().getLogger(__name__)


def _create_mclag_graph_objects(device_ip: str) -> dict:
    """
    Generates a dictionary of MCLAG objects
    and their associated interfaces based on the provided device IP.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        dict: A dictionary containing MCLAG objects as keys
        and a list of associated interfaces as values.
    """
    mclags_obj_list = {}
    mclag_config = get_mclag_config_from_device(device_ip)
    mclag = mclag_config.get("openconfig-mclag:mclag", {})
    mclag_domains_dict_list = mclag.get("mclag-domains", {}).get("mclag-domain")
    mclag_intfc_list = mclag.get("interfaces", {}).get("interface")

    for mclag_domain in mclag_domains_dict_list or []:
        mclag_obj = MCLAG(
            domain_id=mclag_domain.get("config").get("domain-id"),
            keepalive_interval=mclag_domain.get("config").get("keepalive-interval"),
            mclag_sys_mac=mclag_domain.get("config").get("mclag-system-mac"),
            peer_addr=mclag_domain.get("config").get("peer-address"),
            peer_link=mclag_domain.get("config").get("peer-link"),
            session_timeout=mclag_domain.get("config").get("session-timeout"),
            source_address=mclag_domain.get("config").get("source-address"),
            delay_restore=mclag_domain.get("config").get("delay-restore"),
            oper_status=mclag_domain.get("state").get("oper-status"),
            role=mclag_domain.get("state").get("role"),
            system_mac=mclag_domain.get("state").get("system-mac"),
        )
        intfc_list = [
            mclag_intfc["name"]
            for mclag_intfc in mclag_intfc_list or []
            if mclag_obj.domain_id == mclag_intfc["config"]["mclag-domain-id"]
        ]

        mclags_obj_list[mclag_obj] = intfc_list

    return mclags_obj_list


def _create_mclag_gw_mac_obj(device_ip: str) -> List[MCLAG_GW_MAC]:
    """
    Creates a list of MCLAG_GW_MAC objects based on the given device IP.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        List[MCLAG_GW_MAC]: A list of MCLAG_GW_MAC objects.

    Raises:
        None.

    Example Usage:
        create_mclag_gw_mac_obj("192.168.0.1")
    """
    mclag_gw_objs = []
    resp = get_mclag_gateway_mac_from_device(device_ip)

    oc_macs = resp.get("openconfig-mclag:mclag-gateway-macs", {})

    for mac_data in oc_macs.get("mclag-gateway-mac", []):
        gw_mac = mac_data.get("gateway-mac")
        mclag_gw_objs.append(MCLAG_GW_MAC(gateway_mac=gw_mac))

    return mclag_gw_objs


def discover_mclag(device_ip: str = None):
    _logger.info("MCLAG Discovery Started.")
    devices = [get_device_db_obj(device_ip)] if device_ip else get_device_db_obj()
    for device in devices:
        try:
            _logger.info(f"Discovering MCLAG on device {device}.")
            insert_device_mclag_in_db(
                device, _create_mclag_graph_objects(device.mgt_ip)
            )
        except _InactiveRpcError as err:
            _logger.error(
                f"MCLAG Discovery Failed on device {device_ip}, Reason: {err.details()}"
            )
            raise
    create_mclag_peer_link_rel_in_db()


def discover_mclag_gw_macs(device_ip: str = None):
    _logger.info("MCLAG GW MAC Discovery Started.")
    devices = [get_device_db_obj(device_ip)] if device_ip else get_device_db_obj()
    for device in devices:
        try:
            _logger.info(f"Discovering MCLAG on device {device}.")
            insert_device_mclag_gw_macs_in_db(
                device, _create_mclag_gw_mac_obj(device.mgt_ip)
            )
        except _InactiveRpcError as err:
            _logger.error(
                f"MCLAG gateway MAC Discovery Failed on device {device_ip}, Reason: {err.details()}"
            )
            raise


def get_mclags(device_ip: str, domain_id=None):
    """
    Retrieves MCLAG information from the database based on the given device IP
    and optional domain ID.

    Args:
        device_ip (str): The IP address of the device.
        domain_id (Optional[int]): The ID of the domain. Defaults to None.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing
        the properties of the retrieved MCLAG objects.
    """
    op_dict = []
    if domain_id:
        mclag = get_mclag_of_device_from_db(device_ip, domain_id)
        if mclag:
            op_dict.append(mclag.__properties__)
    else:
        mclags = get_mclag_of_device_from_db(device_ip)
        for mclag in mclags or []:
            op_dict.append(mclag.__properties__)
    return op_dict


def config_mclag(
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
    try:
        config_mclag_domain_on_device(
            device_ip,
            domain_id,
            source_addr,
            peer_addr,
            peer_link,
            mclag_sys_mac,
            keepalive_int,
            session_timeout,
            delay_restore,
        )

    except _InactiveRpcError as err:
        _logger.error(
            f" MCLAG configuration failed on device_ip : {device_ip}, Reason: {err.details()}"
        )
        raise
    finally:
        discover_mclag(device_ip)


def del_mclag(device_ip: str):
    try:
        del_mclag_from_device(device_ip)
    except _InactiveRpcError as err:
        _logger.error(
            f" MCLAG deletion failed on device_ip : {device_ip}, Reason: {err.details()}"
        )
        raise
    finally:
        discover_mclag(device_ip)


def get_mclag_gw_mac(device_ip: str, mac: str = None):
    op_dict = []
    if mac:
        mclag_gw_mac = get_mclag_gw_mac_of_device_from_db(device_ip, mac)
        if mclag_gw_mac:
            op_dict.append(mclag_gw_mac.__properties__)
    else:
        mclag_gw_macs = get_mclag_gw_mac_of_device_from_db(device_ip)
        for mac in mclag_gw_macs or []:
            op_dict.append(mac.__properties__)
    return op_dict


def config_mclag_gw_mac(device_ip: str, gw_mac: str):
    try:
        config_mclag_gateway_mac_on_device(device_ip, gw_mac)
    except _InactiveRpcError as err:
        _logger.error(
            f"MCLAG GW MAC {gw_mac} configuration failed on device_ip : {device_ip}, Reason: {err.details()}"
        )
        raise
    finally:
        discover_mclag_gw_macs(device_ip)


def del_mclag_gw_mac(device_ip: str):
    try:
        del_mclag_gateway_mac_from_device(device_ip)
    except _InactiveRpcError:
        _logger.error(
            f"MCLAG GW MAC deletion failed on device_ip : {device_ip}, Reason: {err.details()}"
        )
        raise
    finally:
        discover_mclag_gw_macs(device_ip)


def get_mclag_mem_intfs(device_ip: str, mclag_domain_id: int):
    mclag = get_mclag_of_device_from_db(device_ip, mclag_domain_id)

    op_dict = []
    if mclag:
        mem_intfcs = mclag.intfc_members.all()

        for intf in mem_intfcs or []:
            op_dict.append(intf.__properties__)
    return op_dict


def get_mclag_mem_portchnls(device_ip: str, mclag_domain_id: int):
    mclag = get_mclag_of_device_from_db(device_ip, mclag_domain_id)

    op_dict = []
    if mclag:
        mem_chnl = mclag.portChnl_member.all()

        for chnl in mem_chnl or []:
            op_dict.append(chnl.__properties__)
    return op_dict


def config_mclag_mem_portchnl(
    device_ip: str, mclag_domain_id: int, port_chnl_name: str
):
    try:
        config_mclag_member_on_device(device_ip, mclag_domain_id, port_chnl_name)
    except _InactiveRpcError as err:
        _logger.error(
            f"MCLAG member {port_chnl_name} configuration failed on mclag_domain_id : {mclag_domain_id} and device_ip : {device_ip}, Reason: {err.details()} "
        )
        raise
    finally:
        discover_mclag(device_ip)


def del_mclag_member(device_ip: str):
    try:
        del_mclag_member_on_device(device_ip)
    except _InactiveRpcError as err:
        _logger.error(
            f"MCLAG member deletion failed on device_ip : {device_ip}, Reason: {err.details()}"
        )
        raise
    finally:
        discover_mclag(device_ip)
