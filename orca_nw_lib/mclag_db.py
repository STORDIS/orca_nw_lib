from typing import List

from .device_db import get_device_db_obj
from .graph_db_models import MCLAG, MCLAG_GW_MAC, Device, Interface, PortChannel
from .interface_db import get_interface_of_device_from_db
from .port_chnl_db import get_port_chnl_of_device_from_db
from .utils import get_logging

_logger = get_logging().getLogger(__name__)


def get_mclag_of_device_from_db(device_ip: str, domain_id: int = None):
    """
    Get the MCLAG of a device from the database.

    Args:
        device_ip (str): The IP address of the device.
        domain_id (int, optional): The domain ID. Defaults to None.

    Returns:
        MCLAG or QuerySet or None: The MCLAG object if domain_id is provided and device exists,
        or the QuerySet of all MCLAGs if device exists, or None if device doesn't exist.
    """
    device = get_device_db_obj(device_ip)
    if domain_id:
        return device.mclags.get_or_none(domain_id=domain_id) if device else None
    return device.mclags.all() if device else None


def get_mclag_gw_mac_of_device_from_db(device_ip: str, mac: str = None):
    """
    Retrieves the MCLAG gateway MAC address of a device from the database.

    Args:
        device_ip (str): The IP address of the device.
        mac (str, optional): The MAC address to filter the result. Defaults to None.

    Returns:
        object or None: If `mac` is provided, returns the MCLAG gateway
        MAC address of the device if it exists in the database,
        otherwise returns None.
        If `mac` is not provided, returns a queryset of all MCLAG gateway
        MAC addresses of the device if it exists in the database, otherwise returns None.
    """
    device = get_device_db_obj(device_ip)

    if mac:
        return device.mclag_gw_macs.get_or_none(gateway_mac=mac) if device else None
    else:
        return device.mclag_gw_macs.all() if device else None


def del_mclag_gw_mac_of_device_from_db(device_ip: str, mac: str = None):
    """
    This function is responsible for deleting a specific MCLAG gateway MAC address
    associated with a device from the database.

    Args:
        device_ip (str): The management IP address of the device.
        mac (str, optional): The MAC address of the MCLAG gateway.
        If not provided, all MCLAG gateway MAC addresses associated with the device will be deleted.

    Returns:
        None

    """
    device = get_device_db_obj(device_ip)
    gw_mac = device.mclag_gw_macs.get_or_none(gateway_mac=mac) if device else None
    if gw_mac:
        gw_mac.delete()


def del_mclag_of_device_from_db(device_ip: str, domain_id: int):
    """
    Deletes the Multi-Chassis Link Aggregation (MCLAG) for a specific device from the database.

    Args:
        device_ip (str): The IP address of the device.
        domain_id (int): The domain ID of the MCLAG.

    Returns:
        None
    """
    device = get_device_db_obj(device_ip)
    mclag = device.mclags.get_or_none(domain_id=domain_id) if device else None
    if mclag:
        mclag.delete()


