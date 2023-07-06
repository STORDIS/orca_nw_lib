from orca_nw_lib.bgp import (
    configBGPNeighborAFOnDevice,
    configBGPNeighborsOnDevice,
    configBgpGlobalAFOnDevice,
    configBgpGlobalOnDevice,
    del_bgp_global_from_device,
    delAllBgpGlobalAFFromDevice,
    delAllBgpNeighborsFromDevice,
    delAllNeighborAFFromDevice,
    get_bgp_global_of_vrf_from_device,
    get_bgp_neighbor_from_device,
    getAllBgpAfListFromDevice,
    getAllNeighborAfListFromDevice,
)
from orca_nw_lib.device import getAllDevicesIPFromDB

from orca_nw_lib.utils import get_orca_config, ping_ok
from orca_nw_lib.discovery import discover_all

from orca_nw_lib.constants import network
from orca_nw_lib.interfaces import (
    del_all_subinterface_from_device,
    get_subinterface_from_device,
)
import unittest
from orca_nw_lib.mclag import (
    config_mclag_domain_on_device,
    config_mclag_mem_portchnl_on_device,
    del_mclag_from_device,
    get_mclag_domain_from_device,
)


from orca_nw_lib.interfaces import (
    set_interface_config_on_device,
    get_interface_config_from_device,
)
from orca_nw_lib.port_chnl import (
    add_port_chnl_member,
    add_port_chnl_on_device,
    del_port_chnl_from_device,
    get_all_port_chnl_members,
    get_port_chnl_from_device,
)


