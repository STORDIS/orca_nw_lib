import enum
import json
import re
import ssl
import sys
from typing import List

import grpc
from orca_backend.gnmi_pb2 import JSON, CapabilityRequest, GetRequest, Path, PathElem, JSON_IETF, SetRequest, TypedValue, Update
from orca_backend.gnmi_pb2_grpc import gNMIStub
from orca_backend.utils import settings, logging
from orca_backend.constants import device_ip,grpc_port, username,password,conn_timeout
_logger=logging.getLogger(__name__)

stubs={}
def getGrpcStubs(device_ip,grpc_port=settings.get(grpc_port),
                 username=settings.get(username),password=settings.get(password)):
    global stubs
    if stubs and stubs.get(device_ip):
        return stubs.get(device_ip)
    else:
        try:
            sw_cert = ssl.get_server_certificate((device_ip, grpc_port),timeout=settings.get(conn_timeout)).encode("utf-8")
            # Option 1
            #creds = grpc.ssl_channel_credentials(root_certificates=sw_cert)
            #stub.Get(GetRequest(path=[path], type=GetRequest.ALL, encoding=JSON_IETF),
            #        metadata=[("username", user),
            #                  ("password", passwd)], )

            #Option 2, In this case need not to send user/pass in metadata in get request.
            def auth_plugin(context, callback):
                callback([("username", username), ("password", password)], None)
            creds = grpc.composite_channel_credentials(
            grpc.ssl_channel_credentials(root_certificates=sw_cert),
            grpc.metadata_call_credentials(auth_plugin),
            )

            optns = (("grpc.ssl_target_name_override", "localhost"),)
            channel = grpc.secure_channel(f"{device_ip}:{grpc_port}", creds, options=optns)
            stub = gNMIStub(channel)
            stubs[device_ip] = stub
            return stub
        except TimeoutError as te:
            raise te
        except ConnectionRefusedError as cr:
            _logger.error(f"Connection refused by {device_ip}")
       
    

def send_gnmi_get(device_ip,path:list[Path]):
    op={}
    try:
        device_gnmi_stub=getGrpcStubs(device_ip)
        try:
            resp = device_gnmi_stub.Get(GetRequest(path=path, 
                                                type=GetRequest.ALL, 
                                                encoding=JSON_IETF),timeout=settings.get(conn_timeout)) if device_gnmi_stub else _logger.error(f"no gnmi stub found for device {device_ip}")
            #resp_cap=device_gnmi_stub.Capabilities(CapabilityRequest())
            #print(resp_cap)
            for u in resp.notification[0].update :
                op = u.val.json_ietf_val.decode("utf-8")
                op = json.loads(op)
        except Exception as e:
            _logger.error(f"{e} \n {path}")
        
    except TimeoutError as e:
        #_logger.error(f"Failed to get server certificate for device {device_ip} {e}")
        raise e
    return op


def get_gnmi_update_req(path:Path, val:dict):
    update=Update(path=path,val=TypedValue(json_ietf_val=bytes(json.dumps(val),"utf-8")))
    return SetRequest(update=[update])


def get_gnmi_del_req(path:Path):
    return SetRequest(delete=[path])


def send_gnmi_set(req:SetRequest, device_ip:str):
    resp=""
    try:
        device_gnmi_stub=getGrpcStubs(device_ip)
        try:
            resp = device_gnmi_stub.Set(req,timeout=settings.get(conn_timeout)) if device_gnmi_stub else _logger.error(f"no gnmi stub found for device {device_ip}")
        except Exception as e:
            _logger.error(e)
        
    except TimeoutError as e:
        #_logger.error(f"Failed to get server certificate for device {device_ip} {e}")
        _logger.error(e)
    return resp



def create_gnmi_path(path_arr:List[str])->List[Path]:
    '''Returns a list of gnmi path object create from string formated path array'''
    paths=[]
    for path in path_arr:
        gnmi_path = Path()

        path_elements = path.split('/')
        print(path_elements)

        for pe_entry in path_elements:
            if not re.match('.+?:.+?', pe_entry) and len(path_elements) == 1:
                sys.exit(f'You haven\'t specified either YANG module or the top-level container in \'{pe_entry}\'.')

            elif re.match('.+?:.+?', pe_entry):
                gnmi_path.origin = pe_entry.split(':')[0]
                gnmi_path.elem.add(name=pe_entry.split(':')[1])

            elif re.match('.+?\[.+?\]', pe_entry):
                gnmi_path.elem.add(name=pe_entry.split('[')[0], key={f'{pe_entry.split("[")[1].split("=")[0]}': f'{re.sub("]", "", pe_entry.split("[")[1].split("=")[1])}'})

            else:
                gnmi_path.elem.add(name=pe_entry)
            paths.append(gnmi_path)
    return paths


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

class discovery_status(enum.Enum):
    running=1
    completed=2
    never_ran=2

def read_lldp_topo(ip):
    #discovered_devices.add(ip)
    if ip not in topology.keys(): 
        try:
            nbrs=get_neighbours(ip)
            topology[ip]=nbrs
            for nbr in nbrs or []:
                read_lldp_topo(nbr)
        except TimeoutError as te:
            _logger.info(f"Device {ip} couldn't be discovered reason : {te}.")

from orca_backend.data_graph import insert_topology_in_db

def discover_topology():
    _logger.info("Discovery Started.")
    
    import ipaddress
    ip_or_nw=settings.get(device_ip)
    try:
        ips=ipaddress.ip_network(ip_or_nw)
        for ip in ips:
            read_lldp_topo(str(ip))
        _logger.info('Discovered topology using {0}: {1}'.format(ip_or_nw,topology))
    except ValueError as ve:
        _logger.error(ve)
    insert_topology_in_db(topology)
    return topology
    