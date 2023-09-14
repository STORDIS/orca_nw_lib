# ORCA Network Library
ORCA Network Library is a python package to facilitate CRUD operations on SONiC devices using gNMI interface. orca_nw_lib maintains a graph database with the realtime device configurations and network topology.
ORCA Network Library can be used to develop the orchestration solutions, NMS applications,  newtwork data analytics  
- [ORCA Network Library](#orca-network-library)
  - [Build and Install orca\_nw\_lib](#build-and-install-orca_nw_lib)
  - [orca\_nw\_lib configuration](#orca_nw_lib-configuration)
  - [Install Neo4j](#install-neo4j)
  - [Using the ORCA APIs](#using-the-orca-apis)
  - [Executing Tests](#executing-tests)
  - [Supported SONiC versions](#supported-sonic-versions)

## Build and Install orca_nw_lib 

    cd orca_nw_lib
    poetry build
    pip install dist/orca_nw_lib-****.whl

>**Note** - Poetry, Python3 and pip must be pre installed.


## orca_nw_lib configuration
[orca.yml](orca_nw_lib/orca.yml) file contains all necessary configuration parameters required by orca_nw_lib. parameters are described in the file itself. [orca.yml](orca_nw_lib/orca.yml) is read by default by the function get_orca_config in [utils.py](orca_nw_lib/utils.py), Although applications can call get_orca_config with custom config files keeping same structure. \
[logging.yml](orca_nw_lib/logging.yml) contains logging configuration. [logging.yml](orca_nw_lib/logging.yml) is read by default by the function get_logging in [utils.py](orca_nw_lib/utils.py), Although applications can call get_logging with custom logging config files keeping same structure.


## Install Neo4j
Easiest to install neo4j is to run in container with the following command :
        
    docker run \
        --name testneo4j \
        -p7474:7474 -p7687:7687 \
        -d \
        -v $HOME/neo4j/data:/data \
        -v $HOME/neo4j/logs:/logs \
        -v $HOME/neo4j/import:/var/lib/neo4j/import \
        -v $HOME/neo4j/plugins:/plugins \
        --env NEO4J_AUTH=neo4j/password \
        neo4j:latest
Then open https://localhost:7474 with credentials neo4j/password to browse the database.


## Using the ORCA APIs
For normal usage following APIs in python modules in the package [orca_nw_lib](orca_nw_lib) are useful -\
[discovery.py](orca_nw_lib/discovery.py) - discover_all() function can be used to discover complete topology as per the network defined in orca.yml\
[bgp.py](orca_nw_lib/bgp.py) - BGP CRUD operations\
[device.py] (orca_nw_lib/device.py) - Get device system info.\
[interface.py](orca_nw_lib/interface.py) - Interfaces CRUD operations.\
[lldp.py](orca_nw_lib/lldp.py) - Read LLDP relation, usefull while doing discovery.\
[mclag.py](orca_nw_lib/mclag.py) - MCLAG CRUD operations.\
[port_chnl.py](orca_nw_lib/port_chnl.py) - Port Channel CRUD operations.\
[portgroup.py](orca_nw_lib/portgroup.py) - Read port group information.\
[vlan.py](orca_nw_lib/vlan.py) - VLAN CRUD operations.

There are modules having suffixes _db and _gnmi, they contain operations to be performed in db or on device using gNMI respectively.\
e.g. interface.py have general operation on interfaces and users can achieve normal interface configurations by using functions present in interface.py, on the other hand interface_db.py has function to perform CRUD operations in graph DB and interface_gnmi.py has function to configure interfaces on device.

## Executing Tests
Test cases are located under [test](./orca_nw_lib/test) directory.\
Example:
- To execute tests
  
        pytest orca_nw_lib/test/test_network.py

- To execute single test cases 
  
        pytest orca_nw_lib/test/test_network.py -k test_remove_port_chnl_members

- To print console messages from code 
  
        pytest orca_nw_lib/test/test_interface.py -k test_remove_port_chnl_members -s

## Supported SONiC versions
- Broadcom Enterprise SONiC (Latest tested on 4.0.5)