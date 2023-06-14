import sys

sys.path.append('../orca_nw_lib')
from orca_nw_lib.utils import load_config,load_logging_config
load_config()
load_logging_config()
from orca_nw_lib.interfaces import Speed,config_interface, get_interface_speed, get_interface_status
from orca_nw_lib.port_chnl import add_port_chnl, del_port_chnl, get_port_chnl,add_port_chnl_member,get_all_port_chnl_members,remove_port_chnl_member


dut_ip='10.10.131.111'


def test_speed_config():
    speed_to_set=Speed.SPEED_10GB
    config_interface(dut_ip,'Ethernet0',speed=speed_to_set)
    assert get_interface_speed(dut_ip,'Ethernet0').get('openconfig-if-ethernet:port-speed') == str(speed_to_set)


def test_interface_enable():
    config_interface(dut_ip,'Ethernet0',enable=True)
    assert get_interface_status(dut_ip,'Ethernet0').get('openconfig-interfaces:enabled') == True
    
def test_add_port_chnl():
    chnl_name='PortChannel101'
    add_port_chnl(dut_ip,chnl_name)
    assert get_port_chnl(dut_ip,chnl_name).get('sonic-portchannel:PORTCHANNEL_LIST')[0].get('name') == chnl_name
    del_port_chnl(dut_ip,chnl_name)
    
def test_add_port_chnl_members():
    chnl_name='PortChannel101'
    add_port_chnl(dut_ip,chnl_name,"up")
    assert get_port_chnl(dut_ip,chnl_name).get('sonic-portchannel:PORTCHANNEL_LIST')[0].get('name') == chnl_name
    
    mem_infcs = ['Ethernet4','Ethernet8']
    add_port_chnl_member(dut_ip, chnl_name, mem_infcs)
    output=get_all_port_chnl_members(dut_ip)
    output_mem_infcs=[]
    for item in output.get("sonic-portchannel:PORTCHANNEL_MEMBER_LIST"):
        if item.get('name') == chnl_name:
            output_mem_infcs.append(item.get('ifname'))
    
    assert mem_infcs==output_mem_infcs
    del_port_chnl(dut_ip,chnl_name)
    
    
def test_remove_port_chnl_members():
    chnl_name='PortChannel101'
    add_port_chnl(dut_ip,chnl_name,"up")
    assert get_port_chnl(dut_ip,chnl_name).get('sonic-portchannel:PORTCHANNEL_LIST')[0].get('name') == chnl_name
    
    mem_infcs = ['Ethernet4','Ethernet8']
    add_port_chnl_member(dut_ip, chnl_name, mem_infcs)
    output=get_all_port_chnl_members(dut_ip)
    output_mem_infcs=[]
    for item in output.get("sonic-portchannel:PORTCHANNEL_MEMBER_LIST"):
        if item.get('name') == chnl_name:
            output_mem_infcs.append(item.get('ifname'))
    
    assert mem_infcs==output_mem_infcs
    
    remove_port_chnl_member(dut_ip,chnl_name,'Ethernet4')
    
    output=get_all_port_chnl_members(dut_ip)
    output_mem_infcs=[]
    for item in output.get("sonic-portchannel:PORTCHANNEL_MEMBER_LIST"):
        if item.get('name') == chnl_name:
            output_mem_infcs.append(item.get('ifname'))
    
    assert 'Ethernet4' not in output_mem_infcs
    
    del_port_chnl(dut_ip,chnl_name)