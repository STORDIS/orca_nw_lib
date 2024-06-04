
<p align="center">
<a href="https://pypi.org/project/orca_nw_lib/">
      <img alt="PyPI - Downloads" src="https://img.shields.io/pypi/dm/orca-nw-lib">
    </a>
<a href="https://github.com/stordis/orca_nw_lib/issues">
      <img alt="Issues" src="https://img.shields.io/github/issues/stordis/orca_nw_lib?color=0088ff" />
</a>
<a href="https://github.com/stordis/orca_nw_lib/graphs/contributors">
      <img alt="GitHub Contributors" src="https://img.shields.io/github/contributors/stordis/orca_nw_lib" />
</a>
<a href="https://github.com/stordis/orca_nw_lib/pulls?q=">
      <img alt="GitHub pull requests" src="https://img.shields.io/github/issues-pr/stordis/orca_nw_lib?color=0088ff" />
</a>
</p>

# ORCA Network Library
ORCA Network Library is an open source python package to facilitate CRUD operations on SONiC devices using gNMI interface. orca_nw_lib maintains a graph database with the realtime device configurations and network topology.
ORCA Network Library can be used to develop the orchestration solutions, NMS applications,  newtwork data analytics.  
- [ORCA Network Library](#orca-network-library)
  - [Install orca\_nw\_lib using pip](#install-orca_nw_lib-using-pip)
  - [Prerequisite](#prerequisite)
    - [Install Neo4j](#install-neo4j)
    - [orca\_nw\_lib configuration](#orca_nw_lib-configuration)
  - [Build and Install orca\_nw\_lib from source](#build-and-install-orca_nw_lib-from-source)
  - [Using the ORCA Network APIs](#using-the-orca-network-apis)
  - [Knowing API call status](#knowing-api-call-status)
  - [Keeping graph DB in sync with realtime Network state.](#keeping-graph-db-in-sync-with-realtime-network-state)
  - [Executing Tests](#executing-tests)
  - [Releases of orca\_nw\_lib](#releases-of-orca_nw_lib)
  - [Supported SONiC versions](#supported-sonic-versions)
  - [Contribute](#contribute)

## Install orca_nw_lib using pip
Latest release of ORCA Network Library can be simply installed using pip as follows :
        
    pip install orca_nw_lib

## Prerequisite
After installing the orca_nw_lib package, orca_nw_lib can be used like any other python package in your application. But before using orca_nw_lib, it is required to install Neo4j and do some basic configurations.
### Install Neo4j
orca_nw_lib uses neo4j to store the network topology. To install neo4j easiest is to run Neo4j Docker image in container with the following command :
        
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


### orca_nw_lib configuration
In the application where orca_nw_lib is used, `load_orca_config` function in [utils.py](orca_nw_lib/utils.py) must be called before using any APIs of orca_nw_lib. This function loads device and neo4j access information also the logging configuration by default from 
[orca_nw_lib.yml](orca_nw_lib/orca_nw_lib.yml) and [orca_nw_lib_logging.yml](orca_nw_lib/orca_nw_lib_logging.yml) files.
Although user can call load_orca_config with custom config files.
The parameter information is documented in orca.yml file and logging.yml is standard python logging configuration file.

## Build and Install orca_nw_lib from source
Optionally if user want to build and install orca_nw_lib from source, ORCA Network Library uses poetry to build the orca_nw_lib package. As a pre-requisite poetry must be installed in this case. Poetry can be easily installed using the following command :
        
    pip install poetry

To build orca_nw_lib use the following commands :

    git clone https://github.com/STORDIS/orca_nw_lib.git
    cd orca_nw_lib
    poetry build
    pip install dist/orca_nw_lib-****.whl

Once installed the orca_nw_lib package, orca_nw_lib can be used like any other python package in your application.



## Using the ORCA Network APIs
For normal usage following APIs in python modules in the package [orca_nw_lib](orca_nw_lib) are useful -\
[utils.py](orca_nw_lib/utils.py) - load_orca_config() function must be called before using any APIs of orca_nw_lib.\
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
Exception objects raised by APIs in the modules above can be caught to know the API status. Exception object has all necessary details about the error.

## Keeping graph DB in sync with realtime Network state.
Any configuration done on the device via orca_nw_lib APIs automatically keeps the DB in sync with the realtime network state by triggering the discovery method for the network component although gNMI subscriptions would have been the best way to achieve this, but due lack of support for gNMI subscription for all openconfig models in SONiC currently only pull mechanism can be used to keep graph DB in sync with realtime network state. 
> NOTE : For changes done on the device out side of orca_nw_lib i.e. changes done directly on the device, Best way to keep graph DB in sync with realtime network state is to trigger full discovery at a pre-defined interval.

## Executing Tests
Tests are not only used for regular software testing but are a good example to know the usage of APIs in orca_nw_lib. When starting to use orca_nw_lib referring to tests can be a good starting point. Test cases are located under [test](./orca_nw_lib/test) directory. To execute tests a topology of 3 switches (1-spine, 2-leaves) is required. Prior to execute tests, leaves should be connected to spine and respective interfaces should be enabled, so that by providing one of the switch IP in [orca.yml](./orca_nw_lib/orca.yml) whole topology gets discovered.\
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
- Broadcom Enterprise SONiC (Latest tested on >=4.0.5)

## Contribute
You can contribute to the project by opening an issue or sending a pull request.