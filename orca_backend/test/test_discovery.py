import sys

sys.path.append('../orca_backend')
from orca_backend.graph_db_utils import clean_db
from orca_backend.discovery import discover_interfaces, discover_topology, discover_port_chnl
clean_db()
discover_topology()
discover_interfaces()
discover_port_chnl()