class SampleConfig(unittest.TestCase):
    vrf_name = "default"
    dut_ip = ""
    dut_ip_2= ""
    dut_ip_3=""
    asn0 = 65000
    asn1 = 65001
    asn2 = 65002
    bgp_ip_0 = "1.1.1.0"
    bgp_ip_1 = "1.1.1.1"
    bgp_ip_2 = "1.1.1.2"
    bgp_ip_3 = "1.1.1.3"
    afi_safi='ipv4_unicast'
    chnl_name = "PortChannel103"
    peer_link = "PortChannel100"
    mem_port_chnl = "PortChannel101"
    mem_port_chnl_2 = "PortChannel102"
    domain_id = 1
    mclag_sys_mac = "00:00:00:22:22:22"
    ethernet0='Ethernet0'
    ethernet1='Ethernet1'
    
    

    @classmethod
    def setUpClass(cls):
        if not set(
            [ip for ip in get_orca_config().get(network) if ping_ok(ip)]
        ).issubset(set(getAllDevicesIPFromDB())):
            discover_all()
        assert set(
            [ip for ip in get_orca_config().get(network) if ping_ok(ip)]
        ).issubset(set(getAllDevicesIPFromDB()))
        cls.dut_ip = getAllDevicesIPFromDB()[0]
        cls.dut_ip_2 = getAllDevicesIPFromDB()[1]
        cls.dut_ip_3 = getAllDevicesIPFromDB()[2]
        assert cls.dut_ip is not None
    
    @classmethod
    def tearDownClass(cls):
        ## Once all config test cases are done discovefr all again,
        ## Because, currently not all the nodes in DB are updated in real time.
        discover_all()

    def test_port_channel_config(self):
        add_port_chnl_on_device(self.dut_ip, self.chnl_name, "up")
        assert (
            get_port_chnl_from_device(self.dut_ip, self.chnl_name)
            .get("sonic-portchannel:PORTCHANNEL_LIST")[0]
            .get("name")
            == self.chnl_name
        )

        mem_infcs = [self.ethernet0, self.ethernet1]
        add_port_chnl_member(self.dut_ip, self.chnl_name, mem_infcs)
        output = get_all_port_chnl_members(self.dut_ip)
        output_mem_infcs = []
        for item in output.get("sonic-portchannel:PORTCHANNEL_MEMBER_LIST"):
            if item.get("name") == self.chnl_name:
                output_mem_infcs.append(item.get("ifname"))
        
    def test_mclag_configuration(self):
        ## On device -1 mclag config 
        del_port_chnl_from_device(self.dut_ip, self.peer_link)
        add_port_chnl_on_device(self.dut_ip, self.peer_link)
        assert (
            get_port_chnl_from_device(self.dut_ip, self.peer_link)
            .get("sonic-portchannel:PORTCHANNEL_LIST")[0]
            .get("name")
            == self.peer_link
        )
        del_mclag_from_device(self.dut_ip)
        config_mclag_domain_on_device(
            self.dut_ip,
            self.domain_id,
            self.dut_ip,
            self.dut_ip_2,
            self.peer_link,
            self.mclag_sys_mac,
        )
        
        resp = get_mclag_domain_from_device(self.dut_ip)
        assert (
            resp.get("openconfig-mclag:mclag-domain")[0].get("config").get("domain-id")
            == self.domain_id
        )
        assert (
            resp.get("openconfig-mclag:mclag-domain")[0]
            .get("config")
            .get("mclag-system-mac")
            == self.mclag_sys_mac
        )
        assert (
            resp.get("openconfig-mclag:mclag-domain")[0]
            .get("config")
            .get("peer-address")
            == self.dut_ip_2
        )
        assert (
            resp.get("openconfig-mclag:mclag-domain")[0].get("config").get("peer-link")
            == self.peer_link
        )
        
        ## member configuration
        
        del_port_chnl_from_device(self.dut_ip, self.mem_port_chnl)
        del_port_chnl_from_device(self.dut_ip, self.mem_port_chnl_2)

        add_port_chnl_on_device(self.dut_ip, self.mem_port_chnl)
        add_port_chnl_on_device(self.dut_ip, self.mem_port_chnl_2)
        
        config_mclag_mem_portchnl_on_device(
            self.dut_ip, self.domain_id, self.mem_port_chnl
        )
        config_mclag_mem_portchnl_on_device(
            self.dut_ip, self.domain_id, self.mem_port_chnl_2
        )
        
        ## On device -2 mclag config 
        del_port_chnl_from_device(self.dut_ip_2, self.peer_link)
        add_port_chnl_on_device(self.dut_ip_2, self.peer_link)
        assert (
            get_port_chnl_from_device(self.dut_ip_2, self.peer_link)
            .get("sonic-portchannel:PORTCHANNEL_LIST")[0]
            .get("name")
            == self.peer_link
        )
        del_mclag_from_device(self.dut_ip_2)
        config_mclag_domain_on_device(
            self.dut_ip_2,
            self.domain_id,
            self.dut_ip_2,
            self.dut_ip,
            self.peer_link,
            self.mclag_sys_mac,
        )
        
        resp = get_mclag_domain_from_device(self.dut_ip_2)
        assert (
            resp.get("openconfig-mclag:mclag-domain")[0].get("config").get("domain-id")
            == self.domain_id
        )
        assert (
            resp.get("openconfig-mclag:mclag-domain")[0]
            .get("config")
            .get("mclag-system-mac")
            == self.mclag_sys_mac
        )
        assert (
            resp.get("openconfig-mclag:mclag-domain")[0]
            .get("config")
            .get("peer-address")
            == self.dut_ip
        )
        assert (
            resp.get("openconfig-mclag:mclag-domain")[0].get("config").get("peer-link")
            == self.peer_link
        )
        
        ## member configuration
        
        del_port_chnl_from_device(self.dut_ip_2, self.mem_port_chnl)
        del_port_chnl_from_device(self.dut_ip_2, self.mem_port_chnl_2)

        add_port_chnl_on_device(self.dut_ip_2, self.mem_port_chnl)
        add_port_chnl_on_device(self.dut_ip_2, self.mem_port_chnl_2)
        
        config_mclag_mem_portchnl_on_device(
            self.dut_ip_2, self.domain_id, self.mem_port_chnl
        )
        config_mclag_mem_portchnl_on_device(
            self.dut_ip_2, self.domain_id, self.mem_port_chnl_2
        )
        
        
    def test_bgp_config(self):
        del_bgp_global_from_device(self.dut_ip, self.vrf_name)
        assert not get_bgp_global_of_vrf_from_device(self.dut_ip, self.vrf_name)
        pfxLen=31
        idx=0
        ethernet0='Ethernet0'
        ethernet1='Ethernet1'
        ##Clear IPs from all interfaces on the device inorder to avoid overlapping IP error 
        del_all_subinterface_from_device(self.dut_ip, ethernet0)
        del_all_subinterface_from_device(self.dut_ip, ethernet1)
        del_all_subinterface_from_device(self.dut_ip_2, ethernet0)
        del_all_subinterface_from_device(self.dut_ip_3, ethernet0)
        ############################ Setup 2 interfaces on spine #######################
        ##################### Setup first interface
        
        set_interface_config_on_device(
                self.dut_ip,
                ethernet0,
                ip='1.1.1.1',
                ip_prefix_len=pfxLen,
                index=idx,
                enable=True
            )
        
        sub_if_config = (
                get_subinterface_from_device(self.dut_ip,ethernet0, idx)
                .get("openconfig-interfaces:subinterface")[0]
                .get("openconfig-if-ip:ipv4")
                .get("addresses")
                .get("address")[0]
            )
        assert sub_if_config.get("ip") == '1.1.1.1'
        assert sub_if_config.get("config").get("prefix-length") == pfxLen
        
        config = get_interface_config_from_device(self.dut_ip, ethernet0).get(
            "openconfig-interfaces:config"
        )
        assert config.get("enabled") == True
        
        ##################### Setup second interface
        set_interface_config_on_device(
                self.dut_ip,
                ethernet1,
                ip='1.1.1.2',
                ip_prefix_len=pfxLen,
                index=idx,
                enable=True
            )
        
        sub_if_config = (
                get_subinterface_from_device(self.dut_ip,ethernet1, idx)
                .get("openconfig-interfaces:subinterface")[0]
                .get("openconfig-if-ip:ipv4")
                .get("addresses")
                .get("address")[0]
            )
        assert sub_if_config.get("ip") == '1.1.1.2'
        assert sub_if_config.get("config").get("prefix-length") == pfxLen
        
        config = get_interface_config_from_device(self.dut_ip, ethernet1).get(
            "openconfig-interfaces:config"
        )
        assert config.get("enabled") == True
        
        ############################ Setup 1 interfaces on leaf-1 #######################
        
        set_interface_config_on_device(
                self.dut_ip_2,
                ethernet0,
                ip='1.1.1.0',
                ip_prefix_len=pfxLen,
                index=idx,
                enable=True
            )
        
        sub_if_config = (
                get_subinterface_from_device(self.dut_ip_2,ethernet0, idx)
                .get("openconfig-interfaces:subinterface")[0]
                .get("openconfig-if-ip:ipv4")
                .get("addresses")
                .get("address")[0]
            )
        assert sub_if_config.get("ip") == '1.1.1.0'
        assert sub_if_config.get("config").get("prefix-length") == pfxLen
        
        config = get_interface_config_from_device(self.dut_ip_2, ethernet0).get(
            "openconfig-interfaces:config"
        )
        assert config.get("enabled") == True
        
        ############################ Setup 1 interfaces on leaf-2 #######################
        
        set_interface_config_on_device(
                self.dut_ip_3,
                ethernet0,
                ip='1.1.1.3',
                ip_prefix_len=pfxLen,
                index=idx,
                enable=True
            )
        
        sub_if_config = (
                get_subinterface_from_device(self.dut_ip_3,ethernet0, idx)
                .get("openconfig-interfaces:subinterface")[0]
                .get("openconfig-if-ip:ipv4")
                .get("addresses")
                .get("address")[0]
            )
        assert sub_if_config.get("ip") == '1.1.1.3'
        assert sub_if_config.get("config").get("prefix-length") == pfxLen
        
        config = get_interface_config_from_device(self.dut_ip_3, ethernet0).get(
            "openconfig-interfaces:config"
        )
        assert config.get("enabled") == True
        
        
        
        
        ################# Configure BGP on spine #################
        
        del_bgp_global_from_device(self.dut_ip, self.vrf_name)
        assert not get_bgp_global_of_vrf_from_device(self.dut_ip, self.vrf_name)
        configBgpGlobalOnDevice(
            self.dut_ip, self.asn0, self.dut_ip, vrf_name=self.vrf_name
        )
        for bgp_global in (
            get_bgp_global_of_vrf_from_device(self.dut_ip, self.vrf_name).get(
                "sonic-bgp-global:BGP_GLOBALS_LIST"
            )
            or []
        ):
            assert self.asn0 == bgp_global.get("local_asn")
            assert self.dut_ip == bgp_global.get("router_id")
            assert self.vrf_name == bgp_global.get("vrf_name")

        ################# Configure BGP & neighbor on leaf-1 #################
        
        del_bgp_global_from_device(self.dut_ip_2, self.vrf_name)
        assert not get_bgp_global_of_vrf_from_device(self.dut_ip_2, self.vrf_name)
        configBgpGlobalOnDevice(
            self.dut_ip_2, self.asn1, self.dut_ip_2, vrf_name=self.vrf_name
        )
        
        for bgp_global in (
            get_bgp_global_of_vrf_from_device(self.dut_ip_2, self.vrf_name).get(
                "sonic-bgp-global:BGP_GLOBALS_LIST"
            )
            or []
        ):
            assert self.asn1 == bgp_global.get("local_asn")
            assert self.dut_ip_2 == bgp_global.get("router_id")
            assert self.vrf_name == bgp_global.get("vrf_name")
        
        ################# Configure BGP & neighbor on leaf-2 #################
        
        del_bgp_global_from_device(self.dut_ip_3, self.vrf_name)
        assert not get_bgp_global_of_vrf_from_device(self.dut_ip_3, self.vrf_name)
        configBgpGlobalOnDevice(
            self.dut_ip_3, self.asn2, self.dut_ip_3, vrf_name=self.vrf_name
        )
        
        for bgp_global in (
            get_bgp_global_of_vrf_from_device(self.dut_ip_3, self.vrf_name).get(
                "sonic-bgp-global:BGP_GLOBALS_LIST"
            )
            or []
        ):
            assert self.asn2 == bgp_global.get("local_asn")
            assert self.dut_ip_3 == bgp_global.get("router_id")
            assert self.vrf_name == bgp_global.get("vrf_name")
            
        ############################ Config bgp AF on all nodes
        for dev in [self.dut_ip_2, self.dut_ip,self.dut_ip_3]:
            delAllBgpGlobalAFFromDevice(dev)
            assert not getAllBgpAfListFromDevice(dev)
            
            configBgpGlobalAFOnDevice(dev,self.afi_safi,self.vrf_name)
            
            for af in getAllBgpAfListFromDevice(dev).get("sonic-bgp-global:BGP_GLOBALS_AF_LIST") or []:
                assert af.get('afi_safi') == self.afi_safi
                assert af.get('vrf_name') == self.vrf_name
            
        ############################ Setup neighbor on Spine #######################
        delAllBgpNeighborsFromDevice(self.dut_ip)
        assert not get_bgp_neighbor_from_device(self.dut_ip)
        
        configBGPNeighborsOnDevice(self.dut_ip, self.asn1, self.bgp_ip_0, self.vrf_name)
        configBGPNeighborsOnDevice(self.dut_ip, self.asn2, self.bgp_ip_3, self.vrf_name)
        for nbr in get_bgp_neighbor_from_device(self.dut_ip).get(
            "sonic-bgp-neighbor:BGP_NEIGHBOR_LIST"
        ):
            assert (self.asn1 == nbr.get("asn") and self.bgp_ip_0 == nbr.get("neighbor")) or (self.asn2 == nbr.get("asn") and self.bgp_ip_3 == nbr.get("neighbor"))
            assert self.vrf_name == nbr.get("vrf_name")
        
        delAllNeighborAFFromDevice(self.dut_ip)
        assert not getAllNeighborAfListFromDevice(self.dut_ip)
        configBGPNeighborAFOnDevice(self.dut_ip,self.afi_safi,self.bgp_ip_0,self.vrf_name,True)
        configBGPNeighborAFOnDevice(self.dut_ip,self.afi_safi,self.bgp_ip_3,self.vrf_name,True)
        
        for nbr_af in getAllNeighborAfListFromDevice(self.dut_ip).get("sonic-bgp-neighbor:BGP_NEIGHBOR_AF_LIST") or []:
            assert nbr_af.get('admin_status')==True
            assert nbr_af.get('afi_safi')==self.afi_safi
            assert nbr_af.get('vrf_name')==self.vrf_name
            
        
        ############################ Setup neighbor on Leaf-1 #######################
        delAllBgpNeighborsFromDevice(self.dut_ip_2)
        assert not get_bgp_neighbor_from_device(self.dut_ip_2)
        
        configBGPNeighborsOnDevice(self.dut_ip_2, self.asn0, self.bgp_ip_1, self.vrf_name)
        for nbr in get_bgp_neighbor_from_device(self.dut_ip_2).get(
            "sonic-bgp-neighbor:BGP_NEIGHBOR_LIST"
        ):
            assert self.asn0 == nbr.get("asn") and self.bgp_ip_1 == nbr.get("neighbor")
            assert self.vrf_name == nbr.get("vrf_name")
        
        delAllNeighborAFFromDevice(self.dut_ip_2)
        assert not getAllNeighborAfListFromDevice(self.dut_ip_2)
        configBGPNeighborAFOnDevice(self.dut_ip_2,self.afi_safi,self.bgp_ip_1,self.vrf_name,True)
        
        for nbr_af in getAllNeighborAfListFromDevice(self.dut_ip_2).get("sonic-bgp-neighbor:BGP_NEIGHBOR_AF_LIST") or []:
            assert nbr_af.get('admin_status')==True
            assert nbr_af.get('afi_safi')==self.afi_safi
            assert nbr_af.get('vrf_name')==self.vrf_name
            
        ############################ Setup neighbor on Leaf-2 #######################
        delAllBgpNeighborsFromDevice(self.dut_ip_3)
        assert not get_bgp_neighbor_from_device(self.dut_ip_3)
        
        configBGPNeighborsOnDevice(self.dut_ip_3, self.asn0, self.bgp_ip_2, self.vrf_name)
        for nbr in get_bgp_neighbor_from_device(self.dut_ip_3).get(
            "sonic-bgp-neighbor:BGP_NEIGHBOR_LIST"
        ):
            assert self.asn0 == nbr.get("asn") and self.bgp_ip_2 == nbr.get("neighbor")
            assert self.vrf_name == nbr.get("vrf_name")
            
        delAllNeighborAFFromDevice(self.dut_ip_3)
        assert not getAllNeighborAfListFromDevice(self.dut_ip_3)
        configBGPNeighborAFOnDevice(self.dut_ip_3,self.afi_safi,self.bgp_ip_2,self.vrf_name,True)
        
        for nbr_af in getAllNeighborAfListFromDevice(self.dut_ip_3).get("sonic-bgp-neighbor:BGP_NEIGHBOR_AF_LIST") or []:
            assert nbr_af.get('admin_status')==True
            assert nbr_af.get('afi_safi')==self.afi_safi
            assert nbr_af.get('vrf_name')==self.vrf_name
        # TODO pfx are not being sent and received with above config, neighbours are connected though.
