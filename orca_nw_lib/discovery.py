import ipaddress

from .mclag import discover_mclag, discover_mclag_gw_macs
from .mclag_db import create_mclag_peer_link_rel

from .port_chnl import discover_port_chnl
from .vlan import discover_vlan
from .bgp import connect_bgp_peers, createBGPGraphObjects, insert_device_bgp_in_db
from .device import createDeviceGraphObject, getDeviceFromDB
from .graph_db_models import Device
from .interfaces import insert_device_interfaces_in_db, createInterfaceGraphObjects
from .lldp import create_lldp_relations_in_db, getLLDPNeighbors
from .portgroup import createPortGroupGraphObjects, insert_device_port_groups_in_db
from .utils import get_logging, get_orca_config
from .constants import network


_logger = get_logging().getLogger(__name__)


topology = {}


def read_lldp_topo(ip):
    try:
        device = createDeviceGraphObject(ip)
        if device not in topology.keys():
            nbrs = getLLDPNeighbors(ip)
            temp_arr = []
            for nbr in nbrs:
                nbr_device = createDeviceGraphObject(nbr.get("nbr_ip"))
                # Following check prevents adding an empty device object in topology.
                # with no mgt_ip any no other properties as well.
                # This may happen if device is pingable but gnmi connection can not be established.
                if nbr_device.mgt_intf and nbr_device.mgt_intf:
                    temp_arr.append(
                        {
                            "nbr_device": createDeviceGraphObject(nbr.get("nbr_ip")),
                            "nbr_port": nbr.get("nbr_port"),
                            "local_port": nbr.get("local_port"),
                        }
                    )

            topology[device] = temp_arr

            for nbr in nbrs or []:
                read_lldp_topo(nbr.get("nbr_ip"))
    except Exception as te:
        _logger.info(f"Device {ip} couldn't be discovered reason : {te}.")


def discover_interfaces():
    _logger.info("Interface Discovery Started.")
    for device in getDeviceFromDB():
        _logger.info(f"Discovering interfaces of device {device}.")
        insert_device_interfaces_in_db(
            device, createInterfaceGraphObjects(device.mgt_ip)
        )


def discover_port_groups():
    _logger.info("Port-groups Discovery Started.")
    for device in getDeviceFromDB():
        _logger.info(f"Discovering port-groups of device {device}.")
        insert_device_port_groups_in_db(
            device, createPortGroupGraphObjects(device.mgt_ip)
        )


def insert_topology_in_db(topology):
    for device, neighbors in topology.items():
        if Device.nodes.get_or_none(mac=device.mac) is None:
            device.save()
        # create its neighbor
        for nbr in neighbors:
            nbr_device = nbr.get("nbr_device")
            if Device.nodes.get_or_none(mac=nbr_device.mac) is None:
                nbr_device.save()


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
        import pprint

        _logger.info(
            "Discovered topology using network provided {0}: \n{1}".format(
                get_orca_config().get(network), pprint.pformat(topology)
            )
        )
        _logger.info(f"Total devices discovered:{len(topology)}")

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
    _logger.info("Discovering LLDP relations.")
    create_lldp_relations_in_db(topology)


def discover_bgp():
    _logger.info("Discovering BGP Global List.")
    for device in getDeviceFromDB():
        _logger.info(f"Discovering BGP on device {device}.")
        insert_device_bgp_in_db(device, createBGPGraphObjects(device.mgt_ip))


def create_bgp_peer_link_rel():
    _logger.info("Discovering BGP neighbor relations.")
    connect_bgp_peers()


def discover_all():
    # clean_db()
    global topology
    topology = {}
    if discover_topology():
        discover_interfaces()
        discover_port_groups()
        discover_vlan()
        create_lldp_rel()
        discover_port_chnl()
        discover_mclag()
        discover_mclag_gw_macs()
        discover_bgp()
        create_bgp_peer_link_rel()

        _logger.info(f"!! Discovered successfully {len(topology)} Devices !!")
        return True
    _logger.info("!! Discovery was Unsuccessful !!")
    return False
