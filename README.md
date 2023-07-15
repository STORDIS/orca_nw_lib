# orca

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

## Build and Install orca_nw_lib 

    cd orca_nw_lib
    poetry build
    pip install dist/orca_nw_lib-****.whl

>**Note** - Poetry , python and pip must be pre installed.

## To use the ORCA APIs
- Before using APIs of orca_nw_lib, neo4j database and logging configurations should be done by calling the functions load_config and load_logging_config in [./orca_nw_lib/utils.py](./orca_nw_lib/utils.py), As an example for loading default configs refer function load_default_orca_config.
- In the device components specific python modules i.e. device.py or interfaces.py there are APIs to get information directly from the device or from Neo4j datatbase.
- APIs which get information directly from device might take longer than the API which retrirved data from the Neo4j datatbase.
- To use APIs which get data from Neo4j datatbase ends with ******FromDB() i.e. getInterfacesDetailsFromDB(device_ip), those APIs will return data only when the network discovery is initiated using the APIs in [./orca_nw_lib/discovery.py](./orca_nw_lib/discovery.py), refer [./orca_nw_lib/test/test_discovery.py](./orca_nw_lib/test/test_discovery.py).

## Execute Tests
Test cases are located under [./orca_nw_lib/test](./orca_nw_lib/test) directory.
- To execute tests
  
        pytest orca_nw_lib/test/test_network.py

- To execute single test cases 
  
        pytest orca_nw_lib/test/test_network.py -k test_remove_port_chnl_members

- To print console messages from code 
  
        pytest orca_nw_lib/test/test_interface.py -k test_remove_port_chnl_members -s