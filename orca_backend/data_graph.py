import json
from neo4j import GraphDatabase
from orca_backend.device import Device

from orca_backend.utils import settings, logging
from orca_backend.constants import neo4j_url, neo4j_password,neo4j_user  
_logger=logging.getLogger(__name__)

db_session=None
def get_db_session():
    global db_session
    if db_session is None:
        db_session = GraphDatabase.driver(settings.get(neo4j_url), 
                                  auth=(settings.get(neo4j_user),settings.get(neo4j_password))).session()
    return db_session

def switch_present_in_db(tx,device:Device):
    op=tx.run("MATCH (s:Switch) WHERE s.mac = $device_mac return s",device_mac=device.mac)
    for o in op:
        if o.data().get('s').get('mac') == device.mac:
            return True
    return False
     

def clean_db(tx):
    tx.run("MATCH (s) DETACH DELETE s")


def create_switch(tx, device: Device):
    tx.run("CREATE (s:Switch {img_name: $img_name,mgt_intf:$mgt_intf, mgt_ip:$mgt_ip, hwsku:$hwsku,mac:$mac,platform:$platform,type:$type})",
           img_name=device.img_name, mgt_intf=device.mgt_intf, mgt_ip=device.mgt_ip, hwsku=device.hwsku, mac=device.mac, platform=device.platform, type=device.type)


def create_switch_with_rel(tx, device:Device, nbr:Device):
    tx.run("MATCH (s:Switch) WHERE s.mac = $mac "
           "CREATE (s)-[:LLDP]->(:Switch {img_name: $img_name,mgt_intf:$mgt_intf, mgt_ip:$mgt_ip, hwsku:$hwsku,mac:$nbr_mac,platform:$platform,type:$type})",
           mac=device.mac, img_name=nbr.img_name, mgt_intf=nbr.mgt_intf, mgt_ip=nbr.mgt_ip, hwsku=nbr.hwsku, nbr_mac=nbr.mac, platform=nbr.platform, type=nbr.type)
     
def create_rel(tx,from_switch:Device,to_switch:Device):
    tx.run('MATCH (f:Switch {mac:$from_switch_mac}) ,(t:Switch {mac:$to_switch_mac}) MERGE (f)-[:LLDP]->(t)'
           ,from_switch_mac=from_switch.mac,to_switch_mac=to_switch.mac)
    
    
def insert_topology_in_db(topology):
    #Clean up all Database
    get_db_session().execute_write(clean_db)
    #Iterate topo dictionary for each device and its neighbor devices
    for device,neighbors in topology.items():
        # Check if device is already present in DB, Check is useful when some devices are already created as a result of code at the bottom
        # because they are neighbors to this device but have also neighbors.
        if not get_db_session().execute_read(switch_present_in_db, device):
             get_db_session().execute_write(create_switch,device)
        #create its neighbor
        for nbr in neighbors:
            if not get_db_session().execute_read(switch_present_in_db,nbr):
               get_db_session().execute_write(create_switch_with_rel,device,nbr)
            ## Device is present in database, but only a relation needs to be created   
            get_db_session().execute_write(create_rel,device,nbr)    
