import json
from neo4j import GraphDatabase
from discovery.processor.sonic_grpc import logging

from discovery.processor.utils import settings
from discovery.processor.constants import neo4j_url, neo4j_password,neo4j_user  
_logger=logging.getLogger(__name__)

driver = GraphDatabase.driver(settings.get(neo4j_url), 
                                  auth=(settings.get(neo4j_user),settings.get(neo4j_password)))
session=driver.session()

def switch_present_in_db(tx,switch_ip):
    op=tx.run("MATCH (s:Switch) WHERE s.ip = $switch_ip return s",switch_ip=switch_ip)
    for o in op:
        if o.data().get('s').get('ip') == switch_ip:
            return True
    return False
     

def clean_db(tx):
    tx.run("MATCH (s) DETACH DELETE s")


def create_switch(tx, switch_ip):
    tx.run("CREATE (s:Switch {ip: $ip})", ip=switch_ip)
    
def create_switch_with_rel(tx, switch_ip,nbr):#
     tx.run("MATCH (s:Switch) WHERE s.ip = $ip "
                "CREATE (s)-[:LLDP]->(:Switch {ip: $nbr})",
                ip=switch_ip, nbr=nbr)
     
def create_rel(tx,from_switch_ip,to_switch_ip):
    tx.run('MATCH (f:Switch {ip:$from_switch_ip}) ,(t:Switch {ip:$to_switch_ip}) MERGE (f)-[:LLDP]->(t)'
           ,from_switch_ip=from_switch_ip,to_switch_ip=to_switch_ip)
    
    
def insert_topology_in_db(topology):
    driver.session().execute_write(clean_db)
    for switch_ip,neighbors in topology.items():
        if not session.execute_read(switch_present_in_db,switch_ip):
            driver.session().execute_write(create_switch,switch_ip)
        #create its neighbor
        for nbr in neighbors:
            if not session.execute_read(switch_present_in_db,nbr):
               driver.session().execute_write(create_switch_with_rel,switch_ip,nbr)
            driver.session().execute_write(create_rel,switch_ip,nbr)    
