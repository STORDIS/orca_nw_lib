import enum
import ipaddress
from orca_nw_lib.lldp import getLLDPNeighbors

from orca_nw_lib.portgroup import createPortGroupGraphObjects
from .device import createDeviceGraphObject
from .gnmi_pb2 import Path, PathElem
from .gnmi_util import send_gnmi_get
from .interfaces import createInterfaceGraphObjects
from .mclag import createMclagGraphObjects
from .port_chnl import createPortChnlGraphObject
from .utils import get_logging, get_orca_config
from .constants import network
from .lldp import getLLDPNeighbors

_logger = get_logging().getLogger(__name__)


def is_lldp_enabled(device_ip):
    path_lldp_state = Path(
        target="openconfig",
        origin="openconfig-lldp",
        elem=[
            PathElem(
                name="lldp",
            ),
            PathElem(
                name="state",
            ),
            PathElem(
                name="enabled",
            ),
        ],
    )
    try:
        response = send_gnmi_get(device_ip, path_lldp_state)
        if response is not None:
            for key in response:
                if response.get("openconfig-lldp:enabled"):
                    return True
                else:
                    _logger.info(f"LLDP is disabled on {device_ip}")
                    return False
        else:
            _logger.info(f"Error occured while making request on {device_ip}.")
            return False
    except TimeoutError as e:
        raise e


topology = {}


def read_lldp_topo(ip):
    try:
        device = createDeviceGraphObject(ip)
        if device not in topology.keys():
            nbrs = getLLDPNeighbors(ip)
            topology[device] = [
                {
                    "nbr_device": createDeviceGraphObject(nbr.get("nbr_ip")),
                    "nbr_port": nbr.get("nbr_port"),
                    "local_port": nbr.get("local_port"),
                }
                for nbr in nbrs
            ]
            for nbr in nbrs or []:
                read_lldp_topo(nbr.get("nbr_ip"))
    except Exception as te:
        _logger.info(f"Device {ip} couldn't be discovered reason : {te}.")


from orca_nw_lib.graph_db_utils import (
    clean_db,
    create_lldp_relations,
    create_mclag_peerlink_relations,
    getAllDevices,
    insert_device_interfaces_in_db,
    insert_device_mclag_in_db,
    insert_device_port_chnl_in_db,
    insert_device_port_groups_in_db,
    insert_topology_in_db,
)


def discover_port_chnl():
    _logger.info("Port Channel Discovery Started.")
    for device in getAllDevices():
        _logger.info(f"Discovering Port Channels of device {device}.")
        insert_device_port_chnl_in_db(device, createPortChnlGraphObject(device.mgt_ip))


def discover_interfaces():
    _logger.info("Interface Discovery Started.")
    for device in getAllDevices():
        _logger.info(f"Discovering interfaces of device {device}.")
        insert_device_interfaces_in_db(
            device, createInterfaceGraphObjects(device.mgt_ip)
        )


def discover_port_groups():
    _logger.info("Port-groups Discovery Started.")
    for device in getAllDevices():
        _logger.info(f"Discovering port-groups of device {device}.")
        insert_device_port_groups_in_db(
            device, createPortGroupGraphObjects(device.mgt_ip)
        )


def discover_mclag():
    _logger.info("MCLAG Discovery Started.")
    for device in getAllDevices():
        _logger.info(f"Discovering MCLAG on device {device}.")
        insert_device_mclag_in_db(device, createMclagGraphObjects(device.mgt_ip))


def discover_topology():
    _logger.info(
        "Network Discovery Started using network provided {0}".format(
            get_orca_config().get(network)
        )
    )
    try:
        for ip_or_nw in get_orca_config().get(network):
            ips = ipaddress.ip_network(ip_or_nw)
            for ip in ips:
                _logger.debug(f"Discovering device:{ip} and its neighbors.")
                read_lldp_topo(str(ip))
        _logger.info(
            "Discovered topology using network provided {0}: {1}".format(
                get_orca_config().get(network), topology
            )
        )
    except ValueError as ve:
        _logger.error(ve)
        return False

    if topology:
        _logger.info("Inserting Device LLDP topology to database.")
        insert_topology_in_db(topology)
    else:
        return False
    return True


def create_lldp_rel():
    _logger.info("Creating LLDP relations.")
    create_lldp_relations(topology)

def create_mclag_peer_link_rel():
    _logger.info("Creating MCLAG peer-link relations.")
    create_mclag_peerlink_relations()

def discover_all():
    clean_db()
    if discover_topology():
        discover_interfaces()
        create_lldp_rel()
        discover_port_chnl()
        discover_mclag()
        create_mclag_peer_link_rel()
        discover_port_groups()
        return True
    return False