def create_mclag_peerlink_relations_in_db():
    """
    Creates MCLAG peerlink relations in the database.

    Retrieves devices from the database using the `getDeviceFromDB()` function.
    For each device, fetches the MCLAG information using the `get_mclag_of_device_from_db()` function.
    If the MCLAG information is available, retrieves the peer link and port channel information
    using the `get_port_chnl_of_device_from_db()` function.
    Connects the MCLAG peer link node to the port channel if the port channel information is available.

    Retrieves the peer address from the MCLAG information.
    Fetches the MCLAG information of the peer device using the `get_mclag_of_device_from_db()` function.
    Retrieves the peer link and port channel information of the peer device.
    Connects the port channel of the local device to the port channel of the peer device if both port channel information is available.
    """
    for local_dev in get_device_db_obj() or []:
        # there is only 1 mclag per device possible so always fetch index 0
        mclag_local = (
            mcl[0] if (mcl := get_mclag_of_device_from_db(local_dev.mgt_ip)) else None
        )
        if mclag_local:
            peer_link_local = mclag_local.peer_link
            port_chnl_local = get_port_chnl_of_device_from_db(
                local_dev.mgt_ip, peer_link_local
            )
            if port_chnl_local:
                mclag_local.peer_link_node.connect(port_chnl_local)

            peer_addr = mclag_local.peer_addr
            mclag_remote = (
                mcl_r[0] if peer_addr and (mcl_r := get_mclag_of_device_from_db(peer_addr)) else None
            )
            peer_link_remote = mclag_remote.peer_link if mclag_remote else None
            if peer_addr and peer_link_remote:
                port_chnl_remote = get_port_chnl_of_device_from_db(
                    peer_addr, peer_link_remote
                )
                if port_chnl_remote:
                    mclag_remote.peer_link_node.connect(port_chnl_remote)

                port_chnl_local.peer_link.connect(
                    port_chnl_remote
                ) if port_chnl_local and port_chnl_remote else None


def copy_mclag_obj_props(target_obj: MCLAG, src_obj: MCLAG):
    """
    Copies the properties of an MCLAG object from a source object to a target object.

    Parameters:
        target_obj (MCLAG): The target MCLAG object to copy the properties to.
        src_obj (MCLAG): The source MCLAG object to copy the properties from.

    Returns:
        None
    """
    target_obj.domain_id = src_obj.domain_id
    target_obj.keepalive_interval = src_obj.keepalive_interval
    target_obj.mclag_sys_mac = src_obj.mclag_sys_mac
    target_obj.peer_addr = src_obj.peer_addr
    target_obj.peer_link = src_obj.peer_link
    target_obj.session_timeout = src_obj.session_timeout
    target_obj.source_address = src_obj.source_address
    target_obj.oper_status = src_obj.oper_status
    target_obj.role = src_obj.role
    target_obj.system_mac = src_obj.system_mac
    target_obj.delay_restore = src_obj.delay_restore
    target_obj.session_vrf = src_obj.session_vrf
    target_obj.fast_convergence = src_obj.fast_convergence


def insert_device_mclag_in_db(device: Device, mclag_to_intfc_list):
    """
    Insert the device's MCLAG information into the database.

    Args:
        device (Device): The device object representing the device.
        mclag_to_intfc_list (dict): A dictionary mapping MCLAG objects to a list of interface names.

    Returns:
        None

    Raises:
        None
    """
    for mclag, intfcs in mclag_to_intfc_list.items():
        if mclag_in_db := get_mclag_of_device_from_db(device.mgt_ip, mclag.domain_id):
            copy_mclag_obj_props(mclag_in_db, mclag)
            mclag_in_db.save()
            device.mclags.connect(mclag_in_db)

        else:
            mclag.save()
            device.mclags.connect(mclag)

        saved_mclag = get_mclag_of_device_from_db(device.mgt_ip, mclag.domain_id)

        for intf_name in intfcs:
            intf_obj = get_interface_of_device_from_db(device.mgt_ip, intf_name)
            if intf_obj:
                saved_mclag.intfc_members.connect(intf_obj)
            port_chnl_obj = get_port_chnl_of_device_from_db(device.mgt_ip, intf_name)
            if port_chnl_obj:
                saved_mclag.portChnl_member.connect(port_chnl_obj)

    ## Handle the case when some or all mclags has been deleted from device but remained in DB
    ## Remove all mclags which are in DB but not on device

    for mcl_in_db in get_mclag_of_device_from_db(device.mgt_ip):
        if mcl_in_db not in mclag_to_intfc_list:
            del_mclag_of_device_from_db(device.mgt_ip, mcl_in_db.domain_id)
        ## Also disconnect interfaces and port channels if not a member of mclag in the device
        for mem_if in mcl_in_db.intfc_members.all() or []:
            if mem_if.name not in mclag_to_intfc_list.get(mcl_in_db):
                mcl_in_db.intfc_members.disconnect(mem_if)

        for mem_chnl in mcl_in_db.portChnl_member.all() or []:
            if mem_chnl.lag_name not in mclag_to_intfc_list.get(mcl_in_db):
                mcl_in_db.portChnl_member.disconnect(mem_chnl)


