from orca_backend.gnmi_util import discover_topology
from orca_backend.port_chnl import add_port_chnl_member, remove_port_chnl_member, get_port_chnl,add_port_chnl,del_port_chnl,del_all_port_chnl
from orca_backend.interfaces import enable_interface, get_all_interfaces
#discover_topology()
##MCLAG Configurations
from test_common import device_ip,load_orca_config

load_orca_config()
eth_1="Ethernet1"
eth_2="Ethernet2"
eth_3="Ethernet3"
port_chnl_100="PortChannel100"

print(get_all_interfaces(device_ip))

del_all_port_chnl(device_ip)
add_port_chnl(device_ip,port_chnl_100)
add_port_chnl_member(device_ip,port_chnl_100,eth_2)
add_port_chnl_member(device_ip,port_chnl_100,eth_3)
enable_interface(device_ip,eth_2,True)
enable_interface(device_ip,eth_3,True)
print(get_port_chnl(device_ip))