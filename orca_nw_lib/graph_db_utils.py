from orca_nw_lib.graph_db_models import Device, PortChannel, PortGroup
from orca_nw_lib.graph_db_models import Interface

from orca_nw_lib.utils import get_orca_config, get_logging
from orca_nw_lib.constants import neo4j_url, neo4j_password, neo4j_user, protocol

from neomodel import (
    config,
    db,
    clear_neo4j_database,
    Traversal,
    OUTGOING
)

config.DATABASE_URL = f"{get_orca_config().get(protocol)}://{get_orca_config().get(neo4j_user)}:{get_orca_config().get(neo4j_password)}@{get_orca_config().get(neo4j_url)}"

_logger = get_logging().getLogger(__name__)


def insert_topology_in_db(topology):
    for device, neighbors in topology.items():
        if Device.nodes.get_or_none(mac=device.mac) is None:
            device.save()
        # create its neighbor
        for nbr in neighbors:
            if Device.nodes.get_or_none(mac=nbr.mac) is None:
                nbr.save()
            Device.nodes.get(mac=device.mac).neighbor.connect(
                Device.nodes.get(mac=nbr.mac)
            )


def insert_device_interfaces_in_db(device: Device, interfaces: dict):
    for intfc, sub_intfc in interfaces.items():
        intfc.save()
        device.interfaces.connect(intfc)
        for sub_i in sub_intfc:
            sub_i.save()
            intfc.subInterfaces.connect(sub_i)


def insert_device_port_groups_in_db(device: Device=None, port_groups: dict=None):
    for pg, mem_intfcs in port_groups.items():
        pg.save()
        device.port_groups.connect(pg)
        for if_name in mem_intfcs:
            intf = getInterfaceOfDevice(device.mgt_ip, if_name)
            if intf:
                pg.memberInterfaces.connect(intf) 



def insert_device_mclag_in_db(device: Device, mclag_to_intfc_list):
    for mclag, intfcs in mclag_to_intfc_list.items():
        mclag.save()
        device.mclags.connect(mclag)
        for intf_name in intfcs:
            intf_obj = getInterfaceOfDevice(device.mgt_ip, intf_name)
            if intf_obj:
                mclag.intfc_members.connect(intf_obj)
            port_chnl_obj = getPortChnlOfDevice(device.mgt_ip, intf_name)
            if port_chnl_obj:
                mclag.portChnl_member.connect(port_chnl_obj)


def insert_device_port_chnl_in_db(device: Device, portchnl_to_mem_list):
    for chnl, mem_list in portchnl_to_mem_list.items():
        chnl.save()
        device.port_chnl.connect(chnl)
        for intf_name in mem_list:
            intf_obj = getInterfaceOfDevice(device.mgt_ip, intf_name)
            if intf_obj:
                chnl.members.connect(intf_obj)


def clean_db():
    clear_neo4j_database(db)


def getAllDevices():
    return Device.nodes.all()


def getAllDevicesIP():
    return [ device.mgt_ip for device in Device.nodes.all()]


def getDevice(mgt_ip: str):
    return Device.nodes.get_or_none(mgt_ip=mgt_ip)


def getAllInterfacesOfDevice(device_ip: str):
    device = getDevice(device_ip)
    return device.interfaces.all() if device else None


def getAllPortGroupsOfDevice(device_ip: str):
    device:Device = getDevice(device_ip)
    return device.port_groups.all() if device else None

def getPortGroupIDOfDeviceInterface(device_ip: str,inertface_name:str):
    ## TODO: Following query certainly has scope of performance enhancement.
    for pg in getAllPortGroupsOfDevice(device_ip):
        for intf in pg.memberInterfaces.all():
            if intf.name == inertface_name:
                return pg.port_group_id
    return None


def getAllInterfacesNameOfDevice(device_ip: str):
    intfcs = getAllInterfacesOfDevice(device_ip)
    return [intfc.name for intfc in intfcs] if intfcs else None


def getInterfaceOfDevice(device_ip: str, interface_name: str) -> Interface:
    device = getDevice(device_ip)
    return (
        getDevice(device_ip).interfaces.get_or_none(name=interface_name)
        if device
        else None
    )


def getAllPortChnlOfDevice(device_ip: str):
    device = getDevice(device_ip)
    return getDevice(device_ip).port_chnl.all() if device else None


def getPortChnlOfDevice(device_ip: str, port_chnl_name: str) -> PortChannel:
    device = getDevice(device_ip)
    return (
        getDevice(device_ip).port_chnl.get_or_none(lag_name=port_chnl_name)
        if device
        else None
    )


def getAllMCLAGsDevice(device_ip: str):
    device = getDevice(device_ip)
    return getDevice(device_ip).mclags.all() if device else None


def getMCLAGOfDevice(device_ip: str, domain_id: str) -> PortChannel:
    device = getDevice(device_ip)
    return (
        getDevice(device_ip).mclags.get_or_none(domain_id=domain_id) if device else None
    )
