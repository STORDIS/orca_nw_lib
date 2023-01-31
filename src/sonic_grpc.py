import json
import re
import ssl
import sys
from typing import List

import grpc

from gnmi_pb2 import GetRequest, Path, PathElem
from gnmi_pb2_grpc import gNMIStub
from gnmi_pb2 import JSON_IETF
from src import logging
from utils import settings
from constants import device_ip,grpc_port, username,password
_logger=logging.getLogger(__name__)

stubs={}
def getGrpcStubs(device_ip,grpc_port=settings.get(grpc_port),
                 username=settings.get(username),password=settings.get(password)):
    if stubs and stubs.get(device_ip):
        return stubs.get(device_ip)
    else:
        sw_cert = ssl.get_server_certificate((device_ip, grpc_port)).encode("utf-8")

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
    

def send_gnmi_get(device_ip,path:Path):
    device_gnmi_stub=getGrpcStubs(device_ip)
    op={}
    try:
        resp = device_gnmi_stub.Get(GetRequest(path=[path], type=GetRequest.ALL, encoding=JSON_IETF),) if device_gnmi_stub else _logger.error(f"no gnmi stub found for device {device_ip}")
        for u in resp.notification[0].update :
            op = u.val.json_ietf_val.decode("utf-8")
            op = json.loads(op)
    except Exception as e:
        _logger.error(f"{e} \n {path}")
    return op



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
            path.append(gnmi_path)
    return paths


def is_lldp_enabled(device_ip):
    path_lldp_state = Path(target='openconfig',
                           origin='openconfig-lldp', 
                           elem=[PathElem(name="lldp", ),
                                 PathElem(name="state", ),
                                 PathElem(name="enabled", ),
                                ])
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
        resp=send_gnmi_get(device_ip, path_lldp_intfs)

        for intfs in resp.get('openconfig-lldp:interface') or []:
            if intfs.get('neighbors'):
                for nbr in intfs.get('neighbors').get('neighbor'):
                    nbr_addr=nbr.get('state').get('management-address')
                    neighbors.append(nbr_addr.split(',')[0])
    return neighbors

#topology={'10.10.130.144': ['10.10.130.15', '10.10.130.13'], 
#          '10.10.130.15': ['10.10.130.13', '10.10.130.14', '10.10.130.144'], 
#          '10.10.130.13': ['10.10.130.15', '10.10.130.144'], 
#          '10.10.130.14': ['10.10.130.15']}
topology={}
def create_lldp_topo(ip):
    #discovered_devices.add(ip)
    if ip not in topology.keys(): 
        nbrs=get_neighbours(ip)
        topology[ip]=nbrs
        for nbr in nbrs or []:
            create_lldp_topo(nbr)
            
create_lldp_topo(settings.get(device_ip))
print(topology)

from data_graph import insert_topology_in_db
insert_topology_in_db(topology)

