import requests
from src import logging
from utils import settings
requests.packages.urllib3.disable_warnings()

_logger=logging.getLogger(__name__)

def send_get_request(data_url,device_ip):
    base_url=f'https://{device_ip}/restconf/data/'
    return requests.get(f'{base_url}/{data_url}',auth=('admin', 'YourPaSsWoRd'), verify=False)


def is_lldp_enabled(device_ip):
    response= send_get_request('openconfig-lldp:lldp/config/enabled',device_ip)
    if response.ok and response is not None:
        response=response.json()
        for key in response:
            if(key == 'ietf-restconf:errors'):
                print(f'Error occured while making restconf request {response.url}')
            else:
                if response.get('openconfig-lldp:enabled'):
                    print('LLDP is enabled')
                    return True
                else:
                    print('LLDP is disabled')
                    return False
    else:
        #print(f'Error occured while making request {response.url} -> {response.status_code}:{response.reason}')
        _logger.info(f'Error occured while making request {response.url} -> {response.status_code}:{response.reason}')
        return False

def get_neighbours(device_ip):
    '''
        Parses the json out of the request, 
        Sample output is in sample directory.
    '''
    neighbours=[]
    if is_lldp_enabled(device_ip):
        resp=send_get_request('openconfig-lldp:lldp',device_ip).json()
        for intfs in resp.get('openconfig-lldp:lldp').get('interfaces').get('interface'):
            if intfs.get('neighbors'):
                for nbr in intfs.get('neighbors').get('neighbor'):
                    nbr_addr=nbr.get('state').get('management-address')
                    neighbours.append(nbr_addr.split(',')[0])
    return neighbours

#discovered_devices=set()
topology=[]
def discover_nbr(ip):
    #discovered_devices.add(ip)
    nbrs=get_neighbours(ip)
    for nbr in nbrs or []:
        #if not nbr in discovered_devices : 
        if not {ip:nbr} in topology : #prevent infinite looping
            topology.append({ip:nbr})#Add mapping to neo4j
            discover_nbr(nbr)

discover_nbr(settings.get('device_ip'))
#print('*****devices**** %s',discovered_devices)
print('*****topology****%s',topology)
