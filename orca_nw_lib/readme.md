# ORCA Network Library
ORCA Network Library is an open sourcepython package to facilitate CRUD operations on SONiC devices using gNMI interface. orca_nw_lib maintains a graph database with the realtime device configurations and network topology.
ORCA Network Library can be used to develop the orchestration solutions, NMS applications,  newtwork data analytics.  
- [ORCA Network Library](#orca-network-library)
  - [Install Neo4j (Prerequisite)](#install-neo4j-prerequisite)
  - [Install orca\_nw\_lib using pip](#install-orca_nw_lib-using-pip)
  - [Build and Install orca\_nw\_lib from source](#build-and-install-orca_nw_lib-from-source)
  - [orca\_nw\_lib configuration](#orca_nw_lib-configuration)
  - [Using the ORCA Network APIs](#using-the-orca-network-apis)
  - [Knowing API call status](#knowing-api-call-status)
  - [Keeping graph DB in sync with realtime Network state.](#keeping-graph-db-in-sync-with-realtime-network-state)
  - [Executing Tests](#executing-tests)
  - [Releases of orca\_nw\_lib](#releases-of-orca_nw_lib)
  - [Supported SONiC versions](#supported-sonic-versions)
  - [Contribute](#contribute)

## Install Neo4j (Prerequisite)
orca_nw_lib uses neo4j to store the network topology. To install neo4j easiest is to run in container with the following command :
        
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

## Install orca_nw_lib using pip
Latest release of ORCA Network Library can be simply installed using pip as follows :
        
    pip install orca_nw_lib

## Build and Install orca_nw_lib from source
ORCA Network Library uses poetry to build the orca_nw_lib package. As a pre-requisite poetry must be installed. Poetry can be easily installed using the following command :
        
    pip install poetry

To build orca_nw_lib use the following commands :

    cd orca_nw_lib
    poetry build
    pip install dist/orca_nw_lib-****.whl

Once installed the orca_nw_lib package, orca_nw_lib can be used like any other python package in your application.

## orca_nw_lib configuration
[orca.yml](orca_nw_lib/orca.yml) file contains all necessary configuration parameters required by orca_nw_lib. parameters are described in the file itself. [orca.yml](orca_nw_lib/orca.yml) is read by default by the function get_orca_config in [utils.py](orca_nw_lib/utils.py), Although applications can call get_orca_config with custom config files keeping same structure. \
\
[logging.yml](orca_nw_lib/logging.yml) contains logging configuration. [logging.yml](orca_nw_lib/logging.yml) is read by default by the function get_logging in [utils.py](orca_nw_lib/utils.py), Although applications can call get_logging with custom logging config files keeping same structure.


## Using the ORCA Network APIs
For normal usage following APIs in python modules in the package [orca_nw_lib](orca_nw_lib) are useful -\
[discovery.py](orca_nw_lib/discovery.py) - discover_all() function can be used to discover complete topology as per the network defined in orca.yml\
[bgp.py](orca_nw_lib/bgp.py) - BGP CRUD operations\
[device.py](orca_nw_lib/device.py) - Get device system info.\
[interface.py](orca_nw_lib/interface.py) - Interfaces CRUD operations.\
[lldp.py](orca_nw_lib/lldp.py) - Read LLDP relation, usefull while doing discovery.\
[mclag.py](orca_nw_lib/mclag.py) - MCLAG CRUD operations.\
[port_chnl.py](orca_nw_lib/port_chnl.py) - Port Channel CRUD operations.\
[portgroup.py](orca_nw_lib/portgroup.py) - Read port group information.\
[vlan.py](orca_nw_lib/vlan.py) - VLAN CRUD operations.

There are modules having suffixes _db and _gnmi, they contain operations to be performed in db or on device using gNMI respectively.\
e.g. interface.py have general operation on interfaces and users can achieve normal interface configurations by using functions present in interface.py, on the other hand interface_db.py has function to perform CRUD operations in graph DB and interface_gnmi.py has function to configure interfaces on device.
> [Test cases](./test) are a good starting point to know the usage of APIs in orca_nbw_lib.

## Knowing API call status
Exception (grpc._channel._InactiveRpcError) raised by APIs in the modules above can be caught to know the API status. Exception object has all necessary details about the error.

## Keeping graph DB in sync with realtime Network state.
gNMI subscription would have been the best way to achieve this, but due lack of support for gNMI subscription for all openconfig models in SONiC orca_nw_lib used the pull mechanism to keep graph DB in sync with realtime network state.

For every write operation performed the API triggers the discovery of that network component.
> NOTE :  To keep graph DB up to date with the changes done out side of application which uses orca_nw_lib i.e. changes done directly on the device, a recurring call to discover_all() should be performed by the application.


## Executing Tests
Test cases are located under [test](./orca_nw_lib/test) directory. To execute tests a topology of 3 switches (1-spine, 2-leaves) is required. Prior to execute tests leaves should be connected to spine and respective interfaces should be enabled , so that by providing one of the switch IP in [orca.yml](./orca_nw_lib/orca.yml) whole topology gets discovered.\
For performing tests creating a topology in GNS3 can be a good starting point.

- To execute tests
  
        pytest orca_nw_lib/test/test_network.py

- To execute single test cases 
  
        pytest orca_nw_lib/test/test_network.py -k test_remove_port_chnl_members

- To print console messages from code 
  
        pytest orca_nw_lib/test/test_interface.py -k test_remove_port_chnl_members -s

## Releases of orca_nw_lib
orca_nw_lib releases are hosted at PyPI- https://pypi.org/project/orca_nw_lib/#history ,
To create a new release, increase the release number in pyproject.toml. 

## Supported SONiC versions
- Broadcom Enterprise SONiC (Latest tested on 4.0.5)

## Contribute
You can contribute to the project by opening an issue or sending a pull request.