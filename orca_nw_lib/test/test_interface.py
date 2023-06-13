import sys
sys.path.append('../orca_nw_lib')
from orca_nw_lib.utils import load_config,load_logging_config
load_config()
load_logging_config()
from orca_nw_lib.port_chnl import add_port_chnl_member, get_port_chnl,add_port_chnl,del_all_port_chnl
from orca_nw_lib.interfaces import Speed,createInterfaceGraphObjects, config_interface, get_all_interfaces, get_interface, get_interface_speed, get_interface_status, getInterfacesDetailsFromGraph
dut_ip='10.10.131.111'


def test_speed_config():
    speed_to_set=Speed.SPEED_10GB
    config_interface(dut_ip,'Ethernet0',speed=speed_to_set)
    assert get_interface_speed(dut_ip,'Ethernet0').get('openconfig-if-ethernet:port-speed') == str(speed_to_set)


def test_interface_enable():
    config_interface(dut_ip,'Ethernet0',enable=True)
    assert get_interface_status(dut_ip,'Ethernet0').get('openconfig-interfaces:enabled') == True
    