import sys
sys.path.append('../orca_nw_lib')
from orca_nw_lib.graph_db_utils import clean_db
from orca_nw_lib.discovery import discover_interfaces, discover_mclag, discover_topology, discover_port_chnl
clean_db()
discover_topology()
discover_interfaces()
discover_port_chnl()
discover_mclag()