def copy_mclag_gw_mac_props(target_obj: MCLAG_GW_MAC, src_obj: MCLAG_GW_MAC):
    """
    Copy the MCLAG gateway MAC properties from the source object to the target object.

    Args:
        target_obj (MCLAG_GW_MAC): The target object to copy the properties to.
        src_obj (MCLAG_GW_MAC): The source object to copy the properties from.

    Returns:
        None
    """
    target_obj.gateway_mac = src_obj.gateway_mac


def insert_device_mclag_gw_macs_in_db(
    device: Device, mclag_gw_macs: List[MCLAG_GW_MAC]
):
    """
    Insert the MCLAG gateway MAC addresses of a device into the database.

    Args:
        device (Device): The device object.
        mclag_gw_macs (List[MCLAG_GW_MAC]): A list of MCLAG_GW_MAC objects
        representing the gateway MAC addresses.

    Returns:
        None

    Raises:
        None

    Description:
        This function inserts the MCLAG gateway MAC addresses of a device into the database.
        It iterates over the given list of MCLAG_GW_MAC objects
        and performs the following steps for each object:

        1. If the gateway MAC address already exists in the database for the given device,
           the properties of the existing gateway MAC address are updated with
           the properties of the new object, and the updated object is saved to the database.
        2. If the gateway MAC address does not exist in the database for the given device,
           the new object is saved to the database.
        3. The device is connected to the gateway MAC address in the database.

        After inserting all the gateway MAC addresses, the function checks for any remaining
        gateway MAC addresses in the database that are not present in the given list.
        If any such gateway MAC address is found, it is deleted from the database.

    Note:
        - This function assumes that the device object has a "mgt_ip" attribute
          representing the management IP address of the device.
        - The functions "get_mclag_gw_mac_of_device_from_db"
          and "del_mclag_gw_mac_of_device_from_db" are assumed to be defined elsewhere
          in the codebase and are used to interact with the database.

    Example Usage:
        device = Device(...)
        mclag_gw_macs = [MCLAG_GW_MAC(...), MCLAG_GW_MAC(...)]
        insert_device_mclag_gw_macs_in_db(device, mclag_gw_macs)
    """
    for mclag_gw_mac in mclag_gw_macs:
        if gw_mac_in_db := get_mclag_gw_mac_of_device_from_db(
            device.mgt_ip, mclag_gw_mac.gateway_mac
        ):
            copy_mclag_gw_mac_props(gw_mac_in_db, mclag_gw_mac)
            gw_mac_in_db.save()
            device.mclag_gw_macs.connect(gw_mac_in_db)
        else:
            mclag_gw_mac.save()
            device.mclag_gw_macs.connect(mclag_gw_mac)

    ## Handle the case when some or all mclags gw macs has
    ## been deleted from device but remained in DB
    ## Remove all mclags gw macs which are in DB but not on device

    for gw_mac_in_db in get_mclag_gw_mac_of_device_from_db(device.mgt_ip):
        if gw_mac_in_db not in mclag_gw_macs:
            del_mclag_gw_mac_of_device_from_db(device.mgt_ip, gw_mac_in_db.gateway_mac)


def create_mclag_peer_link_rel_in_db():
    """
    Create MCLAG peer-link relation in the database.

    This function is responsible for discovering MCLAG peer-link relations
    and creating them in the database. It calls the 
    `create_mclag_peerlink_relations_in_db()` function to perform the actual
    creation of the relations.

    Parameters:
        None

    Returns:
        None
    """
    _logger.info("Discovering MCLAG peer-link relations.")
    create_mclag_peerlink_relations_in_db()
