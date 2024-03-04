from .device import create_device_graph_object
from .interface_db import get_interface_of_device_from_db
from .gnmi_pb2 import Path, PathElem
from .gnmi_util import send_gnmi_get
from .utils import get_logging


_logger = get_logging().getLogger(__name__)


def get_lldp_neighbors(device_ip: str):
    """
    Retrieves the LLDP neighbors of the given device.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        list: A list of dictionaries containing information about the LLDP neighbors.
              Each dictionary has the following keys:
              - local_port (str): The name of the local port.
              - nbr_ip (str): The IP address of the neighbor.
              - nbr_port (str): The name of the neighbor port.
    """
    lldp_json = get_lldp_interfaces_from_device(device_ip)
    neighbors = []
    for intfs in lldp_json.get("openconfig-lldp:interface") or []:
        local_port_name = intfs.get("name")

        if not intfs.get("neighbors") or not intfs.get("neighbors").get("neighbor"):
            ##_logger.debug(f"Can't find neighbor in {device_ip}:{local_port_name}")
            ## not all interfaces are connected, in case interface is not connected to any neighbor
            ## Just continue.
            continue

        for nbr in intfs.get("neighbors").get("neighbor") or []:
            nbr_addr = nbr.get("state").get("management-address")
            if not nbr_addr:
                _logger.error(f"can find neighbor addr in {nbr}")
                continue
            nbr_port = nbr.get("state").get("port-id")
            nbr_data = {
                "local_port": local_port_name,
                "nbr_ip": nbr_addr.split(",")[0],
                "nbr_port": nbr_port,
            }
            neighbors.append(nbr_data)
    return neighbors


def get_lldp_base_path() -> Path:
    """
    Generate the path for accessing the LLDP base in the OpenConfig model.

    Returns:
        Path: The path object representing the LLDP base path in the OpenConfig model.
    """

    return Path(
        target="openconfig",
        origin="openconfig-lldp",
        elem=[
            PathElem(
                name="lldp",
            )
        ],
    )


def get_lldp_interfaces_path() -> Path:
    """
    Generate the path for accessing the interfaces in the LLDP section of the OpenConfig model.

    Returns:
        Path: The path object representing the LLDP interfaces path in the OpenConfig model.
    """
    path = get_lldp_base_path()
    path.elem.append(PathElem(name="interfaces"))
    path.elem.append(PathElem(name="interface"))
    return path


def get_lldp_enable_path() -> Path:
    """
    Generate the path for accessing the LLDP enable in the OpenConfig model.

    Returns:
        Path: The path object representing the LLDP enable path in the OpenConfig model.
    """
    path = get_lldp_base_path()
    path.elem.append(PathElem(name="state"))
    path.elem.append(PathElem(name="enabled"))
    return path


def get_lldp_interfaces_from_device(device_ip: str):
    """
    Retrieves the LLDP interfaces from the specified device.

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        The result of the GNMI get request for the LLDP interfaces.
    """
    return send_gnmi_get(device_ip=device_ip, path=[get_lldp_interfaces_path()])


def create_lldp_relations_in_db(topology):
    """
    Creates LLDP relations in the database based on the given topology.

    Args:
        topology (dict): A dictionary representing the topology of devices and their neighbors.

    Returns:
        None
    """
    for device, neighbors in topology.items():
        for nbr in neighbors:
            nbr_device = nbr.get("nbr_device")

            local_intfc = get_interface_of_device_from_db(
                device.mgt_ip, nbr.get("local_port")
            )

            nbr_intfc = get_interface_of_device_from_db(
                nbr_device.mgt_ip, nbr.get("nbr_port")
            )
            if local_intfc and nbr_intfc:
                local_intfc.lldp_neighbour.connect(nbr_intfc)


def is_lldp_enabled(device_ip):
    """
    This function checks if LLDP (Link Layer Discovery Protocol) is enabled on a device.

    Args:
        device_ip (str): The IP address of the device to check.

    Returns:
        bool: True if LLDP is enabled on the device, False otherwise.
    """
    path_lldp_state = get_lldp_enable_path()
    try:
        response = send_gnmi_get(device_ip, path_lldp_state)
        if response is not None:
            if response.get("openconfig-lldp:enabled"):
                return True
            else:
                _logger.info(f"LLDP is disabled on {device_ip}")
                return False
        else:
            _logger.info(f"Error occurred while making request on {device_ip}.")
            return False
    except TimeoutError as e:
        raise e


def read_lldp_topo(ip: str, topology, lldp_report: list):
    """
    Generate the function comment for the given function body in a markdown code block with the correct language syntax.

    Parameters:
        ip (str): The IP address of the device.
        topology: The current topology dictionary.
        lldp_report (list): The list to store the LLDP report.

    Returns:
        None
    """

    try:
        device = create_device_graph_object(ip)
        if device not in topology:
            nbrs = []
            try:
                nbrs = get_lldp_neighbors(ip)
            except Exception as e:
                log_str = (
                    f"Neighbors of Device {ip} couldn't be discovered reason : {e}."
                )
                _logger.info(log_str)
                lldp_report.append(log_str)

            temp_arr = []
            for nbr in nbrs:
                try:
                    nbr_device = create_device_graph_object(nbr.get("nbr_ip"))

                    # Following check prevents adding an empty device object in topology.
                    # with no mgt_ip any no other properties as well.
                    # This may happen if device is pingable but gnmi connection can not be established.
                    if nbr_device.mgt_intf:
                        temp_arr.append(
                            {
                                "nbr_device": create_device_graph_object(
                                    nbr.get("nbr_ip")
                                ),
                                "nbr_port": nbr.get("nbr_port"),
                                "local_port": nbr.get("local_port"),
                            }
                        )
                except Exception as e:
                    log_str = f"Device {nbr.get('nbr_ip')} couldn't be discovered reason : {e}."
                    _logger.info(log_str)
                    lldp_report.append(log_str)

            topology[device] = temp_arr

            for nbr in nbrs or []:
                read_lldp_topo(nbr.get("nbr_ip"), topology, lldp_report)
    except Exception as e:
        log_str = f"Device {ip} couldn't be discovered reason : {e}."
        _logger.info(log_str)
        lldp_report.append(log_str)
