import sys
sys.path.append('../orca_nw_lib')
from orca_nw_lib.utils import load_default_orca_config
load_default_orca_config()
from orca_nw_lib.port_chnl import add_port_chnl_member, get_port_chnl,add_port_chnl,del_all_port_chnl
from orca_nw_lib.interfaces import createInterfaceGraphObjects, enable_interface, get_all_interfaces, getInterfacesDetailsFromGraph
dut_ip='1010.130.10'
eth_1="Ethernet1"
eth_2="Ethernet2"
eth_3="Ethernet3"
port_chnl_100="PortChannel100"



print(getInterfacesDetailsFromGraph(dut_ip))
createInterfaceGraphObjects(dut_ip)
print(get_all_interfaces(dut_ip))

del_all_port_chnl(dut_ip)
add_port_chnl(dut_ip,port_chnl_100)
add_port_chnl_member(dut_ip,port_chnl_100,eth_2)
add_port_chnl_member(dut_ip,port_chnl_100,eth_3)
enable_interface(dut_ip,eth_2,True)
enable_interface(dut_ip,eth_3,True)
print(get_port_chnl(dut_ip))