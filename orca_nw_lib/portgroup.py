from orca_nw_lib.common import Speed
from orca_nw_lib.device_db import get_device_db_obj
from orca_nw_lib.gnmi_sub import check_gnmi_subscription_and_apply_config
from orca_nw_lib.graph_db_models import PortGroup
from orca_nw_lib.portgroup_gnmi import (
    get_port_group_from_device,
    set_port_group_speed_on_device,
)
from orca_nw_lib.portgroup_db import (
    get_port_group_member_from_db,
    get_port_group_member_names_from_db,
    insert_device_port_groups_in_db,
    get_port_group_from_db, get_port_group_of_if_from_db,
)
from orca_nw_lib.utils import get_logging

_logger = get_logging().getLogger(__name__)


def _create_port_group_graph_objects(device_ip: str, port_group_id=None):
    """
    Create port group graph objects based on the given device IP.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        dict: A dictionary of port group graph objects. The keys are PortGroup objects
            and the values are lists of member interfaces.

    """
    port_groups_json = get_port_group_from_device(device_ip, port_group_id)
    port_group_graph_objs = {}
    for port_group in port_groups_json.get("openconfig-port-group:port-group") or []:
        port_group_state = port_group.get("state", {})
        default_speed = Speed.getSpeedStrFromOCStr(
            port_group_state.get("default-speed")
        )
        member_if_start = port_group_state.get("member-if-start")
        member_if_end = port_group_state.get("member-if-end")
        valid_speeds = [
            Speed.getSpeedStrFromOCStr(s) for s in port_group_state.get("valid-speeds")
        ]
        speed = Speed.getSpeedStrFromOCStr(port_group_state.get("speed"))
        gr_id = port_group_state.get("id")

        mem_infcs = []
        for eth_num in range(
            int(member_if_start.replace("Ethernet", "")),
            int(member_if_end.replace("Ethernet", "")) + 1,
        ):
            mem_infcs.append(f"Ethernet{eth_num}")

        port_group_graph_objs[
            PortGroup(
                port_group_id=gr_id,
                speed=speed,
                valid_speeds=valid_speeds,
                default_speed=default_speed,
            )
        ] = mem_infcs

    return port_group_graph_objs


def get_port_group_members(device_ip: str, group_id):
    """
    Retrieves the members of a port group based on the device IP and group ID.

    Args:
        device_ip (str): The IP address of the device.
        group_id: The ID of the port group.

    Returns:
        list: A list of dictionaries representing the properties of each member interface.
    """
    op_dict = []
    mem_intfcs = get_port_group_member_from_db(device_ip, group_id)
    if mem_intfcs:
        for mem_if in mem_intfcs or []:
            op_dict.append(mem_if.__properties__)
    return op_dict

def get_port_group_of_interface(device_ip: str, if_name:str):
    """
    Retrieves the port group of an interface based on the device IP and interface name.

    Args:
        device_ip (str): The IP address of the device.
        if_name: The name of the interface.

    Returns:
        dict: A dictionary representing the properties of the port group of the interface.
    """
    port_group = get_port_group_of_if_from_db(device_ip, if_name)
    return port_group.__properties__


def get_port_groups(device_ip: str, port_group_id=None):
    """
    Retrieves the port groups for a given device IP.

    Args:
        device_ip (str): The IP address of the device.
        port_group_id (int, optional): The ID of the port group. Defaults to None.

    Returns:
        dict or list: A dictionary representing the properties of the specified port group if 'port_group_id' is provided, 
        otherwise returns a list of dictionaries representing the properties of all port groups associated with the device IP.
        Each dictionary includes the member interfaces of the port group.
    """
    if port_group_id:
        db_output = (
            port_group.__properties__
            if (port_group := get_port_group_from_db(device_ip, port_group_id))
            else None
        )
        db_output["mem_intfs"] = get_port_group_member_names_from_db(
            device_ip, db_output.get("port_group_id")
        )
        return db_output
    else:
        db_output = [
            pg.__properties__ for pg in get_port_group_from_db(device_ip) or []
        ]
        if db_output:
            for pg in db_output or []:
                pg["mem_intfs"] = get_port_group_member_names_from_db(
                    device_ip, pg.get("port_group_id")
                )
        return db_output


def discover_port_groups(
    device_ip: str = None,
    port_group_id: str = None,
    config_triggered_discovery: bool = False,
):
    
    """
    Discovers port groups for a given device IP.

    Args:
        device_ip (str): The IP address of the device.
        port_group_id (str, optional): The ID of the port group. Defaults to None.
        config_triggered_discovery (bool, optional): Flag to indicate if the discovery is triggered by configuration update. Defaults to False.

    Returns:
        None
    """
    _logger.info("Port-groups Discovery Started.")
    devices = [get_device_db_obj(device_ip)] if device_ip else get_device_db_obj()
    for device in devices:
        _logger.info("Discovering  %s of device %s.", ('portgroup %s' % port_group_id if port_group_id else 'all portgroups'), device_ip)
        insert_device_port_groups_in_db(
            device, _create_port_group_graph_objects(device.mgt_ip, port_group_id)
        )
        if config_triggered_discovery and port_group_id:
            ## if discovery is triggered due to config update via ORCA.
            ## Speed changes to port groups are also reflected in the member interfaces.
            ## Discover member interfaces of the port group as well.
            from orca_nw_lib.interface import discover_interfaces
            for mem_if in get_port_group_members(device_ip, port_group_id):
                discover_interfaces(device_ip, mem_if.get("name"))

@check_gnmi_subscription_and_apply_config
def set_port_group_speed(device_ip: str, port_group_id: str, speed: Speed):
    """
    Sets the speed of a port group on a device.

    Args:
        device_ip (str): The IP address of the device.
        port_group_id (str): The ID of the port group.
        speed (Speed): The desired speed for the port group.

    Returns:
        None
        
    Raises:
        Exception: If the speed change fails.
    """
    _logger.debug("Setting port group %s speed to %s on device %s", port_group_id, speed, device_ip)
    try:
        set_port_group_speed_on_device(device_ip, port_group_id, speed)
    except Exception as e:
        _logger.error(
            f"Port Group {port_group_id} speed change failed on device {device_ip}, Reason: {e}"
        )
        raise
    finally:
        from orca_nw_lib.interface import discover_interfaces
        for mem_if in get_port_group_members(device_ip, port_group_id):
            discover_interfaces(device_ip, mem_if.get("name"))
