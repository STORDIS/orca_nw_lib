import enum
from orca_backend.device import Device, wrapper_getDeviceDetails
from orca_backend.gnmi_pb2 import Path, PathElem
from orca_backend.gnmi_util import send_gnmi_get
from orca_backend.utils import logging,settings
from orca_backend.constants import network

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
        Parses the json out of the request, 
        Sample output is in sample directory.
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

def getDeviceObject(ip_addr:str):
    device_detail=wrapper_getDeviceDetails(ip_addr)
    return Device(img_name=device_detail.get('img_name'), 
                  mgt_intf=device_detail.get('mgt_intf'), 
                  mgt_ip= device_detail.get('mgt_ip'),
                  hwsku=device_detail.get('hwsku'), 
                  mac=device_detail.get('mac'), 
                  platform=device_detail.get('platform'), 
                  type=device_detail.get('type'))
    


def read_lldp_topo(ip):   
    try:
        device=getDeviceObject(ip)
        if device not in topology.keys(): 
            nbrs=get_neighbours(ip)
            topology[device]=[getDeviceObject(nbr_ip) for nbr_ip in nbrs]
            for nbr in nbrs or []:
                read_lldp_topo(nbr)
    except Exception as te:
        _logger.info(f"Device {ip} couldn't be discovered reason : {te}.")

from orca_backend.data_graph import insert_topology_in_db


def discover_topology():
    _logger.info("Discovery Started.")
    import ipaddress
    try:
        for ip_or_nw in settings.get(network):
            ips=ipaddress.ip_network(ip_or_nw)
            for ip in ips:
                _logger.debug(f'Discovering device:{ip} and its neighbors.')
                read_lldp_topo(str(ip))
        _logger.info('Discovered topology using network provided {0}: {1}'.format(settings.get(network),topology))
    except ValueError as ve:
        _logger.error(ve)
        
    if topology:
        _logger.info("Inserting topology to database.")
        insert_topology_in_db(topology)
    return topology
    