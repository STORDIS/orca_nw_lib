from orca_nw_lib.common import VlanTagMode
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
from orca_nw_lib.port_chnl_gnmi import add_port_chnl_member, del_port_chnl_from_device, get_all_port_chnl_members, get_port_chnl_from_device, remove_port_chnl_member

from orca_nw_lib.utils import get_orca_config, ping_ok
from orca_nw_lib.discovery import discover_all

from orca_nw_lib.constants import network
from orca_nw_lib.interfaces import (
    del_all_subinterfaces_of_all_interfaces_from_device,
    del_all_subinterfaces_of_interface_from_device,
    get_subinterface_from_device,
    getAllInterfacesNameOfDeviceFromDB,
)
import unittest
from orca_nw_lib.mclag import (
    config_mclag_domain_on_device,
    config_mclag_gateway_mac_on_device,
    config_mclag_mem_portchnl_on_device,
    del_mclag_from_device,
    del_mclag_gateway_mac_from_device,
    get_mclag_domain_from_device,
    get_mclag_gateway_mac_from_device,
)


from orca_nw_lib.interfaces import (
    set_interface_config_on_device,
    get_interface_config_from_device,
)
from orca_nw_lib.port_chnl_gnmi import (
    add_port_chnl_on_device,
)
from orca_nw_lib.vlan_gnmi import (
    config_vlan_on_device,
)
from orca_nw_lib.vlan_gnmi import del_vlan_from_device, get_vlan_details_from_device


