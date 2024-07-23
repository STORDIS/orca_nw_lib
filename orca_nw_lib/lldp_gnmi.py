from orca_nw_lib.gnmi_pb2 import Path, PathElem
from orca_nw_lib.gnmi_util import send_gnmi_get
from orca_nw_lib.utils import get_logging
from .gnmi_util import send_gnmi_get, get_gnmi_path

_logger = get_logging().getLogger(__name__)


def get_lldp_nbr_from_device(device_ip: str, intfc_name: str = None):
    """
    Get LLDP neighbor information from a device.

    Args:
        device_ip (str): The IP address of the device.
        intfc_name (str, optional): The name of the interface. Defaults to None.

    Returns:
        The LLDP neighbor information retrieved from the device.
    """
    return send_gnmi_get(
        device_ip=device_ip,
        path=[
            get_gnmi_path(
                f"openconfig-lldp:lldp/interfaces/interface[name={intfc_name}]"
                if intfc_name
                else "openconfig-lldp:lldp/interfaces/interface"
            ),
        ],
    )


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
