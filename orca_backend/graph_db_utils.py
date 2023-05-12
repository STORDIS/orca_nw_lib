import json
from neo4j import GraphDatabase
from orca_backend.graph_db_models import Device

from orca_backend.utils import settings, logging
from orca_backend.constants import neo4j_url, neo4j_password,neo4j_user,protocol

from neomodel import config,db,clear_neo4j_database,StructuredNode, StringProperty, IntegerProperty,  UniqueIdProperty, RelationshipTo
config.DATABASE_URL=f'{settings.get(protocol)}://{settings.get(neo4j_user)}:{settings.get(neo4j_password)}@{settings.get(neo4j_url)}'

_logger=logging.getLogger(__name__)

def insert_topology_in_db(topology):
    for device,neighbors in topology.items():
        if Device.nodes.get_or_none(mac=device.mac) is None: 
            device.save()
        #create its neighbor
        for nbr in neighbors:
            if Device.nodes.get_or_none(mac=nbr.mac) is None:
                nbr.save()
            Device.nodes.get(mac=device.mac).neighbor.connect(Device.nodes.get(mac=nbr.mac))

def clean_db():
   clear_neo4j_database(db) 
   
def getAllDevices():
    return Device.nodes.all()

   