class SampleConfigDiscovery(unittest.TestCase):
    vrf_name = "default"
    dut_ip_1 = None
    dut_ip_2 = None
    dut_ip_3 = None
    asn0 = 65000
    asn1 = 65001
    asn2 = 65002
    bgp_ip_0 = "1.1.1.0"
    bgp_ip_1 = "1.1.1.1"
    bgp_ip_2 = "1.1.1.2"
    bgp_ip_3 = "1.1.1.3"
    afi_safi = "ipv4_unicast"
    port_chnl_103 = "PortChannel103"
    peer_link_chnl_100 = "PortChannel100"
    mem_port_chnl_101 = "PortChannel101"
    mem_port_chnl_102 = "PortChannel102"
    domain_id = 1
    mclag_sys_mac = "00:00:00:22:22:22"
    ethernet0 = None
    ethernet1 = None
    ethernet2 = None
    ethernet3 = None
    ethernet4 = None
    ethernet5 = None
    ethernet6 = None
    ethernet7 = None
    vlan_name = "Vlan1"
    vlan_name_2 = "Vlan2"
    vlan_id = 1
    vlan_id_2 = 2

    @classmethod
    def setUpClass(cls):
        if not set(
            [ip for ip in get_orca_config().get(network) if ping_ok(ip)]
        ).issubset(set(getAllDevicesIPFromDB())):
            discover_all()
        assert set(
            [ip for ip in get_orca_config().get(network) if ping_ok(ip)]
        ).issubset(set(getAllDevicesIPFromDB()))
        assert (
            len(set(getAllDevicesIPFromDB())) >= 3
        ), "Need atleast 3 devices, 1-spine and 2-leaves to run tests."
        all_device_list = getAllDevicesIPFromDB()
        cls.dut_ip_1 = all_device_list[0]
        cls.dut_ip_2 = all_device_list[1]
        cls.dut_ip_3 = all_device_list[2]

        all_interface = [
            ether
            for ether in getAllInterfacesNameOfDeviceFromDB(cls.dut_ip_1)
            if "Ethernet" in ether
        ]
        cls.ethernet0 = all_interface[0]
        cls.ethernet1 = all_interface[1]
        cls.ethernet2 = all_interface[2]
        cls.ethernet3 = all_interface[3]
        cls.ethernet4 = all_interface[4]
        cls.ethernet5 = all_interface[5]
        cls.ethernet6 = all_interface[6]
        cls.ethernet7 = all_interface[7]

        assert cls.dut_ip_1 is not None

    @classmethod
    def tearDownClass(cls):
        ## Once all config test cases are done discovefr all again,
        ## Because, currently not all the nodes in DB are updated in real time.
        discover_all()
        #TODO: assert more on the nodes and relations discovered.
        assert (
            len(set(getAllDevicesIPFromDB())) >= 3
        ), "Need atleast 3 devices, 1-spine and 2-leaves to run tests."

    def test_create_port_channel_config(self):
        del_port_chnl_from_device(self.dut_ip_1, self.port_chnl_103)
        del_port_chnl_from_device(self.dut_ip_2, self.port_chnl_103)
        del_port_chnl_from_device(self.dut_ip_3, self.port_chnl_103)

        add_port_chnl_on_device(self.dut_ip_1, self.port_chnl_103, "up")
        assert (
            get_port_chnl_from_device(self.dut_ip_1, self.port_chnl_103)
            .get("sonic-portchannel:PORTCHANNEL_LIST")[0]
            .get("name")
            == self.port_chnl_103
        )
        mem_infcs = [self.ethernet2, self.ethernet3]
        add_port_chnl_member(self.dut_ip_1, self.port_chnl_103, mem_infcs)
        output = get_all_port_chnl_members(self.dut_ip_1)
        for item in output.get("sonic-portchannel:PORTCHANNEL_MEMBER_LIST"):
            if item.get("name") == self.port_chnl_103:
                assert item.get("ifname") in mem_infcs

    def test_create_mclag_configuration(self):
        ## On device -1 mclag config
        del_mclag_from_device(self.dut_ip_1)
        del_port_chnl_from_device(self.dut_ip_1, self.peer_link_chnl_100)
        add_port_chnl_on_device(self.dut_ip_1, self.peer_link_chnl_100)
        assert (
            get_port_chnl_from_device(self.dut_ip_1, self.peer_link_chnl_100)
            .get("sonic-portchannel:PORTCHANNEL_LIST")[0]
            .get("name")
            == self.peer_link_chnl_100
        )
        config_mclag_domain_on_device(
            self.dut_ip_1,
            self.domain_id,
            self.dut_ip_1,
            self.dut_ip_2,
            self.peer_link_chnl_100,
            self.mclag_sys_mac,
        )

        resp = get_mclag_domain_from_device(self.dut_ip_1)
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
            == self.peer_link_chnl_100
        )

        ## member configuration

        del_port_chnl_from_device(self.dut_ip_1, self.mem_port_chnl_101)
        del_port_chnl_from_device(self.dut_ip_1, self.mem_port_chnl_102)

        add_port_chnl_on_device(self.dut_ip_1, self.mem_port_chnl_101)
        add_port_chnl_on_device(self.dut_ip_1, self.mem_port_chnl_102)

        config_mclag_mem_portchnl_on_device(
            self.dut_ip_1, self.domain_id, self.mem_port_chnl_101
        )
        config_mclag_mem_portchnl_on_device(
            self.dut_ip_1, self.domain_id, self.mem_port_chnl_102
        )

        ## On device -2 mclag config
        del_mclag_from_device(self.dut_ip_2)
        del_port_chnl_from_device(self.dut_ip_2, self.peer_link_chnl_100)
        add_port_chnl_on_device(self.dut_ip_2, self.peer_link_chnl_100)
        assert (
            get_port_chnl_from_device(self.dut_ip_2, self.peer_link_chnl_100)
            .get("sonic-portchannel:PORTCHANNEL_LIST")[0]
            .get("name")
            == self.peer_link_chnl_100
        )
        config_mclag_domain_on_device(
            self.dut_ip_2,
            self.domain_id,
            self.dut_ip_2,
            self.dut_ip_1,
            self.peer_link_chnl_100,
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
            == self.dut_ip_1
        )
        assert (
            resp.get("openconfig-mclag:mclag-domain")[0].get("config").get("peer-link")
            == self.peer_link_chnl_100
        )

        ## member configuration

        del_port_chnl_from_device(self.dut_ip_2, self.mem_port_chnl_101)
        del_port_chnl_from_device(self.dut_ip_2, self.mem_port_chnl_102)

        add_port_chnl_on_device(self.dut_ip_2, self.mem_port_chnl_101)
        add_port_chnl_on_device(self.dut_ip_2, self.mem_port_chnl_102)

        config_mclag_mem_portchnl_on_device(
            self.dut_ip_2, self.domain_id, self.mem_port_chnl_101
        )
        config_mclag_mem_portchnl_on_device(
            self.dut_ip_2, self.domain_id, self.mem_port_chnl_102
        )
        
        ## Create MCLAG GW mac
        del_mclag_gateway_mac_from_device(self.dut_ip_1)
        assert not get_mclag_gateway_mac_from_device(self.dut_ip_1)
        gw_mac = "aa:bb:aa:bb:aa:bb"
        config_mclag_gateway_mac_on_device(self.dut_ip_1, gw_mac)
        assert (
            get_mclag_gateway_mac_from_device(self.dut_ip_1)
            .get("openconfig-mclag:mclag-gateway-macs")
            .get("mclag-gateway-mac")[0]
            .get("gateway-mac")
            == gw_mac
        )
        
    def test_create_bgp_config(self):
        del_bgp_global_from_device(self.dut_ip_1, self.vrf_name)
        assert not get_bgp_global_of_vrf_from_device(self.dut_ip_1, self.vrf_name)
        pfxLen = 31
        idx = 0
        ##Clear IPs from all interfaces on the device inorder to avoid overlapping IP error
        for ether in getAllInterfacesNameOfDeviceFromDB(self.dut_ip_1):
            ## IP config is not permitted on port channel member port
            if ether != self.ethernet2 and ether != self.ethernet3:
                del_all_subinterfaces_of_interface_from_device(self.dut_ip_1, ether)
        del_all_subinterfaces_of_all_interfaces_from_device(self.dut_ip_2)
        del_all_subinterfaces_of_all_interfaces_from_device(self.dut_ip_3)
        ############################ Setup 2 interfaces on spine #######################
        ##################### Setup first interface

        set_interface_config_on_device(
            self.dut_ip_1,
            self.ethernet0,
            ip=self.bgp_ip_1,
            ip_prefix_len=pfxLen,
            index=idx,
            enable=True,
        )

        sub_if_config = (
            get_subinterface_from_device(self.dut_ip_1, self.ethernet0, idx)
            .get("openconfig-interfaces:subinterface")[0]
            .get("openconfig-if-ip:ipv4", {})
            .get("addresses", {})
            .get("address")[0]
        )
        assert sub_if_config.get("ip") == self.bgp_ip_1
        assert sub_if_config.get("config").get("prefix-length") == pfxLen

        config = get_interface_config_from_device(self.dut_ip_1, self.ethernet0).get(
            "openconfig-interfaces:config"
        )
        assert config.get("enabled") == True

        ##################### Setup second interface
        set_interface_config_on_device(
            self.dut_ip_1,
            self.ethernet1,
            ip=self.bgp_ip_2,
            ip_prefix_len=pfxLen,
            index=idx,
            enable=True,
        )

        sub_if_config = (
            get_subinterface_from_device(self.dut_ip_1, self.ethernet1, idx)
            .get("openconfig-interfaces:subinterface")[0]
            .get("openconfig-if-ip:ipv4", {})
            .get("addresses", {})
            .get("address")[0]
        )
        assert sub_if_config.get("ip") == self.bgp_ip_2
        assert sub_if_config.get("config").get("prefix-length") == pfxLen

        config = get_interface_config_from_device(self.dut_ip_1, self.ethernet1).get(
            "openconfig-interfaces:config"
        )
        assert config.get("enabled") == True

        ############################ Setup 1 interfaces on leaf-1 #######################

        set_interface_config_on_device(
            self.dut_ip_2,
            self.ethernet0,
            ip=self.bgp_ip_0,
            ip_prefix_len=pfxLen,
            index=idx,
            enable=True,
        )

        sub_if_config = (
            get_subinterface_from_device(self.dut_ip_2, self.ethernet0, idx)
            .get("openconfig-interfaces:subinterface")[0]
            .get("openconfig-if-ip:ipv4", {})
            .get("addresses", {})
            .get("address")[0]
        )
        assert sub_if_config.get("ip") == self.bgp_ip_0
        assert sub_if_config.get("config").get("prefix-length") == pfxLen

        config = get_interface_config_from_device(self.dut_ip_2, self.ethernet0).get(
            "openconfig-interfaces:config"
        )
        assert config.get("enabled") == True

        ############################ Setup 1 interfaces on leaf-2 #######################

        set_interface_config_on_device(
            self.dut_ip_3,
            self.ethernet0,
            ip=self.bgp_ip_3,
            ip_prefix_len=pfxLen,
            index=idx,
            enable=True,
        )

        sub_if_config = (
            get_subinterface_from_device(self.dut_ip_3, self.ethernet0, idx)
            .get("openconfig-interfaces:subinterface")[0]
            .get("openconfig-if-ip:ipv4", {})
            .get("addresses", {})
            .get("address")[0]
        )
        assert sub_if_config.get("ip") == self.bgp_ip_3
        assert sub_if_config.get("config").get("prefix-length") == pfxLen

        config = get_interface_config_from_device(self.dut_ip_3, self.ethernet0).get(
            "openconfig-interfaces:config"
        )
        assert config.get("enabled") == True

        ################# Configure BGP on spine #################

        del_bgp_global_from_device(self.dut_ip_1, self.vrf_name)
        assert not get_bgp_global_of_vrf_from_device(self.dut_ip_1, self.vrf_name)
        configBgpGlobalOnDevice(
            self.dut_ip_1, self.asn0, self.dut_ip_1, vrf_name=self.vrf_name
        )
        for bgp_global in (
            get_bgp_global_of_vrf_from_device(self.dut_ip_1, self.vrf_name).get(
                "sonic-bgp-global:BGP_GLOBALS_LIST"
            )
            or []
        ):
            assert self.asn0 == bgp_global.get("local_asn")
            assert self.dut_ip_1 == bgp_global.get("router_id")
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
        for dev in [self.dut_ip_2, self.dut_ip_1, self.dut_ip_3]:
            delAllBgpGlobalAFFromDevice(dev)
            assert not getAllBgpAfListFromDevice(dev)

            configBgpGlobalAFOnDevice(dev, self.afi_safi, self.vrf_name)

            for af in (
                getAllBgpAfListFromDevice(dev).get(
                    "sonic-bgp-global:BGP_GLOBALS_AF_LIST"
                )
                or []
            ):
                assert af.get("afi_safi") == self.afi_safi
                assert af.get("vrf_name") == self.vrf_name

        ############################ Setup neighbor on Spine #######################
        delAllBgpNeighborsFromDevice(self.dut_ip_1)
        assert not get_bgp_neighbor_from_device(self.dut_ip_1)

        configBGPNeighborsOnDevice(
            self.dut_ip_1, self.asn1, self.bgp_ip_0, self.vrf_name
        )
        configBGPNeighborsOnDevice(
            self.dut_ip_1, self.asn2, self.bgp_ip_3, self.vrf_name
        )
        for nbr in get_bgp_neighbor_from_device(self.dut_ip_1).get(
            "sonic-bgp-neighbor:BGP_NEIGHBOR_LIST"
        ):
            assert (
                self.asn1 == nbr.get("asn") and self.bgp_ip_0 == nbr.get("neighbor")
            ) or (self.asn2 == nbr.get("asn") and self.bgp_ip_3 == nbr.get("neighbor"))
            assert self.vrf_name == nbr.get("vrf_name")

        delAllNeighborAFFromDevice(self.dut_ip_1)
        assert not getAllNeighborAfListFromDevice(self.dut_ip_1)
        configBGPNeighborAFOnDevice(
            self.dut_ip_1, self.afi_safi, self.bgp_ip_0, self.vrf_name, True
        )
        configBGPNeighborAFOnDevice(
            self.dut_ip_1, self.afi_safi, self.bgp_ip_3, self.vrf_name, True
        )

        for nbr_af in (
            getAllNeighborAfListFromDevice(self.dut_ip_1).get(
                "sonic-bgp-neighbor:BGP_NEIGHBOR_AF_LIST"
            )
            or []
        ):
            assert nbr_af.get("admin_status") == True
            assert nbr_af.get("afi_safi") == self.afi_safi
            assert nbr_af.get("vrf_name") == self.vrf_name

        ############################ Setup neighbor on Leaf-1 #######################
        delAllBgpNeighborsFromDevice(self.dut_ip_2)
        assert not get_bgp_neighbor_from_device(self.dut_ip_2)

        configBGPNeighborsOnDevice(
            self.dut_ip_2, self.asn0, self.bgp_ip_1, self.vrf_name
        )
        for nbr in get_bgp_neighbor_from_device(self.dut_ip_2).get(
            "sonic-bgp-neighbor:BGP_NEIGHBOR_LIST"
        ):
            assert self.asn0 == nbr.get("asn") and self.bgp_ip_1 == nbr.get("neighbor")
            assert self.vrf_name == nbr.get("vrf_name")

        delAllNeighborAFFromDevice(self.dut_ip_2)
        assert not getAllNeighborAfListFromDevice(self.dut_ip_2)
        configBGPNeighborAFOnDevice(
            self.dut_ip_2, self.afi_safi, self.bgp_ip_1, self.vrf_name, True
        )

        for nbr_af in (
            getAllNeighborAfListFromDevice(self.dut_ip_2).get(
                "sonic-bgp-neighbor:BGP_NEIGHBOR_AF_LIST"
            )
            or []
        ):
            assert nbr_af.get("admin_status") == True
            assert nbr_af.get("afi_safi") == self.afi_safi
            assert nbr_af.get("vrf_name") == self.vrf_name

        ############################ Setup neighbor on Leaf-2 #######################
        delAllBgpNeighborsFromDevice(self.dut_ip_3)
        assert not get_bgp_neighbor_from_device(self.dut_ip_3)

        configBGPNeighborsOnDevice(
            self.dut_ip_3, self.asn0, self.bgp_ip_2, self.vrf_name
        )
        for nbr in get_bgp_neighbor_from_device(self.dut_ip_3).get(
            "sonic-bgp-neighbor:BGP_NEIGHBOR_LIST"
        ):
            assert self.asn0 == nbr.get("asn") and self.bgp_ip_2 == nbr.get("neighbor")
            assert self.vrf_name == nbr.get("vrf_name")

        delAllNeighborAFFromDevice(self.dut_ip_3)
        assert not getAllNeighborAfListFromDevice(self.dut_ip_3)
        configBGPNeighborAFOnDevice(
            self.dut_ip_3, self.afi_safi, self.bgp_ip_2, self.vrf_name, True
        )

        for nbr_af in (
            getAllNeighborAfListFromDevice(self.dut_ip_3).get(
                "sonic-bgp-neighbor:BGP_NEIGHBOR_AF_LIST"
            )
            or []
        ):
            assert nbr_af.get("admin_status") == True
            assert nbr_af.get("afi_safi") == self.afi_safi
            assert nbr_af.get("vrf_name") == self.vrf_name
        # TODO pfx are not being sent and received with above config, neighbours are connected though.

    def test_create_vlan_config(self):
        del_vlan_from_device(self.dut_ip_1)
        assert not get_vlan_details_from_device(self.dut_ip_1, self.vlan_name)
        mem = {self.ethernet4: VlanTagMode.tagged, self.ethernet5: VlanTagMode.untagged}
        mem_2 = {
            self.ethernet6: VlanTagMode.tagged,
            self.ethernet7: VlanTagMode.untagged,
        }

        config_vlan_on_device(self.dut_ip_1, self.vlan_name, self.vlan_id, mem)
        config_vlan_on_device(self.dut_ip_1, self.vlan_name_2, self.vlan_id_2, mem_2)

        vlan_detail = get_vlan_details_from_device(self.dut_ip_1)
        assert len(vlan_detail.get("sonic-vlan:VLAN_LIST")) == 2
        for v in vlan_detail.get("sonic-vlan:VLAN_LIST") or []:
            assert v.get("members") == list(mem.keys()) or v.get("members") == list(
                mem_2.keys()
            )
            assert v.get("name") == self.vlan_name or v.get("name") == self.vlan_name_2
            assert v.get("vlanid") == self.vlan_id or v.get("vlanid") == self.vlan_id_2

        for v in vlan_detail.get("sonic-vlan:VLAN_MEMBER_LIST") or []:
            if v.get("ifname") in [self.ethernet4, self.ethernet6]:
                assert v.get("tagging_mode") == str(VlanTagMode.tagged)
            elif v.get("ifname") in [self.ethernet5, self.ethernet7]:
                assert v.get("tagging_mode") == str(VlanTagMode.untagged)
            assert v.get("name") in [self.vlan_name, self.vlan_name_2]
            
