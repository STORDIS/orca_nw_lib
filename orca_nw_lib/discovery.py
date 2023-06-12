import enum
import ipaddress
from .device import createDeviceGraphObject
from .gnmi_pb2 import Path, PathElem
from .gnmi_util import send_gnmi_get
from .interfaces import createInterfaceGraphObjects
from .mclag import createMclagGraphObjects
from .port_chnl import createPortChnlGraphObject
from .utils import logging,settings
from .constants import network

_logger=logging.getLogger(__name__)

def is_lldp_enabled(device_ip):
    path_lldp_state = Path(target='openconfig',
                           origin='openconfig-lldp', 
                           elem=[PathElem(name="lldp", ),
                                 PathElem(name="state", ),
                                 PathElem(name="enabled", ),
                                ])
    try:
        response=send_gnmi_get(device_ip,path_lldp_state)
        if response is not None:
            for key in response:
                if response.get('openconfig-lldp:enabled'):
                    return True
                else:
                    print(f'LLDP is disabled on {device_ip}')
                    return False
        else:
            _logger.info(f'Error occured while making request on {device_ip}.')
            return False
    except TimeoutError as e:
        raise e

def get_neighbours(device_ip):
    '''
        Returns a list of IP addresses of LLDP neighbors of the device_ip provided in prameters
    '''
    neighbors=[]
    #if is_lldp_enabled(device_ip):
    if 1:
        path_lldp_intfs = Path(target='openconfig',origin='openconfig-lldp', elem=[PathElem(name="lldp", ),
                                                       PathElem(name="interfaces", ),
                                                       PathElem(name="interface", ),
                                                       ])
        path_system_state = Path(target='openconfig',origin='openconfig-system', elem=[PathElem(name="system", ),
                                                       PathElem(name="state", ),
                                                       ])
        try:
            resp=send_gnmi_get(device_ip, [path_lldp_intfs,path_system_state])
            for intfs in resp.get('openconfig-lldp:interface') or []:
                if intfs.get('neighbors'):
                    for nbr in intfs.get('neighbors').get('neighbor'):
                        nbr_addr=nbr.get('state').get('management-address')
                        neighbors.append(nbr_addr.split(',')[0])
        except TimeoutError as te:
            raise te
    return neighbors

topology={}

def read_lldp_topo(ip):   
    try:
        device=createDeviceGraphObject(ip)
        if device not in topology.keys(): 
            nbrs=get_neighbours(ip)
            topology[device]=[createDeviceGraphObject(nbr_ip) for nbr_ip in nbrs]
            for nbr in nbrs or []:
                read_lldp_topo(nbr)
    except Exception as te:
        _logger.info(f"Device {ip} couldn't be discovered reason : {te}.")
        

from orca_nw_lib.graph_db_utils import clean_db, getAllDevices, insert_device_interfaces_in_db, insert_device_mclag_in_db, insert_device_port_chnl_in_db, insert_topology_in_db


def discover_port_chnl():
    _logger.info("Port Channel Discovery Started.")
    for device in getAllDevices():
        _logger.info(f'Discovering Port Channels of device {device}.')
        insert_device_port_chnl_in_db(device, createPortChnlGraphObject(device.mgt_ip))


def discover_interfaces():
    _logger.info("Interface Discovery Started.")
    for device in getAllDevices():
        _logger.info(f'Discovering interfaces of device {device}.')
        insert_device_interfaces_in_db(device, createInterfaceGraphObjects(device.mgt_ip))
        

def discover_mclag():
    _logger.info("MCLAG Discovery Started.")
    for device in getAllDevices():
        _logger.info(f'Discovering MCLAG on device {device}.')
        insert_device_mclag_in_db(device, createMclagGraphObjects(device.mgt_ip))


def discover_topology():
    _logger.info("Device Discovery Started.")
    try:
        for ip_or_nw in settings.get(network):
            ips=ipaddress.ip_network(ip_or_nw)
            for ip in ips:
                _logger.debug(f'Discovering device:{ip} and its neighbors.')
                read_lldp_topo(str(ip))
        _logger.info('Discovered topology using network provided {0}: {1}'.format(settings.get(network),topology))
    except ValueError as ve:
        _logger.error(ve)
        return False
        
    if topology:
        _logger.info("Inserting Device LLDP topology to database.")
        insert_topology_in_db(topology)
    else:
        return False
    return True
    
def discover_all():
    clean_db()
    if discover_topology():
        discover_interfaces()
        discover_port_chnl()
        discover_mclag()
        return True
    return False
    
